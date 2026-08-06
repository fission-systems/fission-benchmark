"""Ghidra headless decompiler and parity diagnostic API server.

Performance features for layered parity:
  1. Persistent project cache (no -deleteProject) keyed by path + content fingerprint.
  2. /parity_bundle — one headless run emits disasm+pcode+cfg.
  3. In-process result cache for repeated (content, mode, addr) hits.
  4. [FAST PATH] pyghidra persistent JVM: JVM is started once at server startup
     and reused for all subsequent requests, eliminating 4-5s per-request
     JVM startup overhead. Falls back to subprocess analyzeHeadless if pyghidra
     is unavailable or raises an unexpected error.
"""
from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="ghidra-decompiler", version="1.3")
GHIDRA_HOME = Path("/opt/ghidra")
GHIDRA_HEADLESS = GHIDRA_HOME / "support" / "analyzeHeadless"
SCRIPT_DIR = Path("/opt/ghidra_scripts")
BATCH_MARKER = "===BATCH_RESULT==="
PROJECT_CACHE = Path(os.environ.get("GHIDRA_PROJECT_CACHE", "/var/cache/ghidra-projects"))
PROJECT_CACHE.mkdir(parents=True, exist_ok=True)

# ── pyghidra persistent JVM ───────────────────────────────────────────────────
# If GHIDRA_USE_PYGHIDRA=0 is set, disable the fast path entirely.
_USE_PYGHIDRA = os.environ.get("GHIDRA_USE_PYGHIDRA", "1") not in {"0", "false", "no"}
_pyghidra_ready = False  # set to True once JVM is successfully started
_pyghidra_lock = threading.Lock()  # serialize program-open calls
_pyghidra_error: str | None = None  # non-None if startup failed permanently

if _USE_PYGHIDRA:
    try:
        import pyghidra as _pyghidra  # type: ignore[import]
        _PYGHIDRA_AVAILABLE = True
    except ImportError:
        _PYGHIDRA_AVAILABLE = False
        logging.warning("pyghidra not installed — using subprocess fallback")
else:
    _PYGHIDRA_AVAILABLE = False

# ─────────────────────────────────────────────────────────────────────────────

# Concurrent analyzeHeadless is safe for *different* project keys (one PE each).
# Cap total JVM headless processes; serialize same-project work to avoid import races.
_HEADLESS_WORKERS = max(1, int(os.environ.get("GHIDRA_HEADLESS_WORKERS", "3")))
_HEADLESS_SEM = threading.Semaphore(_HEADLESS_WORKERS)
_PROJECT_LOCKS: dict[str, threading.Lock] = {}
_PROJECT_LOCKS_GUARD = threading.Lock()

# Cache key includes content fingerprint so corpus rebuilds at the same path
# do not serve stale analysis.
_PARITY_CACHE: dict[tuple, object] = {}
_PARITY_CACHE_MAX = 1024
_IMPORTED_PROJECTS: set[str] = set()
_PARITY_CACHE_LOCK = threading.Lock()
_FP_CACHE: dict[str, tuple[int, int, str]] = {}  # path -> (size, mtime_ns, fp)


def _project_lock(project_name: str) -> threading.Lock:
    with _PROJECT_LOCKS_GUARD:
        lock = _PROJECT_LOCKS.get(project_name)
        if lock is None:
            lock = threading.Lock()
            _PROJECT_LOCKS[project_name] = lock
        return lock


@app.on_event("startup")
def _startup_pyghidra() -> None:
    """Start the persistent JVM once at server startup.

    Runs in a background thread so uvicorn starts accepting HTTP requests
    immediately while Ghidra initialises (avoids Docker health-check timeouts).
    """
    global _pyghidra_ready, _pyghidra_error  # noqa: PLW0603
    if not _PYGHIDRA_AVAILABLE:
        return

    def _init():
        global _pyghidra_ready, _pyghidra_error  # noqa: PLW0603
        try:
            logging.info("[pyghidra] Starting persistent JVM (install_dir=%s)…", GHIDRA_HOME)
            _pyghidra.start(install_dir=GHIDRA_HOME)
            _pyghidra_ready = True
            logging.info("[pyghidra] JVM ready — fast path active")
        except Exception as exc:  # noqa: BLE001
            _pyghidra_error = str(exc)
            logging.warning("[pyghidra] JVM startup failed (%s) — subprocess fallback active", exc)

    threading.Thread(target=_init, daemon=True, name="pyghidra-init").start()


