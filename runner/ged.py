"""Structural correctness metric: source CFG vs decompiled CFG graph edit distance.

Adapted from decbench's `ged` metric (see
`vendor/decbench/decbench/metrics/ged.py` + `utils/cfg.py` in the Fission
monorepo). GED complements `type_match` (variable types vs DWARF) with a
second, independent ground-truth axis: does the decompiler's *control-flow
shape* match the original source's, not just its behavior (semantic_score)
or its Ghidra-relative parity (assembly/pcode/cfg parity)?

Both sides are parsed with the same tool (pyjoern/Joern) for structural
comparability. Source CFGs are extracted from the binary variant's
**preprocessed translation unit**, with authored source retained only as an
explicit legacy fallback. They are not extracted from an isolated function:
fission-benchmark's
fixtures define shared types near the top of the file (e.g.
`typedef struct Node {...} Node;` in advanced_patterns.c) that an isolated
function body wouldn't carry, and Joern needs the file to resolve them.
Decompiled CFGs use isolated per-function text instead -- empirically,
Joern's parser still builds a correct CFG even referencing an undefined
struct type (real decompilers like Ghidra emit `Node *cur` with no
corresponding struct definition at all), since CFG structure comes from
control-flow keywords/blocks, not full type resolution.

First import of `pyjoern` downloads ~1.8GB of Joern (JVM) binaries into
pyjoern's own site-packages directory -- a real, deliberate infrastructure
cost, not a bug. See docs/benchmarking.md (or the pyproject.toml comment)
for why this was still chosen over a lighter pycparser-based alternative.
"""

from __future__ import annotations

import functools
import json
import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Any

try:
    from .metric_cache import load as cache_load, store as cache_store
except ImportError:
    from metric_cache import load as cache_load, store as cache_store

logger = logging.getLogger(__name__)


class _PublishedCfgStatement:
    """Marker preventing a real one-block published CFG from looking empty."""


class _PublishedCfgNode:
    def __init__(self, node_id: int, *, entry: bool, exit_: bool, real: bool) -> None:
        self.id = node_id
        self.is_entrypoint = entry
        self.is_exitpoint = exit_
        self.statements = (_PublishedCfgStatement(),) if real else ()

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _PublishedCfgNode) and self.id == other.id

    def __repr__(self) -> str:
        return f"n{self.id}"


# Exact GED is super-polynomial, so graphs above this node count fall back to
# a cheap structural (size-delta) distance instead of vj_ged.
GED_MAX_NODES = int(os.environ.get("FISSION_BENCHMARK_GED_MAX_NODES") or "60")
GED_CACHE_VERSION = "v2-preprocessed-tu"


# ── Decompiled-C sanitization (pre-parse) ───────────────────────────────────

# ``T [N] name(...)`` is not valid C, so Joern parses nothing for such a
# function and it silently drops out of GED's denominator. Anchored at line
# start so it only rewrites a signature, never an in-body ``char buf[16];``.
_AGG_RETURN = re.compile(r"^([A-Za-z_][\w ]*?)\s*\[\d+\]\s+([A-Za-z_]\w*\s*\()", re.M)

# ``@`` is not legal C and breaks Joern's parse for the whole function.
_REG_ANNOTATION = re.compile(r"\s*@\s*[a-z]\w+\b")

# Tab and newline are the emitted source's own layout, not literal payload.
_KEEP_RAW_BYTES = frozenset({0x09, 0x0A})


def escape_literal_control_bytes(text: str) -> str:
    """Escape raw control bytes appearing inside string/char literals.

    A decompiler that inlines .rodata verbatim emits e.g. an ANSI colour
    sequence as a raw 0x1B. That's valid C, but it makes pyjoern's fast
    parser emit non-JSON, which fails the whole invocation rather than the
    one function. Only literal interiors are rewritten; \\x1b is the same
    bytes to the compiler, so control flow is untouched.
    """
    out: list[str] = []
    in_string = in_char = pending_escape = False
    for char in text:
        code = ord(char)
        if pending_escape:
            out.append(char)
            pending_escape = False
            continue
        if char == "\\" and (in_string or in_char):
            out.append(char)
            pending_escape = True
            continue
        if char == '"' and not in_char:
            in_string = not in_string
        elif char == "'" and not in_string:
            in_char = not in_char
        if (in_string or in_char) and code not in _KEEP_RAW_BYTES and (code < 0x20 or code == 0x7F):
            out.append(f"\\x{code:02x}")
        else:
            out.append(char)
    return "".join(out)


def sanitize_decompiled_c(text: str) -> str:
    """Clean decompiler-specific C quirks that break Joern's parser.

    GED only cares about CFG *structure*, so these edits are purely to make
    the body parseable -- they never touch control flow:

    * **Aggregate/array return type** (angr/ghidra): ``T [N] name(...)`` ->
      ``T name(...)``.
    * **Register annotation** (binja-style): `` @ rax`` stripped.
    * **128-bit types** (ida-style): ``__int128`` widened to ``long long``.
    * **Raw control bytes in literals**: escaped.
    """
    text = _AGG_RETURN.sub(r"\1 \2", text)
    text = _REG_ANNOTATION.sub("", text)
    text = text.replace("unsigned __int128", "unsigned long long").replace("__int128", "long long")
    return escape_literal_control_bytes(text)


