"""Dedicated decompile speed micro-benchmark (cold vs warm).

Runs N timed ``/decompile_batch`` requests against the same binary+addresses
for each decompiler. Does **not** run semantic/oracle and does **not** write
ranking envelopes.

Usage:
  python -m runner.speed_microbench \\
    --endpoint fission=http://localhost:8000 \\
    --endpoint ghidra=http://localhost:8001 \\
    --binary corpus/dev/binaries/c/small_gcc_O0.exe \\
    --addr 0x140001000 --addr 0x140001050 \\
    --trials 5 \\
    --output results/speed/microbench_latest.json

Env:
  SPEED_TRIALS, SPEED_WARMUP (discarded untimed warmups before cold, default 0)
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import json
import os
import re
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx

try:
    from .speed_summary import SPEED_SCHEMA, timing_stats
except ImportError:
    from speed_summary import SPEED_SCHEMA, timing_stats  # type: ignore

ROOT = Path(__file__).resolve().parent.parent
_VERSION_RE = re.compile(r"^v?\d+\.\d+\.\d+$")

_BYTE_UNITS = {
    "b": 1,
    "kb": 1_000,
    "kib": 1_024,
    "mb": 1_000_000,
    "mib": 1_048_576,
    "gb": 1_000_000_000,
    "gib": 1_073_741_824,
    "tb": 1_000_000_000_000,
    "tib": 1_099_511_627_776,
}


def _parse_endpoint(spec: str) -> tuple[str, str]:
    if "=" not in spec:
        raise argparse.ArgumentTypeError(
            f"endpoint must be name=url, got {spec!r}"
        )
    name, url = spec.split("=", 1)
    name, url = name.strip(), url.strip().rstrip("/")
    if not name or not url:
        raise argparse.ArgumentTypeError(f"bad endpoint {spec!r}")
    return name, url


def _parse_named_value(spec: str, *, label: str) -> tuple[str, str]:
    if "=" not in spec:
        raise argparse.ArgumentTypeError(f"{label} must be name=value, got {spec!r}")
    name, value = (part.strip() for part in spec.split("=", 1))
    if not name or not value:
        raise argparse.ArgumentTypeError(f"bad {label} {spec!r}")
    return name, value


def _archive_release_snapshot(doc: dict[str, Any], history_dir: Path) -> str | None:
    """Persist version-keyed resource telemetry for release trend charts."""
    version = str((doc.get("toolchain") or {}).get("fission_version") or "")
    if not _VERSION_RE.fullmatch(version):
        return None
    history_dir.mkdir(parents=True, exist_ok=True)
    (history_dir / f"{version}.json").write_text(
        json.dumps(doc, indent=2) + "\n",
        encoding="utf-8",
    )
    versions = {
        path.stem
        for path in history_dir.glob("v*.json")
        if path.stem != "index"
    }
    ordered = sorted(
        versions,
        key=lambda value: tuple(
            int(part) for part in value.removeprefix("v").split(".")
        ),
    )
    (history_dir / "index.json").write_text(
        json.dumps(ordered, indent=2) + "\n",
        encoding="utf-8",
    )
    return version


def _parse_percent(value: object) -> float | None:
    try:
        return float(str(value).strip().removesuffix("%"))
    except (TypeError, ValueError):
        return None


def _parse_bytes(value: object) -> int | None:
    match = re.fullmatch(r"\s*([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z]+)\s*", str(value))
    if not match:
        return None
    multiplier = _BYTE_UNITS.get(match.group(2).lower())
    if multiplier is None:
        return None
    return round(float(match.group(1)) * multiplier)


def _parse_docker_stats(payload: str) -> dict[str, float | int] | None:
    # Docker Desktop may wrap formatted output in terminal clear-line escape
    # sequences even when stdout is piped. Decode only the JSON object.
    start, end = payload.find("{"), payload.rfind("}")
    if start < 0 or end < start:
        return None
    try:
        raw = json.loads(payload[start : end + 1])
    except json.JSONDecodeError:
        return None
    cpu = _parse_percent(raw.get("CPUPerc"))
    memory_percent = _parse_percent(raw.get("MemPerc"))
    memory_usage = str(raw.get("MemUsage") or "").split("/", 1)[0].strip()
    memory_bytes = _parse_bytes(memory_usage)
    if cpu is None and memory_bytes is None:
        return None
    sample: dict[str, float | int] = {"captured_at_ms": round(time.time() * 1000)}
    if cpu is not None:
        sample["cpu_percent"] = cpu
    if memory_bytes is not None:
        sample["memory_bytes"] = memory_bytes
    if memory_percent is not None:
        sample["memory_percent"] = memory_percent
    try:
        sample["pids"] = int(raw.get("PIDs"))
    except (TypeError, ValueError):
        pass
    return sample


def _resource_summary(samples: list[dict[str, float | int]]) -> dict[str, Any]:
    cpu = [float(s["cpu_percent"]) for s in samples if "cpu_percent" in s]
    memory = [int(s["memory_bytes"]) for s in samples if "memory_bytes" in s]
    memory_percent = [
        float(s["memory_percent"]) for s in samples if "memory_percent" in s
    ]
    pids = [int(s["pids"]) for s in samples if "pids" in s]
    return {
        "available": bool(samples),
        "collector": "docker_stats",
        "scope": "container_cgroup",
        "samples": len(samples),
        "mean_cpu_percent": round(sum(cpu) / len(cpu), 3) if cpu else None,
        "peak_cpu_percent": round(max(cpu), 3) if cpu else None,
        "mean_memory_bytes": round(sum(memory) / len(memory)) if memory else None,
        "peak_memory_bytes": max(memory) if memory else None,
        "mean_memory_percent": (
            round(sum(memory_percent) / len(memory_percent), 3)
            if memory_percent
            else None
        ),
        "peak_memory_percent": round(max(memory_percent), 3) if memory_percent else None,
        "peak_pids": max(pids) if pids else None,
    }


class DockerStatsSampler:
    """Collect Docker cgroup samples concurrently with one timed request."""

    def __init__(self, container: str):
        self.container = container
        self.samples: list[dict[str, float | int]] = []
        self.process: asyncio.subprocess.Process | None = None
        self.task: asyncio.Task[None] | None = None
        self.first_sample = asyncio.Event()
        self.error: str | None = None

    async def start(self) -> None:
        try:
            self.process = await asyncio.create_subprocess_exec(
                "docker",
                "stats",
                "--format",
                "{{json .}}",
                self.container,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            self.task = asyncio.create_task(self._read())
            # Give Docker a chance to establish its first sampling interval
            # before the adapter request starts; this is outside wall_ms.
            await asyncio.sleep(0.05)
        except (OSError, RuntimeError) as exc:
            self.error = str(exc)

    async def _read(self) -> None:
        assert self.process and self.process.stdout
        while True:
            line = await self.process.stdout.readline()
            if not line:
                break
            sample = _parse_docker_stats(line.decode("utf-8", errors="replace"))
            if sample:
                self.samples.append(sample)
                self.first_sample.set()

    async def finish(self) -> dict[str, Any]:
        if self.process is None:
            return {**_resource_summary([]), "container": self.container, "error": self.error}
        if not self.samples:
            try:
                await asyncio.wait_for(self.first_sample.wait(), timeout=1.5)
            except TimeoutError:
                pass
        if self.process.returncode is None:
            try:
                self.process.terminate()
            except ProcessLookupError:
                pass
        try:
            await asyncio.wait_for(self.process.wait(), timeout=1.0)
        except TimeoutError:
            self.process.kill()
            await self.process.wait()
        if self.task:
            await self.task
        summary = _resource_summary(self.samples)
        summary["container"] = self.container
        if not self.samples and self.process.stderr:
            stderr = (await self.process.stderr.read()).decode("utf-8", errors="replace").strip()
            if stderr:
                summary["error"] = stderr[:300]
        return summary


async def _one_batch(
    client: httpx.AsyncClient,
    url: str,
    binary_b64: str,
    addresses: list[str],
    timeout: float,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    try:
        resp = await client.post(
            f"{url}/decompile_batch",
            json={"binary_b64": binary_b64, "addresses": addresses},
            timeout=timeout,
        )
        wall_ms = (time.perf_counter() - t0) * 1000.0
        if resp.status_code != 200:
            return {
                "ok": False,
                "wall_ms": wall_ms,
                "adapter_ms": None,
                "error": f"HTTP {resp.status_code}: {resp.text[:300]}",
            }
        data = resp.json()
        adapter_ms = data.get("time_ms")
        results = data.get("results") or []
        errs = [r.get("error") for r in results if isinstance(r, dict) and r.get("error")]
        return {
            "ok": not errs and adapter_ms is not None,
            "wall_ms": wall_ms,
            "adapter_ms": float(adapter_ms) if adapter_ms is not None else None,
            "n_results": len(results),
            "errors": errs[:5],
            "error": errs[0] if errs else None,
        }
    except Exception as exc:  # noqa: BLE001
        wall_ms = (time.perf_counter() - t0) * 1000.0
        return {
            "ok": False,
            "wall_ms": wall_ms,
            "adapter_ms": None,
            "error": str(exc),
        }


async def run_subject(
    client: httpx.AsyncClient,
    *,
    decompiler: str,
    url: str,
    binary_path: Path,
    addresses: list[str],
    trials: int,
    warmup: int,
    timeout: float,
    container: str | None = None,
) -> dict[str, Any]:
    binary_b64 = base64.b64encode(binary_path.read_bytes()).decode()
    # Untimed warmups (optional) — discarded so "cold" is first measured trial.
    for _ in range(max(0, warmup)):
        await _one_batch(client, url, binary_b64, addresses, timeout)

    trials_out: list[dict[str, Any]] = []
    for i in range(trials):
        # Brief gap reduces pathological connection reuse bias without
        # restarting containers (true process-cold needs image restart).
        if i > 0:
            await asyncio.sleep(0.05)
        sampler = DockerStatsSampler(container) if container else None
        if sampler:
            await sampler.start()
        r = await _one_batch(client, url, binary_b64, addresses, timeout)
        resources = await sampler.finish() if sampler else None
        phase = "cold" if i == 0 else "warm"
        trial = {
            "trial": i,
            "phase": phase,
            "ok": r["ok"],
            "wall_ms": round(float(r["wall_ms"]), 3),
            "adapter_ms": round(float(r["adapter_ms"]), 3)
            if r.get("adapter_ms") is not None
            else None,
            "error": r.get("error"),
        }
        if resources is not None:
            trial["resources"] = resources
        trials_out.append(trial)

    cold = [t for t in trials_out if t["phase"] == "cold" and t.get("adapter_ms")]
    warm = [t for t in trials_out if t["phase"] == "warm" and t.get("adapter_ms")]
    return {
        "decompiler": decompiler,
        "binary": str(binary_path),
        "addresses": addresses,
        "resource_container": container,
        "trials": trials_out,
        "cold": timing_stats(t["adapter_ms"] for t in cold if t["adapter_ms"] is not None),
        "warm": timing_stats(t["adapter_ms"] for t in warm if t["adapter_ms"] is not None),
        "all": timing_stats(
            t["adapter_ms"] for t in trials_out if t.get("adapter_ms") is not None
        ),
    }


def _summarize_by_decompiler(subjects: list[dict[str, Any]]) -> dict[str, Any]:
    by: dict[str, dict[str, list[float]]] = {}
    for subj in subjects:
        d = subj["decompiler"]
        by.setdefault(d, {"cold": [], "warm": [], "all": []})
        for trial in subj.get("trials") or []:
            ms = trial.get("adapter_ms")
            if not isinstance(ms, (int, float)) or ms <= 0:
                continue
            by[d]["all"].append(float(ms))
            if trial.get("phase") == "cold":
                by[d]["cold"].append(float(ms))
            else:
                by[d]["warm"].append(float(ms))
    result = {
        name: {
            "cold": timing_stats(v["cold"]),
            "warm": timing_stats(v["warm"]),
            "all": timing_stats(v["all"]),
        }
        for name, v in sorted(by.items())
    }
    for name, summary in result.items():
        trials = [
            trial
            for subject in subjects
            if subject.get("decompiler") == name
            for trial in (subject.get("trials") or [])
        ]
        summary["resources"] = {
            "collector": "docker_stats",
            "scope": "container_cgroup",
            "cold": _summarize_resource_trials(
                [trial for trial in trials if trial.get("phase") == "cold"]
            ),
            "warm": _summarize_resource_trials(
                [trial for trial in trials if trial.get("phase") == "warm"]
            ),
            "all": _summarize_resource_trials(trials),
        }
    return result


def _summarize_resource_trials(trials: list[dict[str, Any]]) -> dict[str, Any]:
    resources = [
        trial["resources"]
        for trial in trials
        if isinstance(trial.get("resources"), dict)
        and trial["resources"].get("available")
    ]
    cpu_means = [
        float(item["mean_cpu_percent"])
        for item in resources
        if isinstance(item.get("mean_cpu_percent"), (int, float))
    ]
    cpu_peaks = [
        float(item["peak_cpu_percent"])
        for item in resources
        if isinstance(item.get("peak_cpu_percent"), (int, float))
    ]
    memory_peaks = [
        int(item["peak_memory_bytes"])
        for item in resources
        if isinstance(item.get("peak_memory_bytes"), (int, float))
    ]
    memory_percent_peaks = [
        float(item["peak_memory_percent"])
        for item in resources
        if isinstance(item.get("peak_memory_percent"), (int, float))
    ]
    return {
        "n_trials": len(resources),
        "samples": sum(int(item.get("samples") or 0) for item in resources),
        "mean_cpu_percent": (
            round(sum(cpu_means) / len(cpu_means), 3) if cpu_means else None
        ),
        "peak_cpu_percent": round(max(cpu_peaks), 3) if cpu_peaks else None,
        "mean_peak_memory_bytes": (
            round(sum(memory_peaks) / len(memory_peaks)) if memory_peaks else None
        ),
        "peak_memory_bytes": max(memory_peaks) if memory_peaks else None,
        "peak_memory_percent": (
            round(max(memory_percent_peaks), 3) if memory_percent_peaks else None
        ),
    }


async def _amain(args: argparse.Namespace) -> int:
    endpoints = dict(args.endpoint)
    containers = dict(args.container)
    if not endpoints:
        print("FAIL: pass at least one --endpoint name=url", file=sys.stderr)
        return 2
    if not args.binary:
        print("FAIL: pass at least one --binary", file=sys.stderr)
        return 2
    if not args.addr:
        print("FAIL: pass at least one --addr", file=sys.stderr)
        return 2

    binaries = [Path(b) for b in args.binary]
    for b in binaries:
        if not b.is_file():
            print(f"FAIL missing binary: {b}", file=sys.stderr)
            return 2

    trials = max(1, int(args.trials))
    warmup = max(0, int(args.warmup))
    timeout = float(args.timeout)
    addresses = [a.strip() for a in args.addr if a.strip()]

    started = datetime.now(timezone.utc)
    subjects: list[dict[str, Any]] = []

    async with httpx.AsyncClient() as client:
        for binary_path in binaries:
            for dname, url in endpoints.items():
                print(
                    f"==> {dname} {binary_path.name} "
                    f"addrs={len(addresses)} trials={trials} warmup={warmup}",
                    flush=True,
                )
                # Health check (best-effort)
                try:
                    h = await client.get(f"{url}/health", timeout=10.0)
                    if h.status_code != 200:
                        print(f"WARN {dname} health HTTP {h.status_code}", flush=True)
                except Exception as exc:  # noqa: BLE001
                    print(f"WARN {dname} health: {exc}", flush=True)

                subj = await run_subject(
                    client,
                    decompiler=dname,
                    url=url,
                    binary_path=binary_path,
                    addresses=addresses,
                    trials=trials,
                    warmup=warmup,
                    timeout=timeout,
                    container=containers.get(dname),
                )
                subjects.append(subj)
                c = subj["cold"]
                w = subj["warm"]
                print(
                    f"    cold mean={c.get('mean_ms')}ms n={c.get('n')} · "
                    f"warm mean={w.get('mean_ms')}ms n={w.get('n')}",
                    flush=True,
                )

    finished = datetime.now(timezone.utc)
    doc: dict[str, Any] = {
        "schema": "speed-microbench-v2",
        "run_id": str(uuid.uuid4()),
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "duration_ms": int((finished - started).total_seconds() * 1000),
        "toolchain": {
            "fission_version": os.environ.get("FISSION_VERSION"),
            "runner_commit": os.environ.get("GITHUB_SHA")
            or os.environ.get("BENCHMARK_COMMIT"),
            "github_run_id": os.environ.get("GITHUB_RUN_ID"),
        },
        "config": {
            "trials": trials,
            "warmup": warmup,
            "timeout_s": timeout,
            "addresses": addresses,
            "binaries": [str(b) for b in binaries],
            "decompilers": list(endpoints.keys()),
            "resource_containers": containers,
            "resource_scope": "docker_container_cgroup" if containers else None,
            "ranking": False,
        },
        "notes": (
            "cold = first timed /decompile_batch after optional discarded warmups; "
            "warm = trials 2..N on the same process (no container restart). "
            "adapter_ms prefers server-reported time_ms; wall_ms is client RTT. "
            "When --container is set, CPU and memory are sampled concurrently from "
            "Docker container cgroups. CPU may exceed 100% on multicore hosts; peak "
            "memory is the maximum observed sample, not an OS high-water mark."
        ),
        "subjects": subjects,
        "by_decompiler": _summarize_by_decompiler(subjects),
        "extensions_schema": SPEED_SCHEMA,
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(doc, indent=2) + "\n"
    out.write_text(payload, encoding="utf-8")
    print(f"Wrote {out}", flush=True)
    if args.dashboard_copy:
        dashboard_copy = Path(args.dashboard_copy)
        dashboard_copy.parent.mkdir(parents=True, exist_ok=True)
        dashboard_copy.write_text(payload, encoding="utf-8")
        print(f"Dashboard copy: {dashboard_copy}", flush=True)
    if args.history_dir:
        archived = _archive_release_snapshot(doc, Path(args.history_dir))
        if archived:
            print(f"Release speed history: {archived}", flush=True)
        else:
            print("Release speed history skipped: no semantic Fission version", flush=True)

    # Soft gate for CI smoke: require at least one ok cold trial per decompiler.
    fail = 0
    for dname in endpoints:
        subs = [s for s in subjects if s["decompiler"] == dname]
        ok_cold = any(
            t.get("ok") and t.get("phase") == "cold"
            for s in subs
            for t in (s.get("trials") or [])
        )
        if not ok_cold:
            print(f"FAIL {dname}: no successful cold trial", file=sys.stderr)
            fail = 1
    return fail


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--endpoint",
        action="append",
        type=_parse_endpoint,
        default=[],
        help="name=url (repeatable), e.g. fission=http://localhost:8000",
    )
    p.add_argument(
        "--container",
        action="append",
        type=lambda value: _parse_named_value(value, label="container"),
        default=[],
        help=(
            "name=container-id-or-name (repeatable). Enables concurrent Docker "
            "CPU/memory sampling for the matching --endpoint."
        ),
    )
    p.add_argument(
        "--binary",
        action="append",
        default=[],
        help="Path to PE/ELF binary (repeatable)",
    )
    p.add_argument(
        "--addr",
        action="append",
        default=[],
        help="Function entry address hex (repeatable)",
    )
    p.add_argument(
        "--trials",
        type=int,
        default=int(os.environ.get("SPEED_TRIALS", "5")),
        help="Timed trials per decompiler×binary (default 5; trial0=cold)",
    )
    p.add_argument(
        "--warmup",
        type=int,
        default=int(os.environ.get("SPEED_WARMUP", "0")),
        help="Untimed requests before cold trial (default 0)",
    )
    p.add_argument(
        "--timeout",
        type=float,
        default=float(os.environ.get("SPEED_TIMEOUT", "120")),
        help="HTTP timeout seconds per batch (default 120)",
    )
    p.add_argument(
        "--output",
        type=str,
        default=str(ROOT / "results" / "speed" / "microbench_latest.json"),
        help="Output JSON path",
    )
    p.add_argument(
        "--dashboard-copy",
        type=str,
        default=str(ROOT / "public" / "speed-microbench-latest.json"),
        help="Static dashboard JSON copy (empty string disables)",
    )
    p.add_argument(
        "--history-dir",
        type=str,
        default=str(ROOT / "public" / "speed-history"),
        help="Version-keyed dashboard history directory (empty string disables)",
    )
    args = p.parse_args(argv)
    return asyncio.run(_amain(args))


if __name__ == "__main__":
    raise SystemExit(main())