def _run_via_pyghidra(binary_path: str, mode: str, addr: str = "") -> object | None:
    """Fast path: run ExportParity.java in the persistent JVM (no subprocess).

    Captures the ===RESULT=== line that ExportParity prints to System.out
    and returns the parsed JSON. Returns None on any failure so the caller
    falls back to subprocess analyzeHeadless.
    """
    if not _PYGHIDRA_AVAILABLE or not _pyghidra_ready:
        return None

    try:
        import jpype  # type: ignore[import]

        # Redirect Java System.out to a ByteArrayOutputStream so we can capture
        # the ===RESULT=== line from ExportParity.java without subprocess.
        PrintStream = jpype.JClass("java.io.PrintStream")  # type: ignore[attr-defined]
        ByteArrayOutputStream = jpype.JClass("java.io.ByteArrayOutputStream")  # type: ignore[attr-defined]
        baos = ByteArrayOutputStream()
        ps = PrintStream(baos)
        original_out = jpype.java.lang.System.out  # type: ignore[attr-defined]

        script_args = [mode, addr] if addr else [mode]

        with _pyghidra_lock:
            try:
                jpype.java.lang.System.setOut(ps)  # type: ignore[attr-defined]
                _pyghidra.run_script(
                    binary_path,
                    str(SCRIPT_DIR / "ExportParity.java"),
                    project_location=str(PROJECT_CACHE),
                    project_name=f"bin_{_project_key(binary_path)}",
                    script_args=script_args,
                    analyze=not _project_exists(f"bin_{_project_key(binary_path)}"),
                )
            finally:
                jpype.java.lang.System.setOut(original_out)  # type: ignore[attr-defined]
                captured = str(baos.toString("UTF-8"))

        # Parse ===RESULT=== from captured output
        for line in captured.splitlines():
            idx = line.find("===RESULT===")
            if idx < 0:
                continue
            payload = line[idx + len("===RESULT==="):].strip()
            if payload.endswith("(GhidraScript)"):
                payload = payload[: -len("(GhidraScript)")].strip()
            try:
                res = json.loads(payload)
                if isinstance(res, dict) and "error" in res:
                    return None  # let subprocess handle errors
                return res
            except json.JSONDecodeError:
                return None

        return None  # ===RESULT=== not found
    except Exception as exc:  # noqa: BLE001
        logging.debug("[pyghidra fast path] %s — falling back to subprocess", exc)
        return None



class DecompileRequest(BaseModel):
    binary_b64: str
    addr: str


class DecompileResponse(BaseModel):
    decompiler: str = "ghidra"
    name: str
    code: str
    time_ms: int
    error: Optional[str] = None


class BatchDecompileRequest(BaseModel):
    binary_b64: str
    addresses: List[str]


class DecompileResultItem(BaseModel):
    addr: str
    name: str = "?"
    code: str = ""
    error: Optional[str] = None


class BatchDecompileResponse(BaseModel):
    decompiler: str = "ghidra"
    results: List[DecompileResultItem]
    time_ms: int


def _extract_marked_json_line(text: str, marker: str) -> object | None:
    for line in text.splitlines():
        marker_index = line.find(marker)
        if marker_index < 0:
            continue
        payload = line[marker_index + len(marker) :].strip()
        if payload.endswith("(GhidraScript)"):
            payload = payload[: -len("(GhidraScript)")].strip()
        return json.loads(payload)
    return None


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


def _resolve_binary(binary_path: str) -> str:
    if not binary_path or not binary_path.strip():
        raise HTTPException(status_code=400, detail="Binary path cannot be empty")
    resolved = "/" + binary_path if binary_path.startswith("corpus/") else binary_path
    if not os.path.exists(resolved):
        raise HTTPException(status_code=404, detail=f"Binary not found: {resolved}")
    return resolved