def is_degenerate_cfg(cfg: Any) -> bool:
    """True when a CFG has no real structure to compare GED against.

    Two cases, both meaning "nothing to score": zero nodes, or a single
    block whose statements are ALL ``Nop`` -- an empty-prototype CFG Joern
    emits from a declaration-only view. A genuine single-block function (a
    straight-line ``return foo(...);``) has real statements and stays
    scorable (a correct 1-block decompilation -> GED 0).
    """
    n = cfg.number_of_nodes()
    if n == 0:
        return True
    if n >= 2:
        return False
    for node in cfg.nodes():
        for stmt in getattr(node, "statements", None) or []:
            if type(stmt).__name__ != "Nop":
                return False
    return True


# ── Source CFG extraction (whole file, cached per path) ────────────────────


@functools.lru_cache(maxsize=64)
def extract_source_cfgs(source_path: str) -> dict[str, Any]:
    """Parse a whole source translation unit once via pyjoern, cached by path.

    Returns function_name -> CFG DiGraph. Parsing the whole file (not an
    isolated per-function extract) lets same-file typedefs resolve, and the
    result is cached since many (decompiler, function, variant) rows share
    one source file.
    """
    try:
        from pyjoern import parse_source
    except ImportError:
        raise ImportError("pyjoern is required for GED. Install with: pip install pyjoern")

    cfgs: dict[str, Any] = {}
    try:
        parsed = parse_source(Path(source_path))
        if parsed is None:
            return cfgs
        for key, func in parsed.items():
            func_name = func.name if hasattr(func, "name") else str(key)
            cfg = func.cfg if hasattr(func, "cfg") else None
            if cfg is not None:
                cfgs[func_name] = cfg
    except Exception as e:
        logger.warning("CFG extraction from source %s failed: %s", source_path, e)
    return cfgs


@functools.lru_cache(maxsize=1024)
def load_published_source_cfgs(source_cfg_path: str) -> dict[str, Any]:
    """Load DecBench's topology-preserving published source-CFG contract."""
    try:
        import networkx as nx

        payload = json.loads(Path(source_cfg_path).read_text(encoding="utf-8"))
    except (OSError, ValueError, ImportError) as exc:
        logger.warning("Published source CFG %s failed: %s", source_cfg_path, exc)
        return {}

    output: dict[str, Any] = {}
    for name, raw in (payload.get("functions") or {}).items():
        if not isinstance(raw, dict):
            continue
        entries = {int(value) for value in raw.get("entry") or []}
        exits = {int(value) for value in raw.get("exit") or []}
        real = not bool(raw.get("degenerate", True))
        nodes = {
            int(value): _PublishedCfgNode(
                int(value),
                entry=int(value) in entries,
                exit_=int(value) in exits,
                real=real,
            )
            for value in raw.get("nodes") or []
        }
        graph = nx.DiGraph()
        graph.add_nodes_from(nodes.values())
        for edge in raw.get("edges") or []:
            if len(edge) == 2 and int(edge[0]) in nodes and int(edge[1]) in nodes:
                graph.add_edge(nodes[int(edge[0])], nodes[int(edge[1])])
        output[str(name)] = graph
    return output


# ── Decompiled CFG extraction (batched per binary+decompiler) ──────────────


def _parse_decompiled_cfg_batch(functions: dict[str, str], parse_source: Any) -> dict[str, Any]:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".c", delete=False) as f:
        for name, code in functions.items():
            f.write(f"// Function: {name}\n")
            f.write(sanitize_decompiled_c(code))
            f.write("\n\n")
        temp_path = Path(f.name)

    try:
        parsed = parse_source(temp_path)
        cfgs: dict[str, Any] = {}
        if parsed is not None:
            for key, func in parsed.items():
                func_name = func.name if hasattr(func, "name") else str(key)
                cfg = func.cfg if hasattr(func, "cfg") else None
                if cfg is not None:
                    cfgs[func_name] = cfg
        return cfgs
    finally:
        temp_path.unlink(missing_ok=True)


