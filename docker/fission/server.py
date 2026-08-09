"""Fission decompiler and parity diagnostic API server."""
import base64
import hashlib
import json
import os
import subprocess
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="fission-decompiler", version="1.0")
FISSION_BIN = Path("/usr/local/bin/fission_cli")
SLEIGH_SPEC_DIR = os.environ.get("FISSION_SLEIGH_SPEC_DIR", "/sleigh-specs")
RESOURCE_ROOT = os.environ.get("FISSION_RESOURCE_ROOT", "/opt/fission-utils/utils")
GHIDRA_DATA_DIR = os.environ.get("FISSION_GHIDRA_DATA_DIR", "/opt/fission-utils/utils/ghidra-data")
# Core_c_pe hard functions under CI load routinely exceed 30s; 120s is the
# benchmark default (override via FISSION_DECOMP_TIMEOUT_MS).
DECOMP_TIMEOUT_MS = os.environ.get("FISSION_DECOMP_TIMEOUT_MS", "120000")
RELEASE_VERSION_FILE = Path("/opt/fission-release-version")
SOURCE_FILE = Path("/opt/fission-source")
GIT_SHA_FILE = Path("/opt/fission-git-sha")

# ---------------------------------------------------------------------------
# Capability probe — checked once per process lifetime and cached.
# We inspect `fission_cli decomp --help` to discover supported flags so that
# older CLI releases that do not have `--layer` still work correctly.
# ---------------------------------------------------------------------------
_CAPABILITY_CACHE: Dict[str, bool] = {}
_CAPABILITY_PROBED: bool = False
_CAPABILITY_PROBE_ERROR: str | None = None
_CAPABILITY_LOCK = threading.Lock()
_LIST_CAPABILITY_CACHE: Dict[str, bool] = {}
_LIST_CAPABILITY_PROBED: bool = False
_LIST_CAPABILITY_LOCK = threading.Lock()