def _binary_fingerprint(binary_path: str) -> str:
    """Content-sensitive fingerprint (size + mtime + head/tail sample).

    Full SHA-256 of multi-MB PE is unnecessary; head+tail+size catches rebuilds
    that keep the same path. Invalidates when file content or length changes.
    """
    try:
        st = os.stat(binary_path)
    except OSError:
        return "missing"
    cached = _FP_CACHE.get(binary_path)
    if cached and cached[0] == st.st_size and cached[1] == st.st_mtime_ns:
        return cached[2]
    h = hashlib.sha256()
    h.update(f"{st.st_size}:{st.st_mtime_ns}".encode("utf-8"))
    try:
        with open(binary_path, "rb") as fh:
            h.update(fh.read(65536))
            if st.st_size > 65536:
                fh.seek(max(0, st.st_size - 65536))
                h.update(fh.read(65536))
    except OSError:
        return f"err-{st.st_size}-{st.st_mtime_ns}"
    fp = h.hexdigest()[:16]
    _FP_CACHE[binary_path] = (st.st_size, st.st_mtime_ns, fp)
    return fp


def _project_key(binary_path: str) -> str:
    fp = _binary_fingerprint(binary_path)
    return hashlib.sha256(f"{binary_path}|{fp}".encode("utf-8")).hexdigest()[:20]


def _project_exists(project_name: str) -> bool:
    # Ghidra creates <name>.rep directory (and .gpr) for a project.
    return (PROJECT_CACHE / f"{project_name}.rep").exists() or (
        PROJECT_CACHE / f"{project_name}.gpr"
    ).exists()


def _cache_put(key: tuple, value: object) -> None:
    with _PARITY_CACHE_LOCK:
        if len(_PARITY_CACHE) >= _PARITY_CACHE_MAX:
            try:
                del _PARITY_CACHE[next(iter(_PARITY_CACHE))]
            except StopIteration:
                pass
        _PARITY_CACHE[key] = value


def _safe_program_name(binary_path: str) -> str:
    # Ghidra program name is typically the file name.
    return Path(binary_path).name


def _run_headless_parity(binary_path: str, mode: str, addr: str = "") -> object:
    """Run ExportParity — tries pyghidra persistent JVM first, then subprocess.

    Fast path: _run_via_pyghidra reuses the JVM started at server startup,
    eliminating ~4-5s JVM cold-start overhead per request.
    Slow path (fallback): subprocess analyzeHeadless (original behaviour).
    """
    # ── Fast path: persistent JVM ──────────────────────────────────────────
    fast = _run_via_pyghidra(binary_path, mode, addr)
    if fast is not None:
        return fast
    # ── Slow path: subprocess analyzeHeadless ──────────────────────────────

    project_name = f"bin_{_project_key(binary_path)}"
    program_name = _safe_program_name(binary_path)
    exists = _project_exists(project_name) or project_name in _IMPORTED_PROJECTS

    if exists:
        args = [
            str(GHIDRA_HEADLESS),
            str(PROJECT_CACHE),
            project_name,
            "-process",
            program_name,
            "-noanalysis",
            "-scriptPath",
            str(SCRIPT_DIR),
            "-postScript",
            "ExportParity.java",
            mode,
            addr,
        ]
    else:
        args = [
            str(GHIDRA_HEADLESS),
            str(PROJECT_CACHE),
            project_name,
            "-import",
            binary_path,
            "-overwrite",
            "-scriptPath",
            str(SCRIPT_DIR),
            "-postScript",
            "ExportParity.java",
            mode,
            addr,
        ]

    # Same project must be exclusive (import/process races); different projects
    # may run concurrently up to GHIDRA_HEADLESS_WORKERS.
    with _project_lock(project_name):
        with _HEADLESS_SEM:
            result = subprocess.run(args, capture_output=True, text=True, timeout=240)

        combined = (result.stdout or "") + "\n" + (result.stderr or "")
        for line in combined.splitlines():
            idx = line.find("===RESULT===")
            if idx < 0:
                continue
            payload = line[idx + len("===RESULT===") :].strip()
            if payload.endswith("(GhidraScript)"):
                payload = payload[: -len("(GhidraScript)")].strip()
            try:
                res = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise HTTPException(
                    status_code=500,
                    detail=f"Invalid ExportParity JSON: {exc}: {payload[:200]}",
                ) from exc
            if isinstance(res, dict) and "error" in res:
                # If process failed because program missing, retry once with import.
                if exists and "not found" in str(res.get("error", "")).lower():
                    break
                raise HTTPException(status_code=500, detail=res["error"])
            _IMPORTED_PROJECTS.add(project_name)
            return res

        # Fallback: force re-import if process path failed
        if exists:
            args = [
                str(GHIDRA_HEADLESS),
                str(PROJECT_CACHE),
                project_name,
                "-import",
                binary_path,
                "-overwrite",
                "-scriptPath",
                str(SCRIPT_DIR),
                "-postScript",
                "ExportParity.java",
                mode,
                addr,
            ]
            with _HEADLESS_SEM:
                result = subprocess.run(args, capture_output=True, text=True, timeout=240)
            combined = (result.stdout or "") + "\n" + (result.stderr or "")
            for line in combined.splitlines():
                idx = line.find("===RESULT===")
                if idx < 0:
                    continue
                payload = line[idx + len("===RESULT===") :].strip()
                if payload.endswith("(GhidraScript)"):
                    payload = payload[: -len("(GhidraScript)")].strip()
                res = json.loads(payload)
                if isinstance(res, dict) and "error" in res:
                    raise HTTPException(status_code=500, detail=res["error"])
                _IMPORTED_PROJECTS.add(project_name)
                return res

    raise HTTPException(
        status_code=500,
        detail=f"Headless script failed: {(result.stderr or result.stdout or '')[-1500:]}",
    )


