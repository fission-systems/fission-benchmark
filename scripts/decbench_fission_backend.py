"""Out-of-tree DecBench `Decompiler` plugin for Fission.

Not part of the `decbench` package itself (that's a separate vendored/pip
install, see `decbench_local_eval.py`'s module docstring for setup) -- this
registers Fission with DecBench's real `Decompiler` registry so its actual
GED/type_match/byte_match metric code can run against Fission's own output,
independent of (and cross-checking) this repo's own `runner/ged.py` etc.

Import this module once (its `@register_decompiler("fission")` runs as an
import-time side effect) before calling anything in `decbench.pipeline.*`.
`decbench_local_eval.py` does this for you; a one-off REPL/script needs the
same `import decbench_fission_backend  # noqa: F401` before touching decbench.

Mirrors the shape of decbench's own `decompilers/raw/kuna_raw.py` (a CLI
shell-out, whole-binary batch decompiler) -- see that file in a decbench
checkout for the canonical in-tree pattern this follows.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Any

from decbench.decompilers.base import Decompiler
from decbench.decompilers.raw import common
from decbench.decompilers.registry import register_decompiler
from decbench.models.decompilation import (
    DecompilationResult,
    DecompilerMetadata,
    FunctionDecompilation,
)

_l = logging.getLogger(__name__)

# ``<ret type stuff> <name>(`` at the end of a declarator line. Fission's CLI
# JSON has no dedicated function-name field -- the name is parsed out of the
# decompiled code's own first line instead, which is real (DWARF-derived)
# when the input binary isn't stripped. A trailing ``;`` with no ``(``
# (Fission's ``undefined some_name;``/``typedef struct ... ;`` entries for
# non-function symbols it also reports under ``--all``) never matches, so
# those are dropped naturally rather than needing an explicit filter.
_DECLARATOR = re.compile(r"([A-Za-z_]\w*)\s*\([^()]*\)\s*$")


def _fission_bin() -> str | None:
    """Resolve the ``fission_cli`` executable.

    ``FISSION_CLI`` is the primary, explicit way to point this at a build;
    falls back to ``$PATH``.
    """
    env = os.environ.get("FISSION_CLI")
    if env and Path(env).is_file():
        return env
    return shutil.which("fission_cli")


def _function_name(code: str) -> str | None:
    """The function's own declarator line, not necessarily `code`'s first
    line: NIR prints any `typedef struct fission_aggN {...};` an aggregate
    parameter/return type needs, and any referenced global's own declaration,
    BEFORE the function signature -- both real, whole-program-scoped output,
    not noise to strip, but they mean "first line" is only ever the real
    declarator for a function with no aggregate types and no global refs.
    Every Fission-printed function body opens with `<signature>\\n{\\n`
    (`render/printer.rs`'s `print_hir_function_impl`: `")\\n{\\n"` after the
    signature, unconditionally) -- the line immediately before a
    lone-`{`-line is the real declarator regardless of what precedes it.
    An earlier first-line-only version of this function silently mis-scored
    every aggregate/global-referencing function as "never decompiled" in a
    real-corpus DecBench comparison (48/48 real functions in one binary
    wrongly counted as 16/48) before this was caught by manually inspecting
    one "missing" function's full code.
    """
    lines = code.split("\n")
    for i, line in enumerate(lines):
        if line.strip() == "{":
            m = _DECLARATOR.search(lines[i - 1].strip())
            return m.group(1) if m else None
    return None


class RawFissionDecompiler(Decompiler):
    """Fission driven via its CLI's `--all` whole-binary batch mode.

    `layer` selects which of Fission's two pseudocode surfaces (see
    `crates/fission-pcode/src/render/layer.rs`) this decompiler id scores:
    NIR ("semantic-faithful mechanical C", the default/oracle surface) vs
    HIR ("human-readable presentation" -- elides some casts, drops unused-
    noise locals). Registered as two separate decompiler ids (`fission` /
    `fission-hir`) rather than a config knob so both show up as ordinary,
    independently comparable columns through the exact same
    decompile/evaluate pipeline everything else in this harness uses --
    this is what actually answers "which layer scores better" with real
    GED/type_match/byte_match numbers instead of just reading the doc
    comment's stated intent.
    """

    name = "fission"
    display_name = "Fission"
    layer = "nir"

    @staticmethod
    def _bin() -> str | None:
        return _fission_bin()

    def is_available(self) -> bool:
        return self._bin() is not None

    def get_version(self) -> str | None:
        exe = self._bin()
        if not exe:
            return None
        try:
            proc = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=30)
            out = (proc.stdout or proc.stderr or "").strip()
            m = re.search(r"(\d+\.\d+\.\d+\S*)", out)
            return m.group(1) if m else (out.splitlines()[0] if out else "unknown")
        except Exception:  # noqa: BLE001
            return "unknown"

    def _run_all(self, binary_path: Path, timeout_s: float) -> list[dict[str, Any]]:
        exe = self._bin()
        assert exe is not None
        cmd = [
            exe,
            "decomp",
            str(binary_path),
            "--all",
            "--layer",
            self.layer,
            "--json",
            "--no-header",
            "--no-warnings",
            # Without this, a single pathologically slow function blocks the
            # whole `--all` batch (and every OTHER target function in the
            # same binary) up to the full `binary_timeout_seconds`, instead
            # of just falling out as one miss. 45s matches the real DecBench
            # sample-set submission's own per-function budget
            # (`run_fission.py`), so this stays realistic rather than
            # optimistic about what a real submission would actually score.
            "--timeout-ms",
            "45000",
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
        stdout = (proc.stdout or "").strip()
        if not stdout:
            tail = (proc.stderr or "").strip().splitlines()[-5:]
            raise RuntimeError(f"empty stdout (exit {proc.returncode}): {' | '.join(tail)}")
        payload = json.loads(stdout)
        return payload if isinstance(payload, list) else [payload]

    def decompile_binary(
        self,
        binary_path: Path,
        functions: list[tuple[str, int]] | None = None,
        output_dir: Path | None = None,
        function_names: set[str] | None = None,
        progress_path: Path | None = None,
    ) -> DecompilationResult:
        if not self.is_available():
            raise RuntimeError(
                f"Decompiler '{self.name}' is not available "
                f"(set $FISSION_CLI to a fission_cli build, or add it to PATH)"
            )

        start = time.time()
        text_range = common.elf_text_range(binary_path)
        timeout_s = self.config.binary_timeout_seconds

        def _meta(failed: list[str], extra: dict[str, Any]) -> DecompilerMetadata:
            return DecompilerMetadata(
                decompiler_name=self.id,
                decompiler_version=self.get_version(),
                total_time_seconds=time.time() - start,
                timeout_occurred=bool(extra.get("timeout")),
                failed_functions=failed,
                extra={"backend": "fission", "via": "raw", **extra},
            )

        try:
            records = self._run_all(binary_path, timeout_s)
        except subprocess.TimeoutExpired:
            _l.warning("fission-raw timed out on %s", binary_path)
            return DecompilationResult(
                binary_path=binary_path,
                binary_name=binary_path.stem,
                decompiler=_meta(["all"], {"error": f"timeout after {timeout_s}s", "timeout": True}),
                output_dir=output_dir,
            )
        except Exception as e:  # noqa: BLE001
            _l.error("fission-raw failed on %s: %s", binary_path, e)
            return DecompilationResult(
                binary_path=binary_path,
                binary_name=binary_path.stem,
                decompiler=_meta(["all"], {"error": str(e)}),
                output_dir=output_dir,
            )

        decompiled: dict[str, FunctionDecompilation] = {}
        unaddressed: list[str] = []
        enumerated: list[tuple[str, int, str]] = []

        for rec in records:
            code = rec.get("code") or ""
            addr_str = rec.get("address")
            if not code or addr_str is None:
                continue
            name = _function_name(code)
            if not name:
                continue
            try:
                file_addr = int(str(addr_str), 0)
            except ValueError:
                unaddressed.append(name)
                continue
            if common.should_skip_function(name, file_addr, text_range):
                continue
            enumerated.append((name, file_addr, code))

        by_key = {(n, a): c for n, a, c in enumerated}
        addr_pairs = [(n, a) for n, a, _c in enumerated]
        if functions is not None:
            requested = {n for (n, _a) in functions}
            addr_pairs = [(n, a) for (n, a) in addr_pairs if n in requested]
        addr_pairs = common.narrow_to_source(
            addr_pairs, function_names, backend="fission", binary_name=binary_path.name
        )

        for name, file_addr in addr_pairs:
            code = by_key.get((name, file_addr))
            if code is None:
                unaddressed.append(name)
                continue
            decompiled[name] = FunctionDecompilation(
                name=name,
                address=file_addr,
                decompiled_code=code,
                line_count=code.count("\n") + 1,
                metadata=common.extract_metrics(code),
            )

        result = DecompilationResult(
            binary_path=binary_path,
            binary_name=binary_path.stem,
            decompiler=_meta(unaddressed, {"record_count": len(records)}),
            functions=decompiled,
            output_dir=output_dir,
        )

        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            result.to_c_file(output_dir / f"{self.name}_{binary_path.stem}.c")
            result.to_toml(output_dir / f"{self.name}_{binary_path.stem}.toml")

        return result


class RawFissionHirDecompiler(RawFissionDecompiler):
    """Same backend, scoring Fission's HIR ("human-readable") surface instead
    of NIR -- registered separately so `--decompilers fission,fission-hir`
    compares both through the identical decompile/evaluate pipeline."""

    name = "fission-hir"
    display_name = "Fission (HIR)"
    layer = "hir"


register_decompiler("fission")(RawFissionDecompiler)
register_decompiler("fission-hir")(RawFissionHirDecompiler)