def _probe_capabilities() -> None:
    """Populate _CAPABILITY_CACHE from `fission_cli decomp --help` output."""
    global _CAPABILITY_PROBED, _CAPABILITY_PROBE_ERROR
    if _CAPABILITY_PROBED:
        return
    with _CAPABILITY_LOCK:
        if _CAPABILITY_PROBED:
            return
        try:
            r = subprocess.run(
                [str(FISSION_BIN), "decomp", "--help"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            help_text = r.stdout + r.stderr
            if r.returncode not in (0, 1):  # --help may exit 1 on some CLIs
                _CAPABILITY_PROBE_ERROR = (
                    f"fission_cli decomp --help exited {r.returncode}: "
                    f"{help_text[:200]}"
                )
                _CAPABILITY_CACHE["--layer"] = False
                _CAPABILITY_CACHE["--benchmark"] = False
                _CAPABILITY_CACHE["--timeout-ms"] = False
            else:
                _CAPABILITY_CACHE["--layer"] = "--layer" in help_text
                _CAPABILITY_CACHE["--benchmark"] = "--benchmark" in help_text
                _CAPABILITY_CACHE["--timeout-ms"] = "--timeout-ms" in help_text
        except Exception as exc:
            # If help fails, assume minimal capability set (no optional flags).
            _CAPABILITY_PROBE_ERROR = str(exc)
            _CAPABILITY_CACHE["--layer"] = False
            _CAPABILITY_CACHE["--benchmark"] = False
            _CAPABILITY_CACHE["--timeout-ms"] = False
        finally:
            _CAPABILITY_PROBED = True


def supports(flag: str) -> bool:
    """Return True if the CLI binary supports the given flag."""
    _probe_capabilities()
    return _CAPABILITY_CACHE.get(flag, False)


def supports_list(flag: str) -> bool:
    """Return whether the installed CLI exposes a complete-list contract flag."""
    global _LIST_CAPABILITY_PROBED
    if _LIST_CAPABILITY_PROBED:
        return _LIST_CAPABILITY_CACHE.get(flag, False)
    with _LIST_CAPABILITY_LOCK:
        if not _LIST_CAPABILITY_PROBED:
            try:
                result = subprocess.run(
                    [str(FISSION_BIN), "list", "--help"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                help_text = result.stdout + result.stderr
                for candidate in (
                    "--function-discovery-profile",
                    "--include-nonuser-functions",
                ):
                    _LIST_CAPABILITY_CACHE[candidate] = candidate in help_text
            except Exception:
                _LIST_CAPABILITY_CACHE["--function-discovery-profile"] = False
                _LIST_CAPABILITY_CACHE["--include-nonuser-functions"] = False
            finally:
                _LIST_CAPABILITY_PROBED = True
    return _LIST_CAPABILITY_CACHE.get(flag, False)


def function_inventory_command(bin_path: str) -> List[str]:
    """Build the strongest function-inventory command supported by this CLI."""
    command = ["list", bin_path]
    if supports_list("--function-discovery-profile"):
        command.extend(["--function-discovery-profile", "conservative"])
    if supports_list("--include-nonuser-functions"):
        command.append("--include-nonuser-functions")
    command.append("--json")
    return command


def program_metadata_command(bin_path: str) -> List[str]:
    """Build the canonical typed program-metadata export command."""
    return ["inventory", "program-metadata", bin_path]

class DecompileRequest(BaseModel):
    binary_b64: str
    addr: str

class DecompileResponse(BaseModel):
    decompiler: str = "fission"
    name: str
    code: str
    # Dual surfaces from Fission CLI (optional; older CLIs omit them).
    code_nir: Optional[str] = None
    code_hir: Optional[str] = None
    layer: Optional[str] = None
    time_ms: int
    error: Optional[str] = None

class BatchDecompileRequest(BaseModel):
    binary_b64: str
    addresses: List[str]

class DecompileResultItem(BaseModel):
    addr: str
    name: str = "?"
    # Primary code stays NIR-faithful for semantic oracle compatibility.
    code: str = ""
    code_nir: Optional[str] = None
    code_hir: Optional[str] = None
    layer: Optional[str] = None
    error: Optional[str] = None

class BatchDecompileResponse(BaseModel):
    decompiler: str = "fission"
    results: List[DecompileResultItem]
    time_ms: int

def _read_text_file(path: Path, default: str = "") -> str:
    try:
        return path.read_text(encoding="utf-8").strip() or default
    except Exception:
        return default


@app.get("/health")
def health():
    """Health probe with provenance for release vs local quality-loop bundles."""
    version = "unknown"
    release_version = os.environ.get("FISSION_RELEASE_VERSION", "unknown")
    source = os.environ.get("FISSION_SOURCE") or _read_text_file(SOURCE_FILE, "release")
    git_sha = os.environ.get("FISSION_GIT_SHA") or _read_text_file(GIT_SHA_FILE, "")
    source_fingerprint = os.environ.get("FISSION_SOURCE_FINGERPRINT", "")
    try:
        r = subprocess.run(
            [str(FISSION_BIN), "--version"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        version = r.stdout.strip() or r.stderr.strip()
    except Exception:
        pass
    release_version = _read_text_file(RELEASE_VERSION_FILE, release_version)
    # Probe capabilities so they are available immediately on first health call.
    _probe_capabilities()
    payload = {
        "status": "ok",
        "decompiler": "fission",
        "version": version,
        "release_version": release_version,
        # "release" = GitHub Release bake (CI contract). "local" = host bundle mount.
        "source": source if source in ("release", "local") else "release",
        # Capabilities discovered from `fission_cli decomp --help`.
        # Consumers can use this to understand which optional flags are available
        # without re-probing the CLI.
        "capabilities": {
            k: v for k, v in _CAPABILITY_CACHE.items()
        },
        # Probe diagnostics — allows contract tests to distinguish between
        # "probe ran but found no flags" vs "probe itself crashed".
        "capability_probe_ok": _CAPABILITY_PROBE_ERROR is None,
        "capability_probe_error": _CAPABILITY_PROBE_ERROR,
        "parity": {
            "multi_bundle": "/parity_multi_bundle",
            "cli_workers": _CLI_WORKERS,
            "mode": "tool_phased_multi_addr",
            "cache_key": "path+content_fingerprint",
        },
    }
    if git_sha:
        payload["git_sha"] = git_sha
    if source_fingerprint:
        payload["source_fingerprint"] = source_fingerprint
    return payload

# Cap concurrent fission_cli children so multi_bundle cannot thrash the host
# (default 8). Each CLI still reloads the PE; multi-addr batching below cuts
# peak concurrency and amortizes orchestration cost.
_CLI_WORKERS = max(1, int(os.environ.get("FISSION_CLI_WORKERS", "8")))
_CLI_SEM = threading.Semaphore(_CLI_WORKERS)


def run_fission_cli(args: List[str]):
    env = {
        **os.environ,
        "FISSION_SLEIGH_SPEC_DIR": SLEIGH_SPEC_DIR,
        "FISSION_RESOURCE_ROOT": RESOURCE_ROOT,
        "FISSION_GHIDRA_DATA_DIR": GHIDRA_DATA_DIR,
    }
    with _CLI_SEM:
        result = subprocess.run(
            [str(FISSION_BIN)] + args,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail=result.stderr or result.stdout)
    return json.loads(result.stdout)

def validate_address(addr: str) -> int:
    if not addr or not addr.strip():
        raise HTTPException(status_code=400, detail="Address cannot be empty")
    try:
        if addr.lower().startswith("0x"):
            return int(addr, 16)
        try:
            return int(addr, 10)
        except ValueError:
            return int(addr, 16)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid address format: {addr}")

def resolve_binary(binary: str) -> str:
    if not binary or not binary.strip():
        raise HTTPException(status_code=400, detail="Binary path cannot be empty")
    resolved = "/" + binary if binary.startswith("corpus/") else binary
    if not os.path.exists(resolved):
        raise HTTPException(status_code=404, detail=f"Binary not found: {resolved}")
    return resolved

def decompile_batch_command(binary_path: str, addresses_path: str) -> List[str]:
    """Build CLI command for batch decompilation.

    Optional flags (``--layer``, ``--benchmark``, ``--timeout-ms``) are added
    only when the capability probe confirms the current CLI version supports
    them.  This prevents hard failures on older release bundles that predate
    these flags.
    """
    cmd = [
        str(FISSION_BIN),
        "decomp",
        binary_path,
        "--addresses-file",
        addresses_path,
        "--json",
    ]
    # --benchmark and --timeout-ms are optional quality-of-life flags.
    if supports("--benchmark"):
        cmd.append("--benchmark")
    if supports("--timeout-ms"):
        cmd += ["--timeout-ms", DECOMP_TIMEOUT_MS]
    # --layer nir: only add when the CLI explicitly supports it.
    # Older releases output NIR by default anyway, so omitting is safe.
    if supports("--layer"):
        cmd += ["--layer", "nir"]
    return cmd

def normalize_decompile_results(payload: object) -> list[dict]:
    if isinstance(payload, dict):
        functions = payload.get("functions", [])
        return functions if isinstance(functions, list) else []
    if isinstance(payload, list):
        return payload
    return []


def decompile_result_from_cli_item(item: dict, fallback_addr: Optional[str] = None) -> DecompileResultItem:
    """Map Fission CLI JSON function row → adapter result (preserves dual layers)."""
    code = item.get("code") or ""
    code_nir = item.get("code_nir")
    code_hir = item.get("code_hir")
    # Older CLIs only have `code`; treat it as NIR when dual fields are absent.
    if not code_nir and code:
        code_nir = code
    if not code_hir and code:
        code_hir = code
    return DecompileResultItem(
        addr=item.get("addr") or item.get("address") or (fallback_addr or ""),
        name=item.get("name", "?"),
        code=code,
        code_nir=code_nir,
        code_hir=code_hir,
        layer=item.get("layer"),
        error=item.get("error"),
    )

_PARITY_CACHE: Dict[tuple, object] = {}
_PARITY_CACHE_MAX = 1024
_FP_CACHE: Dict[str, tuple] = {}  # path -> (size, mtime_ns, fp)


def _binary_fingerprint(bin_path: str) -> str:
    """Content fingerprint so same path after corpus rebuild does not reuse stale cache."""
    try:
        st = os.stat(bin_path)
    except OSError:
        return "missing"
    cached = _FP_CACHE.get(bin_path)
    if cached and cached[0] == st.st_size and cached[1] == st.st_mtime_ns:
        return cached[2]
    h = hashlib.sha256()
    h.update(f"{st.st_size}:{st.st_mtime_ns}".encode("utf-8"))
    try:
        with open(bin_path, "rb") as fh:
            h.update(fh.read(65536))
            if st.st_size > 65536:
                fh.seek(max(0, st.st_size - 65536))
                h.update(fh.read(65536))
    except OSError:
        return f"err-{st.st_size}-{st.st_mtime_ns}"
    fp = h.hexdigest()[:16]
    _FP_CACHE[bin_path] = (st.st_size, st.st_mtime_ns, fp)
    return fp


def _cache_get(key: tuple):
    return _PARITY_CACHE.get(key)


def _cache_put(key: tuple, value: object) -> None:
    if len(_PARITY_CACHE) >= _PARITY_CACHE_MAX:
        try:
            del _PARITY_CACHE[next(iter(_PARITY_CACHE))]
        except StopIteration:
            pass
    _PARITY_CACHE[key] = value


def _normalize_addr_key(addr: str) -> str:
    text = addr.strip().lower()
    try:
        return f"0x{int(text, 16):x}"
    except ValueError:
        return text


@app.get("/functions")
def functions(binary: str):
    bin_path = resolve_binary(binary)
    fp = _binary_fingerprint(bin_path)
    cache_key = ("functions", fp, bin_path)
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    data = run_fission_cli(function_inventory_command(bin_path))
    res = []
    for item in data:
        res.append({
            "address": item.get("address"),
            "name": item.get("name"),
            "size": item.get("size", 0),
            "kind": "function",
        })
    _cache_put(cache_key, res)
    return res


@app.get("/metadata")
def metadata(binary: str):
    bin_path = resolve_binary(binary)
    cache_key = _ck("metadata", bin_path)
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached
    try:
        result = run_fission_cli(program_metadata_command(bin_path))
    except HTTPException as exc:
        raise HTTPException(
            status_code=501,
            detail=(
                "installed Fission CLI does not expose inventory program-metadata; "
                f"use a current local build: {exc.detail}"
            ),
        ) from exc
    _cache_put(cache_key, result)
    return result


def _normalize_hex_bytes(raw: object) -> str:
    """Normalize instruction bytes to compact lowercase hex without spaces."""
    text = str(raw or "").strip().lower().replace(" ", "").replace("0x", "")
    return text


def _as_int(value: object, default: int = 0) -> int:
    """Coerce CLI JSON fields that may be null/str into int without raising."""
    if value is None or value is False:
        return default
    try:
        if isinstance(value, str):
            text = value.strip().lower()
            if not text:
                return default
            return int(text, 16) if text.startswith("0x") else int(text, 0)
        return int(value)
    except (TypeError, ValueError):
        return default


def _ck(kind: str, bin_path: str, *parts: str) -> tuple:
    """Cache key including content fingerprint for the binary path."""
    return (kind, _binary_fingerprint(bin_path), bin_path, *parts)


def _disasm_impl(bin_path: str, addr: str) -> list:
    cache_key = _ck("disasm", bin_path, _normalize_addr_key(addr))
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]
    data = run_fission_cli(["disasm", bin_path, "--addr", addr, "--function", "--json"])
    res = []
    for inst in data.get("instructions", []):
        byte_hex = _normalize_hex_bytes(inst.get("bytes"))
        text = (inst.get("instruction") or "").strip()
        parts = text.split(None, 1)
        res.append({
            "address": inst.get("address"),
            "bytes": byte_hex,
            "mnemonic": parts[0].lower() if parts else "",
            "operands": parts[1] if len(parts) > 1 else "",
            "length": len(byte_hex) // 2 if byte_hex else 0,
            "fallthrough": None,
            "branch_target": None,
        })
    _cache_put(cache_key, res)
    return res


def _disasm_to_decode(disasm_data: list) -> list:
    res = []
    for inst in disasm_data:
        res.append({
            "address": inst.get("address"),
            "bytes": inst.get("bytes"),
            "length": inst.get("length"),
            "mnemonic": inst.get("mnemonic"),
            "prefixes": [],
            "modrm": None,
            "sib": None,
            "displacement": None,
            "immediate": None,
        })
    return res


@app.get("/disasm")
def disasm(binary: str, addr: str):
    validate_address(addr)
    return _disasm_impl(resolve_binary(binary), addr)


@app.get("/decode")
def decode(binary: str, addr: str):
    validate_address(addr)
    # Free: derived from disasm (no second CLI).
    return _disasm_to_decode(_disasm_impl(resolve_binary(binary), addr))


def _space_name(space_id: object) -> str:
    sid = _as_int(space_id, 0)
    return {
        0: "const",
        2: "unique",
        3: "ram",
        4: "register",
    }.get(sid, f"space_{sid}")


def _map_varnode(node: dict | None) -> dict | None:
    if not node:
        return None
    return {
        "space": _space_name(node.get("space_id", 0)),
        "offset": f"0x{_as_int(node.get('offset', 0)):x}",
        "size": _as_int(node.get("size", 0)),
    }


def _pcode_impl(bin_path: str, addr: str) -> list:
    cache_key = _ck("pcode", bin_path, _normalize_addr_key(addr))
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]
    data = run_fission_cli(["raw-pcode", bin_path, "--addr", addr, "--json"])
    blocks = []
    if isinstance(data.get("pcode"), dict) and isinstance(data["pcode"].get("blocks"), list):
        blocks = data["pcode"]["blocks"]
    elif isinstance(data.get("raw_pcode_blocks"), list):
        blocks = data["raw_pcode_blocks"]

    res = []
    seq = 0
    for block in blocks:
        for op in block.get("ops", []):
            res.append({
                "seq": seq,
                "op": op.get("opcode") or op.get("asm_mnemonic") or "UNKNOWN",
                "output": _map_varnode(op.get("output")),
                "inputs": [
                    _map_varnode(node)
                    for node in (op.get("inputs") or [])
                    if isinstance(node, dict)
                ],
            })
            seq += 1
    _cache_put(cache_key, res)
    return res


def _cfg_impl(bin_path: str, addr: str) -> dict:
    cache_key = _ck("cfg", bin_path, _normalize_addr_key(addr))
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached  # type: ignore[return-value]
    data = run_fission_cli(["pcode-topology", bin_path, "--addr", addr, "--json"])
    topo = data.get("raw_pcode_topology") if isinstance(data.get("raw_pcode_topology"), dict) else {}
    raw_blocks = topo.get("blocks") if isinstance(topo.get("blocks"), list) else data.get("raw_pcode_blocks")
    if not isinstance(raw_blocks, list):
        raw_blocks = []

    # Map instruction start → length so block ends can be Ghidra-compatible
    # inclusive last-byte addresses (terminal_address alone is last-insn start).
    insn_len: dict[int, int] = {}
    try:
        for inst in _disasm_impl(bin_path, addr) or []:
            if not isinstance(inst, dict):
                continue
            ia = _as_int(inst.get("address"), 0)
            ln = _as_int(inst.get("length"), 0)
            if ia and ln > 0:
                insn_len[ia] = ln
    except Exception:
        insn_len = {}

    by_index = {_as_int(b.get("index", i), i): b for i, b in enumerate(raw_blocks)}
    blocks = []
    edges = []
    for block in raw_blocks:
        start_raw = _as_int(block.get("start_address", 0))
        terminal = _as_int(block.get("terminal_address", start_raw), start_raw)
        # Prefer explicit inclusive end if CLI ever provides it.
        if block.get("end_address") is not None or block.get("max_address") is not None:
            end_raw = _as_int(block.get("end_address", block.get("max_address")), terminal)
        else:
            ln = insn_len.get(terminal, 0)
            end_raw = (terminal + ln - 1) if ln > 0 else terminal
        start = f"0x{start_raw:x}"
        end = f"0x{end_raw:x}"
        blocks.append({"start": start, "end": end})
        for succ in block.get("successors") or []:
            target_block = by_index.get(_as_int(succ))
            if not target_block:
                continue
            edges.append({
                "source": start,
                "target": f"0x{_as_int(target_block.get('start_address', 0)):x}",
                "kind": "branch",
            })
    out = {
        "blocks": blocks,
        "edges": edges,
        "end_encoding": "inclusive_last_byte",
    }
    _cache_put(cache_key, out)
    return out


@app.get("/pcode")
def pcode(binary: str, addr: str):
    validate_address(addr)
    return _pcode_impl(resolve_binary(binary), addr)


@app.get("/cfg")
def cfg(binary: str, addr: str):
    validate_address(addr)
    return _cfg_impl(resolve_binary(binary), addr)


def _split_c_parameters(args: str) -> list[str]:
    """Split C parameters without breaking nested function-pointer declarators."""
    parts: list[str] = []
    start = 0
    paren_depth = 0
    bracket_depth = 0
    for idx, char in enumerate(args):
        if char == "(":
            paren_depth += 1
        elif char == ")":
            paren_depth = max(0, paren_depth - 1)
        elif char == "[":
            bracket_depth += 1
        elif char == "]":
            bracket_depth = max(0, bracket_depth - 1)
        elif char == "," and paren_depth == 0 and bracket_depth == 0:
            part = args[start:idx].strip()
            if part:
                parts.append(part)
            start = idx + 1
    tail = args[start:].strip()
    if tail:
        parts.append(tail)
    return parts


def _parse_c_parameter(decl: str, index: int) -> dict:
    import re

    text = re.sub(r"\s+", " ", decl.strip())
    if text == "...":
        return {"index": index, "name": "...", "type": "..."}
    function_pointer = re.match(
        r"^(?P<return>.+?)\s*\(\s*\*\s*(?P<name>[A-Za-z_]\w*)\s*\)\s*"
        r"\((?P<args>.*)\)$",
        text,
    )
    if function_pointer:
        return {
            "index": index,
            "name": function_pointer.group("name"),
            "type": (
                f"{function_pointer.group('return').strip()} (*)"
                f"({function_pointer.group('args').strip()})"
            ),
        }
    ordinary = re.match(
        r"^(?P<type>.+?)(?P<name>[A-Za-z_]\w*)\s*(?P<array>\[[^]]*\])?$",
        text,
    )
    if ordinary:
        ty = ordinary.group("type").strip()
        array = ordinary.group("array")
        if array:
            ty = f"{ty} {array.strip()}"
        return {
            "index": index,
            "name": ordinary.group("name"),
            "type": ty,
        }
    return {"index": index, "name": f"param_{index}", "type": text}


def _parse_c_signature(code: str) -> tuple[str | None, list[dict]]:
    """Parse recovered return and parameter types from the decompilation head."""
    import re

    if not code:
        return None, []
    # First non-empty non-comment line
    for line in code.splitlines():
        text = line.strip()
        if not text or text.startswith("//") or text.startswith("/*"):
            continue
        m = re.match(
            r"^([A-Za-z_][\w\s\*]+?)\s+([A-Za-z_]\w*)\s*\((.*)\)\s*\{?$",
            text,
        )
        if not m:
            continue
        ret = re.sub(r"\s+", " ", m.group(1).strip())
        args = m.group(3).strip()
        if not args or args == "void":
            return ret, []
        params = [
            _parse_c_parameter(part, idx)
            for idx, part in enumerate(_split_c_parameters(args))
        ]
        return ret, params
    return None, []


def _parse_c_structs(code: str, *, pointer_size: int) -> list[dict]:
    """Extract aggregate layouts emitted by Fission's typed C surface.

    This consumes actual decompiler-owned typedefs. Synthetic `_pad_*` members
    advance layout but are not reported as semantic fields.
    """
    import re

    primitive_sizes = {
        "bool": 1,
        "char": 1,
        "signed char": 1,
        "unsigned char": 1,
        "short": 2,
        "unsigned short": 2,
        "int": 4,
        "uint": 4,
        "unsigned int": 4,
        "long": 4,
        "unsigned long": 4,
        "longlong": 8,
        "ulonglong": 8,
        "long long": 8,
        "unsigned long long": 8,
        "float": 4,
        "double": 8,
    }

    def declaration_size(ty: str, count: int) -> int:
        normalized = re.sub(r"\s+", " ", ty.strip())
        element_size = (
            pointer_size
            if "*" in normalized
            else primitive_sizes.get(normalized, 0)
        )
        return element_size * count

    structs: list[dict] = []
    typedef = re.compile(
        r"typedef\s+struct\s+(?P<tag>[A-Za-z_]\w*)\s*\{"
        r"(?P<body>.*?)\}\s*(?P<alias>[A-Za-z_]\w*)\s*;",
        re.DOTALL,
    )
    declaration = re.compile(
        r"^(?P<type>.+?)\s+(?P<name>[A-Za-z_]\w*)"
        r"(?:\[(?P<count>\d+)\])?\s*;$"
    )
    for match in typedef.finditer(code):
        fields: list[dict] = []
        cursor = 0
        for raw_line in match.group("body").splitlines():
            field_match = declaration.match(raw_line.strip())
            if not field_match:
                continue
            ty = field_match.group("type").strip()
            name = field_match.group("name")
            count = int(field_match.group("count") or 1)
            size = declaration_size(ty, count)
            encoded_offset = re.fullmatch(r"field_([0-9a-fA-F]+)", name)
            offset = int(encoded_offset.group(1), 16) if encoded_offset else cursor
            cursor = max(cursor, offset + size)
            if name.startswith("_pad_"):
                continue
            fields.append(
                {
                    "name": name,
                    "offset": offset,
                    "size": size,
                    "type": ty,
                }
            )
        if fields:
            structs.append(
                {
                    "name": match.group("alias"),
                    "size": cursor,
                    "fields": fields,
                }
            )
    return structs


def _windows_param_locations(param_count: int, *, bits: int) -> list[dict]:
    """Default Windows PE locations for the first N parameters."""
    if bits == 32:
        # cdecl/stdcall: all stack params (right-to-left); we only report slots.
        return [
            {"index": i, "name": f"param_{i}", "location": f"stack+0x{i * 4:x}", "size": 4}
            for i in range(param_count)
        ]
    # x64: RCX, RDX, R8, R9 then stack
    regs = ["rcx", "rdx", "r8", "r9"]
    out = []
    for i in range(param_count):
        if i < len(regs):
            out.append({"index": i, "name": f"param_{i}", "location": regs[i], "size": 8})
        else:
            # shadow space starts at 0x20; 8-byte slots thereafter
            off = 0x20 + (i - 4) * 8
            out.append(
                {
                    "index": i,
                    "name": f"param_{i}",
                    "location": f"stack+0x{off:x}",
                    "size": 8,
                }
            )
    return out


def _abi_impl(bin_path: str, addr: str) -> dict:
    cache_key = _ck("abi", bin_path, _normalize_addr_key(addr))
    cached = _cache_get(cache_key)
    if isinstance(cached, dict):
        return cached
    # Prefer decomp JSON for signature text.
    try:
        data = run_fission_cli(["decomp", bin_path, "--addr", addr, "--json"])
    except Exception as exc:
        return {
            "status": "error",
            "address": addr,
            "error": str(exc),
            "parameters": [],
            "return": None,
        }
    item: dict = {}
    if isinstance(data, list) and data:
        item = data[0] if isinstance(data[0], dict) else {}
    elif isinstance(data, dict):
        fns = data.get("functions") or data.get("results") or []
        if isinstance(fns, list) and fns and isinstance(fns[0], dict):
            item = fns[0]
        else:
            item = data
    code = str(item.get("code") or item.get("code_nir") or "")
    ret_ty, parsed_params = _parse_c_signature(code)
    nparams = len(parsed_params)
    # Infer bitness from path / pe: m32 in name → 32-bit
    bits = 32 if "m32" in bin_path or "-m32" in bin_path else 64
    convention = "windows_x86" if bits == 32 else "windows_x64"
    params = _windows_param_locations(nparams, bits=bits)
    for location, recovered in zip(params, parsed_params):
        location["name"] = recovered["name"]
        location["type"] = recovered["type"]
    ret = {
        "index": -1,
        "name": "return",
        "location": "eax" if bits == 32 else "rax",
        "size": 4 if bits == 32 else 8,
        "type": ret_ty,
    }
    out = {
        "status": "ok",
        "address": _normalize_addr_key(addr),
        "name": item.get("name") or "?",
        "convention": convention,
        "parameters": params,
        "return": ret,
        "source": "decomp_signature+windows_default",
        "param_count": nparams,
    }
    _cache_put(cache_key, out)
    return out


@app.get("/abi")
def abi(binary: str, addr: str):
    """Recover ABI slots from decomp signature + PE calling convention defaults."""
    validate_address(addr)
    return _abi_impl(resolve_binary(binary), addr)


def _types_impl(bin_path: str, addr: str) -> dict:
    cache_key = _ck("types", bin_path, _normalize_addr_key(addr))
    cached = _cache_get(cache_key)
    if isinstance(cached, dict):
        return cached
    abi = _abi_impl(bin_path, addr)
    ret = abi.get("return") if isinstance(abi.get("return"), dict) else {}
    code = ""
    try:
        # Reuse decomp text for struct name hints.
        data = run_fission_cli(["decomp", bin_path, "--addr", addr, "--json"])
        item: dict = {}
        if isinstance(data, list) and data and isinstance(data[0], dict):
            item = data[0]
        elif isinstance(data, dict):
            item = data
        code = str(item.get("code") or item.get("code_nir") or "")
    except Exception:
        code = ""
    recovered_ret, recovered_params = _parse_c_signature(code)
    pointer_size = 4 if "m32" in bin_path or "-m32" in bin_path else 8
    recovered_structs = _parse_c_structs(code, pointer_size=pointer_size)
    abi_params = {
        int(p.get("index")): p
        for p in abi.get("parameters") or []
        if isinstance(p, dict) and p.get("index") is not None
    }
    params = []
    for recovered in recovered_params:
        carrier = abi_params.get(int(recovered["index"]), {})
        params.append(
            {
                "index": recovered["index"],
                "name": recovered["name"],
                "type": recovered["type"],
                "size": carrier.get("size") or 0,
            }
        )
    out = {
        "status": "ok",
        "address": _normalize_addr_key(addr),
        "name": abi.get("name"),
        "return_type": recovered_ret or ret.get("type"),
        "return_size": ret.get("size") or 0,
        "parameters": params,
        "structs": recovered_structs,
        "layout_surface": "field_iou",
        "source": (
            "decomp_signature+aggregate_typedefs"
            if recovered_structs
            else "decomp_signature"
        ),
    }
    _cache_put(cache_key, out)
    return out


@app.get("/types")
def types(binary: str, addr: str):
    validate_address(addr)
    return _types_impl(resolve_binary(binary), addr)


def _callgraph_impl(bin_path: str, addr: str) -> dict:
    """Callees inferred from CALL-like ops in raw p-code / disasm (best-effort)."""
    cache_key = _ck("callgraph", bin_path, _normalize_addr_key(addr))
    cached = _cache_get(cache_key)
    if isinstance(cached, dict):
        return cached
    callees: set[str] = set()
    try:
        dis = _disasm_impl(bin_path, addr) or []
        for inst in dis:
            if not isinstance(inst, dict):
                continue
            mn = str(inst.get("mnemonic") or "").lower()
            ops = str(inst.get("operands") or "")
            if mn in {"call", "callq"} or mn.startswith("call"):
                # extract hex address if present
                import re

                m = re.search(r"0x[0-9a-fA-F]+", ops)
                if m:
                    callees.add(f"0x{int(m.group(0), 16):x}")
    except Exception:
        pass
    src = _normalize_addr_key(addr)
    edges = [
        {"source": src, "target": t, "kind": "call"} for t in sorted(callees)
    ]
    out = {
        "status": "ok",
        "address": src,
        "callees": sorted(callees),
        "edges": edges,
        "callee_count": len(callees),
        "source": "disasm_call_targets",
    }
    _cache_put(cache_key, out)
    return out


@app.get("/callgraph")
def callgraph(binary: str, addr: str):
    validate_address(addr)
    return _callgraph_impl(resolve_binary(binary), addr)


def _strings_impl(bin_path: str, addr: str) -> dict:
    """Recover strings via PE scan + disasm/decomp references."""
    cache_key = _ck("strings", bin_path, _normalize_addr_key(addr))
    cached = _cache_get(cache_key)
    if isinstance(cached, dict):
        return cached
    from pe_helpers import (
        strings_from_decomp_code,
        strings_in_pe,
        strings_referenced_by_disasm,
    )

    pe_strings = strings_in_pe(bin_path)
    dis = []
    try:
        dis = _disasm_impl(bin_path, addr) or []
    except Exception:
        dis = []
    found = set(strings_referenced_by_disasm(pe_strings, dis if isinstance(dis, list) else []))
    try:
        data = run_fission_cli(["decomp", bin_path, "--addr", addr, "--json"])
        code = ""
        if isinstance(data, list) and data and isinstance(data[0], dict):
            code = str(data[0].get("code") or "")
        elif isinstance(data, dict):
            code = str(data.get("code") or "")
        found.update(strings_from_decomp_code(code))
    except Exception:
        pass
    out = {
        "status": "ok",
        "address": _normalize_addr_key(addr),
        "strings": sorted(found),
        "count": len(found),
        "pe_string_pool": len(pe_strings),
        "source": "pe_scan+disasm_xref+decomp_literals",
    }
    _cache_put(cache_key, out)
    return out


@app.get("/strings")
def strings_export(binary: str, addr: str):
    validate_address(addr)
    return _strings_impl(resolve_binary(binary), addr)


def _pcode_sink_key(varnode: object) -> str:
    """Canonical `space+offset:size` key shared with ExportParity.java."""
    if not isinstance(varnode, dict):
        return "unknown"
    space = str(varnode.get("space") or "unknown").strip().lower()
    offset = _as_int(varnode.get("offset"), 0)
    size = _as_int(varnode.get("size"), 0)
    return f"{space}+0x{offset:x}:{size}"


def _dataflow_impl(bin_path: str, addr: str) -> dict:
    cache_key = _ck("dataflow", bin_path, _normalize_addr_key(addr))
    cached = _cache_get(cache_key)
    if isinstance(cached, dict):
        return cached
    returns: set[str] = set()
    stores: set[str] = set()
    try:
        ops = _pcode_impl(bin_path, addr) or []
        for op in ops:
            if not isinstance(op, dict):
                continue
            name = str(op.get("op") or "").upper().replace("_", "")
            inputs = op.get("inputs") or []
            if name in {"RET", "RETURN"}:
                # Match ExportParity.java: raw RETURN input 0 is the control
                # destination. A semantic return value exists only at input 1.
                returns.add(_pcode_sink_key(inputs[1]) if len(inputs) > 1 else "void")
            if name == "STORE" and len(inputs) >= 3:
                stores.add(f"{_pcode_sink_key(inputs[1])}<-{_pcode_sink_key(inputs[2])}")
    except Exception as exc:
        return {
            "status": "error",
            "error": str(exc),
            "return_sinks": [],
            "store_sinks": [],
        }
    out = {
        "status": "ok",
        "address": _normalize_addr_key(addr),
        "return_sinks": sorted(returns),
        "store_sinks": sorted(stores),
        "source": "raw_pcode_sinks",
    }
    _cache_put(cache_key, out)
    return out


@app.get("/dataflow")
def dataflow(binary: str, addr: str):
    validate_address(addr)
    return _dataflow_impl(resolve_binary(binary), addr)


@app.get("/seh")
def seh(binary: str, addr: str):
    """PE .pdata RUNTIME_FUNCTION coverage for the function VA (product-independent)."""
    validate_address(addr)
    path = resolve_binary(binary)
    from pe_helpers import function_unwind_info

    info = function_unwind_info(path, addr)
    info.setdefault("is_thunk", False)
    info.setdefault("no_return", False)
    info.setdefault("convention", "unknown")
    info.setdefault("program_eh_symbol_count", info.get("program_runtime_function_count", 0))
    return info


def _assemble_bundle(key: str, dis, pc, cg) -> dict:
    out = {
        "schema": "fission-parity-bundle-v1",
        "address": key,
        "disasm": dis,
        "decode": _disasm_to_decode(dis if isinstance(dis, list) else []),
        "pcode": pc,
        "cfg": cg,
    }
    return out


def _bundle_one(bin_path: str, addr: str) -> dict:
    """disasm + pcode + cfg for one address (decode free from disasm)."""
    key = _normalize_addr_key(addr)
    cache_key = _ck("bundle", bin_path, key)
    cached = _cache_get(cache_key)
    if isinstance(cached, dict):
        return cached

    with ThreadPoolExecutor(max_workers=3) as pool:
        f_dis = pool.submit(_disasm_impl, bin_path, addr)
        f_pcode = pool.submit(_pcode_impl, bin_path, addr)
        f_cfg = pool.submit(_cfg_impl, bin_path, addr)
        dis = f_dis.result()
        pc = f_pcode.result()
        cg = f_cfg.result()

    out = _assemble_bundle(key, dis, pc, cg)
    _cache_put(cache_key, out)
    return out


def _map_addrs(impl, bin_path: str, addrs: List[str], workers: int) -> dict:
    """Run a single CLI-backed tool over many addresses (multi-addr batch)."""
    out: dict = {}
    if not addrs:
        return out
    w = min(max(1, workers), len(addrs))
    with ThreadPoolExecutor(max_workers=w) as pool:
        futures = {pool.submit(impl, bin_path, a): a for a in addrs}
        for fut in as_completed(futures):
            a = futures[fut]
            key = _normalize_addr_key(a)
            try:
                out[key] = fut.result()
            except Exception as exc:
                out[key] = exc
    return out


def _bundle_many(bin_path: str, addrs: List[str]) -> dict:
    """Multi-addr parity bundle for one binary.

    Strategy (process-spawn aware):
      1. Serve full bundles from in-memory cache when present.
      2. For misses, run *tool-phased* multi-addr batches:
         all disasm, all raw-pcode, all pcode-topology — three parallel
         address-maps with a global CLI semaphore. This caps peak
         fission_cli children at FISSION_CLI_WORKERS (not 3×N).
      3. Assemble per-address bundles; decode is free from disasm.
    """
    by_addr: dict = {}
    missing: List[str] = []
    for a in addrs:
        key = _normalize_addr_key(a)
        cached = _cache_get(_ck("bundle", bin_path, key))
        if isinstance(cached, dict):
            by_addr[key] = cached
        else:
            missing.append(a)

    if not missing:
        return by_addr

    # Split CLI budget across the three tools so they can run concurrently.
    per_tool = max(1, _CLI_WORKERS // 3)
    with ThreadPoolExecutor(max_workers=3) as pool:
        f_dis = pool.submit(_map_addrs, _disasm_impl, bin_path, missing, per_tool)
        f_pc = pool.submit(_map_addrs, _pcode_impl, bin_path, missing, per_tool)
        f_cfg = pool.submit(_map_addrs, _cfg_impl, bin_path, missing, per_tool)
        dis_map = f_dis.result()
        pc_map = f_pc.result()
        cfg_map = f_cfg.result()

    for a in missing:
        key = _normalize_addr_key(a)
        dis = dis_map.get(key)
        pc = pc_map.get(key)
        cg = cfg_map.get(key)
        tool_errors: dict = {}
        for label, val in (("disasm", dis), ("pcode", pc), ("cfg", cg)):
            if isinstance(val, Exception):
                tool_errors[label] = str(val)

        # Partial success: keep good surfaces. Full failure only if all tools died.
        if len(tool_errors) == 3:
            by_addr[key] = {"error": "; ".join(f"{k}: {v}" for k, v in tool_errors.items())}
            continue

        dis_ok = dis if not isinstance(dis, Exception) else None
        pc_ok = pc if not isinstance(pc, Exception) else None
        cg_ok = cg if not isinstance(cg, Exception) else None
        # Missing (None) without exception → empty, not a silent success cache of errors.
        if dis_ok is None:
            dis_ok = []
        if pc_ok is None:
            pc_ok = []
        if cg_ok is None:
            cg_ok = {"blocks": [], "edges": []}

        out = _assemble_bundle(key, dis_ok, pc_ok, cg_ok)
        if tool_errors:
            out["tool_errors"] = tool_errors
            # Do not cache partial/error results — retries should re-run tools.
        else:
            # Never cache fully empty multi-surface success (likely failed open).
            if dis_ok or pc_ok or (isinstance(cg_ok, dict) and cg_ok.get("blocks")):
                _cache_put(_ck("bundle", bin_path, key), out)
        by_addr[key] = out
    return by_addr


@app.get("/parity_bundle")
def parity_bundle(binary: str, addr: str):
    """One HTTP call → disasm/decode/pcode/cfg (CLI steps parallelized)."""
    validate_address(addr)
    t0 = time.monotonic()
    out = dict(_bundle_one(resolve_binary(binary), addr))
    out["time_ms"] = int((time.monotonic() - t0) * 1000)
    return out


@app.get("/parity_multi_bundle")
def parity_multi_bundle(binary: str, addrs: str):
    """Many addresses on one binary; tool-phased multi-addr batching."""
    t0 = time.monotonic()
    raw_list = [a.strip() for a in addrs.split(",") if a.strip()]
    if not raw_list:
        raise HTTPException(status_code=400, detail="addrs must be non-empty")
    for a in raw_list:
        validate_address(a)
    bin_path = resolve_binary(binary)
    by_addr = _bundle_many(bin_path, raw_list)

    return {
        "schema": "fission-parity-multi-bundle-v1",
        "by_addr": by_addr,
        "time_ms": int((time.monotonic() - t0) * 1000),
        "requested": len(raw_list),
        "cli_workers": _CLI_WORKERS,
        "mode": "tool_phased_multi_addr",
        "binary_fingerprint": _binary_fingerprint(bin_path),
    }

@app.post("/decompile", response_model=DecompileResponse)
def decompile(req: DecompileRequest):
    validate_address(req.addr)
    batch_req = BatchDecompileRequest(binary_b64=req.binary_b64, addresses=[req.addr])
    start = time.monotonic()
    try:
        resp = decompile_batch(batch_req)
        elapsed = int((time.monotonic() - start) * 1000)
        item = resp.results[0]
        if item.error:
            return DecompileResponse(name="?", code="", time_ms=elapsed, error=item.error)
        return DecompileResponse(
            name=item.name,
            code=item.code,
            code_nir=item.code_nir,
            code_hir=item.code_hir,
            layer=item.layer,
            time_ms=elapsed,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/decompile_batch", response_model=BatchDecompileResponse)
def decompile_batch(req: BatchDecompileRequest):
    try:
        binary_bytes = base64.b64decode(req.binary_b64, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 payload")
        
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f_bin:
        f_bin.write(binary_bytes)
        tmp_bin_path = f_bin.name
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f_addrs:
        for addr in req.addresses:
            f_addrs.write(f"{addr}\n")
        tmp_addrs_path = f_addrs.name

    env = {
        **os.environ,
        "FISSION_SLEIGH_SPEC_DIR": SLEIGH_SPEC_DIR,
        "FISSION_RESOURCE_ROOT": RESOURCE_ROOT,
        "FISSION_GHIDRA_DATA_DIR": GHIDRA_DATA_DIR,
    }
    start = time.monotonic()
    # Outer process budget must exceed per-function CLI --timeout-ms × N addrs.
    # Fallback uses a single-addr budget slightly above DECOMP_TIMEOUT_MS.
    try:
        timeout_ms = int(DECOMP_TIMEOUT_MS)
    except ValueError:
        timeout_ms = 120_000
    batch_proc_timeout = max(180.0, (timeout_ms / 1000.0) * max(len(req.addresses), 1) + 60.0)
    single_proc_timeout = max(90.0, timeout_ms / 1000.0 + 30.0)
    try:
        batch_failed = False
        batch_err_detail = ""
        try:
            result = subprocess.run(
                decompile_batch_command(tmp_bin_path, tmp_addrs_path),
                env=env,
                capture_output=True,
                text=True,
                timeout=batch_proc_timeout,
            )
            if result.returncode != 0:
                batch_failed = True
                batch_err_detail = (
                    f"batch exit {result.returncode}: "
                    f"{(result.stderr or result.stdout or '')[:400]}"
                )
            else:
                res_list = normalize_decompile_results(json.loads(result.stdout))
                results = [decompile_result_from_cli_item(item) for item in res_list]
        except Exception as exc:  # noqa: BLE001
            batch_failed = True
            batch_err_detail = f"{type(exc).__name__}: {exc}"

        if batch_failed:
            results = []
            for addr in req.addresses:
                with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f_single:
                    f_single.write(f"{addr}\n")
                    tmp_single_path = f_single.name
                try:
                    res_single = subprocess.run(
                        decompile_batch_command(tmp_bin_path, tmp_single_path),
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=single_proc_timeout,
                    )
                    if res_single.returncode != 0:
                        results.append(DecompileResultItem(
                            addr=addr,
                            error=(
                                f"Batch fallback failed with exit code {res_single.returncode}: "
                                f"{(res_single.stderr or res_single.stdout or '')[:300]}"
                                f" (batch: {batch_err_detail[:200]})"
                            ),
                        ))
                    else:
                        res_list = normalize_decompile_results(json.loads(res_single.stdout))
                        if res_list:
                            results.append(decompile_result_from_cli_item(res_list[0], fallback_addr=addr))
                        else:
                            results.append(DecompileResultItem(
                                addr=addr,
                                error=f"No decompile result returned for address (batch: {batch_err_detail[:200]})",
                            ))
                except Exception as e:
                    results.append(DecompileResultItem(
                        addr=addr,
                        error=(
                            f"Batch fallback failed with exception: {type(e).__name__}: {e} "
                            f"(batch: {batch_err_detail[:200]})"
                        ),
                    ))
                finally:
                    try:
                        os.unlink(tmp_single_path)
                    except Exception:
                        pass
        elapsed = int((time.monotonic() - start) * 1000)
        return BatchDecompileResponse(results=results, time_ms=elapsed)
    finally:
        try:
            os.unlink(tmp_bin_path)
        except Exception:
            pass
        try:
            os.unlink(tmp_addrs_path)
        except Exception:
            pass