def extract_decompiled_cfgs(functions: dict[str, str]) -> dict[str, Any]:
    """Parse ALL decompiled functions for one (binary, decompiler) batch in a
    single Joern invocation (mirrors decbench's per-binary batching -- one
    parse call instead of one per function).

    Args:
        functions: function_name -> decompiled_code (unsanitized).

    Returns:
        function_name -> CFG DiGraph for whichever functions Joern parsed.
    """
    try:
        from pyjoern import parse_source
    except ImportError:
        raise ImportError("pyjoern is required for GED. Install with: pip install pyjoern")

    cfgs: dict[str, Any] = {}
    if not functions:
        return cfgs

    def parse_with_isolation(items: list[tuple[str, str]]) -> dict[str, Any]:
        batch = dict(items)
        try:
            parsed_cfgs = _parse_decompiled_cfg_batch(batch, parse_source)
            missing = [item for item in items if item[0] not in parsed_cfgs]
            if not missing:
                return parsed_cfgs
            if len(items) == 1:
                logger.warning("CFG extraction omitted decompiled function %s", items[0][0])
                return parsed_cfgs
            if len(missing) == len(items):
                midpoint = len(items) // 2
                logger.warning(
                    "CFG extraction omitted all %d decompiled functions; isolating halves",
                    len(items),
                )
                return {
                    **parse_with_isolation(items[:midpoint]),
                    **parse_with_isolation(items[midpoint:]),
                }
            # Preserve functions Joern accepted and retry only omitted rows.
            recovered = parse_with_isolation(missing)
            return {**parsed_cfgs, **recovered}
        except Exception as exc:
            if len(items) == 1:
                logger.warning(
                    "CFG extraction failed for decompiled function %s: %s",
                    items[0][0],
                    exc,
                )
                return {}
            midpoint = len(items) // 2
            logger.warning(
                "CFG extraction from %d-function batch failed; isolating halves: %s",
                len(items),
                exc,
            )
            return {
                **parse_with_isolation(items[:midpoint]),
                **parse_with_isolation(items[midpoint:]),
            }

    cfgs.update(parse_with_isolation(list(functions.items())))

    return cfgs


# ── GED computation ─────────────────────────────────────────────────────────

_vj_ged = None


def _get_vj_ged():
    global _vj_ged
    if _vj_ged is None:
        try:
            from cfgutils.similarity import vj_ged

            _vj_ged = vj_ged
        except ImportError:
            raise ImportError("cfgutils is required for GED. Install with: pip install cfgutils")
    return _vj_ged


def _graph_content(graph: Any) -> dict[str, Any]:
    """Stable-enough CFG content payload for the versioned metric cache."""
    nodes = list(graph.nodes())
    node_index = {node: index for index, node in enumerate(nodes)}
    return {
        "nodes": [
            {
                "statements": [repr(stmt) for stmt in (getattr(node, "statements", None) or [])],
                "in_degree": int(graph.in_degree(node)),
                "out_degree": int(graph.out_degree(node)),
            }
            for node in nodes
        ],
        "edges": sorted(
            (node_index[left], node_index[right]) for left, right in graph.edges()
        ),
    }


def compute_ged(source_cfg: Any, decompiled_cfg: Any) -> dict[str, Any]:
    """Graph edit distance between a source CFG and a decompiled CFG.

    Returns a dict with `ged` (float, lower is better; 0.0 = perfect
    structural match), node/edge counts, and `approximated` (True when a
    graph exceeded GED_MAX_NODES and a cheap size-delta stood in for exact
    vj_ged -- a sound lower bound, but consumers should not treat a 0 there
    as a real perfect match unless they also check node/edge counts equal).
    Returns `{"error": ...}` (no `ged` key) for a missing/degenerate CFG.
    """
    if source_cfg is None or decompiled_cfg is None:
        return {"error": "missing CFG"}

    s_nodes = source_cfg.number_of_nodes()
    if is_degenerate_cfg(source_cfg):
        return {
            "error": f"degenerate source CFG (source_nodes={s_nodes})",
            "source_nodes": s_nodes,
            "decompiled_nodes": decompiled_cfg.number_of_nodes(),
        }

    d_nodes = decompiled_cfg.number_of_nodes()
    s_edges = source_cfg.number_of_edges()
    d_edges = decompiled_cfg.number_of_edges()
    base = {
        "source_nodes": s_nodes,
        "source_edges": s_edges,
        "decompiled_nodes": d_nodes,
        "decompiled_edges": d_edges,
    }

    cache_key = {
        "max_nodes": GED_MAX_NODES,
        "source": _graph_content(source_cfg),
        "decompiled": _graph_content(decompiled_cfg),
    }
    cached = cache_load("ged", GED_CACHE_VERSION, cache_key)
    if isinstance(cached, dict):
        return {**cached, "cache": {"schema": "metric-content-cache-v1", "hit": True}}

    if s_nodes > GED_MAX_NODES or d_nodes > GED_MAX_NODES:
        approx = float(abs(s_nodes - d_nodes) + abs(s_edges - d_edges))
        result = {**base, "ged": approx, "approximated": True}
        cache_store("ged", GED_CACHE_VERSION, cache_key, result)
        return {**result, "cache": {"schema": "metric-content-cache-v1", "hit": False}}

    vj_ged = _get_vj_ged()
    try:
        ged_value = vj_ged(source_cfg, decompiled_cfg)
        result = {**base, "ged": float(ged_value)}
        cache_store("ged", GED_CACHE_VERSION, cache_key, result)
        return {**result, "cache": {"schema": "metric-content-cache-v1", "hit": False}}
    except Exception as e:
        return {**base, "error": str(e)}