def run_export_parity(binary_path: str, mode: str, addr: str = ""):
    binary_path = _resolve_binary(binary_path)
    fp = _binary_fingerprint(binary_path)
    cache_key = (fp, binary_path, mode, addr or "")
    with _PARITY_CACHE_LOCK:
        if cache_key in _PARITY_CACHE:
            return _PARITY_CACHE[cache_key]
        # Prefer filling from a cached bundle when asking for a single mode.
        if mode in {"disasm", "pcode", "cfg"} and addr:
            bundle = _PARITY_CACHE.get((fp, binary_path, "bundle", addr))
            if isinstance(bundle, dict) and mode in bundle:
                cached_mode = bundle[mode]
            else:
                cached_mode = None
        else:
            cached_mode = None
    if cached_mode is not None:
        _cache_put(cache_key, cached_mode)
        return cached_mode

    res = _run_headless_parity(binary_path, mode, addr)
    _cache_put(cache_key, res)

    # If we ran a bundle, also populate per-mode cache entries.
    if mode == "bundle" and isinstance(res, dict):
        for sub in ("disasm", "pcode", "cfg"):
            if sub in res:
                _cache_put((fp, binary_path, sub, addr or ""), res[sub])
    return res


def _disasm_to_decode(disasm_data: object) -> list:
    res = []
    if not isinstance(disasm_data, list):
        return res
    for inst in disasm_data:
        if not isinstance(inst, dict):
            continue
        b = inst.get("bytes", "")
        res.append({
            "address": inst.get("address"),
            "bytes": b,
            "length": inst.get("length", len(str(b).replace(" ", "")) // 2),
            "mnemonic": inst.get("mnemonic", ""),
            "prefixes": [],
            "modrm": None,
            "sib": None,
            "displacement": None,
            "immediate": None,
        })
    return res


@app.get("/health")
def health():
    with _PARITY_CACHE_LOCK:
        cache_entries = len(_PARITY_CACHE)
    return {
        "status": "ok",
        "decompiler": "ghidra",
        "version": "12.0",
        "parity": {
            "project_cache": str(PROJECT_CACHE),
            "project_cache_exists": PROJECT_CACHE.is_dir(),
            "memory_cache_entries": cache_entries,
            "bundle_endpoint": "/parity_bundle",
            "headless_workers": _HEADLESS_WORKERS,
            "cache_key": "path+content_fingerprint",
            "address_resolution": "direct_then_image_base_relative",
        },
        "pyghidra": {
            "available": _PYGHIDRA_AVAILABLE,
            "ready": _pyghidra_ready,
            "fast_path_active": _PYGHIDRA_AVAILABLE and _pyghidra_ready,
            "error": _pyghidra_error,
        },
    }


@app.get("/functions")
def functions(binary: str):
    return run_export_parity(binary, "functions")


@app.get("/metadata")
def metadata(binary: str):
    return run_export_parity(binary, "metadata")


@app.get("/disasm")
def disasm(binary: str, addr: str):
    validate_address(addr)
    return run_export_parity(binary, "disasm", addr)


@app.get("/decode")
def decode(binary: str, addr: str):
    validate_address(addr)
    disasm_data = run_export_parity(binary, "disasm", addr)
    return _disasm_to_decode(disasm_data)


@app.get("/pcode")
def pcode(binary: str, addr: str):
    validate_address(addr)
    return run_export_parity(binary, "pcode", addr)


@app.get("/cfg")
def cfg(binary: str, addr: str):
    validate_address(addr)
    return run_export_parity(binary, "cfg", addr)


@app.get("/abi")
def abi(binary: str, addr: str):
    """Calling-convention / parameter storage export via ExportParity."""
    validate_address(addr)
    return run_export_parity(binary, "abi", addr)


@app.get("/types")
def types(binary: str, addr: str):
    validate_address(addr)
    return run_export_parity(binary, "types", addr)


@app.get("/callgraph")
def callgraph(binary: str, addr: str):
    validate_address(addr)
    return run_export_parity(binary, "callgraph", addr)


@app.get("/strings")
def strings_export(binary: str, addr: str):
    validate_address(addr)
    return run_export_parity(binary, "strings", addr)


@app.get("/dataflow")
def dataflow(binary: str, addr: str):
    validate_address(addr)
    return run_export_parity(binary, "dataflow", addr)


@app.get("/seh")
def seh(binary: str, addr: str):
    validate_address(addr)
    return run_export_parity(binary, "seh", addr)


@app.get("/parity_bundle")
def parity_bundle(binary: str, addr: str):
    """One headless invocation → disasm + pcode + cfg (decode derived)."""
    validate_address(addr)
    start = time.monotonic()
    bundle = run_export_parity(binary, "bundle", addr)
    if not isinstance(bundle, dict):
        raise HTTPException(status_code=500, detail="bundle response is not an object")
    # Ensure decode is present for clients that want all four.
    if "disasm" in bundle and "decode" not in bundle:
        bundle = dict(bundle)
        bundle["decode"] = _disasm_to_decode(bundle.get("disasm"))
    bundle["time_ms"] = int((time.monotonic() - start) * 1000)
    return bundle


def _normalize_addr_key(addr: str) -> str:
    text = addr.strip().lower()
    if text.startswith("0x"):
        return f"0x{int(text, 16):x}"
    try:
        return f"0x{int(text, 16):x}"
    except ValueError:
        return text


@app.get("/parity_multi_bundle")
def parity_multi_bundle(binary: str, addrs: str):
    """One headless invocation for many function addresses in the same binary.

    Query: addrs=0x140001530,0x14000155f,0x14000158c
    Response: { "by_addr": { "0x...": { disasm, pcode, cfg, decode }, ... }, "time_ms": N }
    """
    start = time.monotonic()
    raw_list = [a.strip() for a in addrs.split(",") if a.strip()]
    if not raw_list:
        raise HTTPException(status_code=400, detail="addrs must be a non-empty comma list")
    for a in raw_list:
        validate_address(a)

    # Memory cache: reuse any addresses already bundled for this content fingerprint.
    binary_path = _resolve_binary(binary)
    fp = _binary_fingerprint(binary_path)
    by_addr: dict[str, object] = {}
    missing: list[str] = []
    for a in raw_list:
        key = _normalize_addr_key(a)
        with _PARITY_CACHE_LOCK:
            cached = _PARITY_CACHE.get((fp, binary_path, "bundle", key))
        if isinstance(cached, dict) and "disasm" in cached:
            item = dict(cached)
            if "decode" not in item:
                item["decode"] = _disasm_to_decode(item.get("disasm"))
            by_addr[key] = item
        else:
            missing.append(a)

    if missing:
        joined = ",".join(missing)
        multi = run_export_parity(binary, "multi_bundle", joined)
        if not isinstance(multi, dict) or not isinstance(multi.get("by_addr"), dict):
            raise HTTPException(status_code=500, detail="multi_bundle response invalid")
        for k, v in multi["by_addr"].items():
            nk = _normalize_addr_key(str(k))
            if isinstance(v, dict) and "error" not in v:
                if "decode" not in v and "disasm" in v:
                    v = dict(v)
                    v["decode"] = _disasm_to_decode(v.get("disasm"))
                _cache_put((fp, binary_path, "bundle", nk), v)
                for sub in ("disasm", "pcode", "cfg"):
                    if sub in v:
                        _cache_put((fp, binary_path, sub, nk), v[sub])
            by_addr[nk] = v

    return {
        "schema": "ghidra-parity-multi-bundle-v1",
        "by_addr": by_addr,
        "time_ms": int((time.monotonic() - start) * 1000),
        "requested": len(raw_list),
        "fetched_via_headless": len(missing),
        "binary_fingerprint": fp,
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
        return DecompileResponse(name=item.name, code=item.code, time_ms=elapsed)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _content_project_key(binary_bytes: bytes) -> str:
    """Stable project id for HTTP batch decompile (b64 payload, no corpus path)."""
    return hashlib.sha256(binary_bytes).hexdigest()[:20]


def _run_ghidra_headless(binary_bytes: bytes, addresses: List[str]) -> List[DecompileResultItem]:
    """Decompile many addresses with persistent project cache (parity-style).

    Previously each batch used a throwaway project + ``-deleteProject``, so every
    PE paid full import/analysis cost again. Reuse ``PROJECT_CACHE`` keyed by
    content hash: first call imports, later calls ``-process`` + multi-addr script.
    """
    project_name = f"dec_{_content_project_key(binary_bytes)}"
    # Materialize bytes under the cache root so re-import paths stay stable.
    # Program name inside Ghidra matches the imported file basename.
    blob_dir = PROJECT_CACHE / "blobs"
    blob_dir.mkdir(parents=True, exist_ok=True)
    binary_path = blob_dir / f"{project_name}.bin"
    program_name = binary_path.name
    if not binary_path.is_file() or binary_path.stat().st_size != len(binary_bytes):
        binary_path.write_bytes(binary_bytes)

    script_log = PROJECT_CACHE / f"{project_name}.script.log"
    exists = _project_exists(project_name) or project_name in _IMPORTED_PROJECTS

    if exists:
        args = [
            str(GHIDRA_HEADLESS),
            str(PROJECT_CACHE),
            project_name,
            "-process",
            program_name,
            "-noanalysis",
            "-scriptPath",
            str(SCRIPT_DIR),
            "-postScript",
            "DecompileFunction.java",
            *addresses,
            "-scriptlog",
            str(script_log),
        ]
    else:
        args = [
            str(GHIDRA_HEADLESS),
            str(PROJECT_CACHE),
            project_name,
            "-import",
            str(binary_path),
            "-overwrite",
            "-scriptPath",
            str(SCRIPT_DIR),
            "-postScript",
            "DecompileFunction.java",
            *addresses,
            "-scriptlog",
            str(script_log),
        ]

    with _project_lock(project_name):
        with _HEADLESS_SEM:
            result = subprocess.run(args, capture_output=True, text=True, timeout=300)
        if result.returncode == 0 or _project_exists(project_name):
            _IMPORTED_PROJECTS.add(project_name)

    parse_sources = [result.stdout, result.stderr]
    if script_log.exists():
        parse_sources.append(script_log.read_text(errors="replace"))

    for source in parse_sources:
        res_list = None
        try:
            res_list = _extract_marked_json_line(source, BATCH_MARKER)
        except Exception:
            pass
        if res_list is not None:
            items = []
            for item in res_list:
                items.append(
                    DecompileResultItem(
                        addr=item.get("addr") or item.get("address"),
                        name=item.get("name", "?"),
                        code=item.get("code", ""),
                        error=item.get("error"),
                    )
                )
            return items

    raise RuntimeError(
        f"Ghidra script failed or marker not found. Exit code {result.returncode}"
    )


@app.post("/decompile_batch", response_model=BatchDecompileResponse)
def decompile_batch(req: BatchDecompileRequest):
    try:
        binary_bytes = base64.b64decode(req.binary_b64, validate=True)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 payload")

    start = time.monotonic()
    try:
        results = _run_ghidra_headless(binary_bytes, req.addresses)
    except Exception:
        results = []
        for addr in req.addresses:
            try:
                single_results = _run_ghidra_headless(binary_bytes, [addr])
                if single_results:
                    results.append(single_results[0])
                else:
                    results.append(DecompileResultItem(addr=addr, error="Empty result returned"))
            except Exception as se:
                results.append(
                    DecompileResultItem(addr=addr, error=f"Headless script failed: {str(se)}")
                )

    elapsed = int((time.monotonic() - start) * 1000)
    return BatchDecompileResponse(results=results, time_ms=elapsed)
