#!/usr/bin/env python3
"""Materialize a pinned DecBench dataset config as a Fission scale corpus.

The importer downloads only ground-truth binaries and published source CFGs.
It does not import other decompilers' outputs, and it never executes a corpus
binary. Generated artifacts live under corpus/scale and are gitignored;
dataset-lock.json is the committed provenance and count contract.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = ROOT / "corpus" / "scale"
LOCK_PATH = CORPUS_DIR / "dataset-lock.json"
sys.path.insert(0, str(ROOT))

from runner.type_match import detect, dwarf_info  # noqa: E402

MALWARE_PROJECTS = frozenset({"dexter", "minipig", "mirai", "mydoom", "x0r-usb"})


def _load_lock(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    required = ("dataset_repo", "revision", "license", "configs")
    missing = [name for name in required if not data.get(name)]
    if missing:
        raise ValueError(f"{path}: missing lock fields {missing}")
    return data


def _safe_component(value: object, field: str) -> str:
    text = str(value or "")
    if (
        not text
        or text in {".", ".."}
        or "/" in text
        or "\\" in text
        or "\x00" in text
    ):
        raise ValueError(f"unsafe {field}: {text!r}")
    return text


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _url(repo: str, revision: str, relative: str) -> str:
    encoded = urllib.parse.quote(relative, safe="/")
    return f"https://huggingface.co/datasets/{repo}/resolve/{revision}/{encoded}"


def _download(
    *,
    repo: str,
    revision: str,
    relative: str,
    destination: Path,
    expected_sha256: str | None = None,
    retries: int = 4,
) -> dict[str, Any]:
    if destination.is_file():
        actual = _sha256(destination)
        if expected_sha256 is None or actual == expected_sha256:
            return {"path": str(destination), "sha256": actual, "cached": True}

    destination.parent.mkdir(parents=True, exist_ok=True)
    part = destination.with_name(destination.name + ".part")
    request = urllib.request.Request(
        _url(repo, revision, relative),
        headers={"User-Agent": "fission-benchmark-scale-import/1"},
    )
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                with part.open("wb") as output:
                    while chunk := response.read(1024 * 1024):
                        output.write(chunk)
            actual = _sha256(part)
            if expected_sha256 and actual != expected_sha256:
                raise ValueError(
                    f"{relative}: sha256 {actual} != expected {expected_sha256}"
                )
            os.replace(part, destination)
            return {"path": str(destination), "sha256": actual, "cached": False}
        except (OSError, urllib.error.URLError, ValueError) as exc:
            last_error = exc
            part.unlink(missing_ok=True)
            if attempt + 1 < retries:
                time.sleep(2**attempt)
    raise RuntimeError(f"download failed for {relative}: {last_error}")


def _die_attribute(die: Any, name: str) -> Any | None:
    pending = [die]
    seen: set[int] = set()
    while pending:
        current = pending.pop()
        offset = int(getattr(current, "offset", id(current)))
        if offset in seen:
            continue
        seen.add(offset)
        attribute = current.attributes.get(name)
        if attribute is not None:
            return attribute
        for reference in ("DW_AT_abstract_origin", "DW_AT_specification"):
            if reference not in current.attributes:
                continue
            try:
                target = current.get_DIE_from_attribute(reference)
            except Exception:
                target = None
            if target is not None:
                pending.append(target)
    return None


def _decode_name(value: object) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return str(value or "")


def _dwarf_addresses(binary: Path, wanted: set[str]) -> dict[str, int]:
    dwarf = dwarf_info(binary)
    if dwarf is None:
        return {}
    addresses: dict[str, int] = {}
    for cu in dwarf.iter_CUs():
        for die in cu.iter_DIEs():
            if die.tag != "DW_TAG_subprogram":
                continue
            low_pc = _die_attribute(die, "DW_AT_low_pc")
            name_attr = _die_attribute(die, "DW_AT_name")
            if low_pc is None or name_attr is None:
                continue
            name = _decode_name(name_attr.value)
            if name not in wanted:
                continue
            address = int(low_pc.value)
            if address > 0:
                addresses[name] = min(addresses.get(name, address), address)
    return addresses


def _isa_format(binary: Path) -> tuple[str, str, str]:
    info = detect(binary)
    if info is None:
        raise ValueError(f"unsupported binary format: {binary}")
    isa = {
        "x86-64": "x86_64",
        "x86": "x86_32",
        "arm": "arm",
        "aarch64": "aarch64",
        "riscv": "riscv",
    }.get(info.arch, info.arch)
    abi = f"{'linux' if info.fmt == 'elf' else 'windows'}-{isa}"
    return isa, info.fmt, abi


def _variant_opt(opt: str) -> str:
    return {"O0": "-O0", "O2": "-O2", "O2-noinline": "-O2-noinline"}.get(
        opt, f"-{opt}"
    )


def _manifest_name(opt: str, project: str, stem: str) -> str:
    readable = re.sub(r"[^A-Za-z0-9._-]+", "_", f"{opt}__{project}__{stem}")[:120]
    suffix = hashlib.sha256(f"{opt}\0{project}\0{stem}".encode()).hexdigest()[:10]
    return f"{readable}__{suffix}.json"


def _materialize_group(
    group: dict[str, Any],
    *,
    repo: str,
    revision: str,
    corpus_dir: Path,
) -> dict[str, Any]:
    project = _safe_component(group.get("project"), "project")
    opt = _safe_component(group.get("opt"), "opt")
    stem = _safe_component(group.get("binary"), "binary stem")
    binary_rel = Path(str(group["binary_path"]))
    binary_name = _safe_component(binary_rel.name, "binary filename")
    local_binary = corpus_dir / "binaries" / opt / project / binary_name
    _download(
        repo=repo,
        revision=revision,
        relative=binary_rel.as_posix(),
        destination=local_binary,
        expected_sha256=str(group.get("sha256") or "") or None,
    )

    source_cfg_remote = str(group.get("source_cfg_path") or "")
    local_cfg_rel = Path("source_cfgs") / opt / project / f"{stem}.json"
    if source_cfg_remote:
        _download(
            repo=repo,
            revision=revision,
            relative=source_cfg_remote,
            destination=corpus_dir / local_cfg_rel,
        )

    cfg_symbols: set[str] = set()
    if source_cfg_remote:
        cfg_payload = json.loads((corpus_dir / local_cfg_rel).read_text(encoding="utf-8"))
        cfg_functions = cfg_payload.get("functions") if isinstance(cfg_payload, dict) else None
        if not isinstance(cfg_functions, dict):
            raise ValueError(f"invalid published source CFG: {corpus_dir / local_cfg_rel}")
        cfg_symbols = {str(name) for name in cfg_functions}

    wanted = {str(name) for name in group.get("functions") or [] if name}
    addresses = _dwarf_addresses(local_binary, wanted)
    isa, fmt, abi = _isa_format(local_binary)
    functions = []
    for symbol in sorted(wanted & set(addresses)):
        subject_id = f"decbench::{project}::{stem}::{symbol}"
        functions.append(
            {
                "name": symbol,
                "subject_id": subject_id,
                "project": project,
                "language": "c",
                "source": f"sources/{project}",
                "semantic": {
                    "mode": "none",
                    "oracle": "unavailable_external_dataset",
                    "ranking": False,
                },
                "compiler_variants": [
                    {
                        "compiler": "gcc",
                        "opt": _variant_opt(opt),
                        "binary": (
                            Path("binaries") / opt / project / binary_name
                        ).as_posix(),
                        "addr": hex(addresses[symbol]),
                        "isa": isa,
                        "format": fmt,
                        "abi_profile": abi,
                        "source_cfg": local_cfg_rel.as_posix() if source_cfg_remote else "",
                    }
                ],
            }
        )
    return {
        "project": project,
        "opt": opt,
        "binary": stem,
        "binary_file": binary_name,
        "functions": functions,
        "requested": len(wanted),
        "resolved": len(functions),
        "source_cfg_resolved": len((wanted & set(addresses)) & cfg_symbols),
        "unresolved": sorted(wanted - set(addresses)),
        "binary_sha256": _sha256(local_binary),
        "source_cfg": local_cfg_rel.as_posix() if source_cfg_remote else None,
    }


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def materialize(args: argparse.Namespace) -> dict[str, Any]:
    lock = _load_lock(args.lock)
    config_meta = (lock.get("configs") or {}).get(args.config)
    if not isinstance(config_meta, dict):
        raise ValueError(
            f"unknown config {args.config!r}; choose from {sorted(lock['configs'])}"
        )
    repo = str(lock["dataset_repo"])
    revision = str(lock["revision"])
    manifest_remote = str(config_meta["manifest"])
    manifest_cache = (
        ROOT
        / ".cache"
        / "scale-corpus"
        / revision
        / args.config
        / "manifest.json"
    )
    _download(
        repo=repo,
        revision=revision,
        relative=manifest_remote,
        destination=manifest_cache,
    )
    dataset_manifest = json.loads(manifest_cache.read_text(encoding="utf-8"))
    groups = list(dataset_manifest.get("binaries") or [])
    if int(dataset_manifest.get("function_count") or 0) != int(
        config_meta.get("functions") or 0
    ) or len(groups) != int(config_meta.get("binaries") or 0):
        raise RuntimeError(
            "pinned dataset manifest counts drifted from dataset-lock.json"
        )
    excluded: list[str] = []
    if not args.include_malware:
        excluded = sorted(
            {
                str(group.get("project"))
                for group in groups
                if str(group.get("project")) in MALWARE_PROJECTS
            }
        )
        groups = [
            group
            for group in groups
            if str(group.get("project")) not in MALWARE_PROJECTS
        ]
    if args.max_binaries:
        groups = groups[: args.max_binaries]
    elif not args.include_malware and config_meta.get("safe_binaries"):
        if len(groups) != int(config_meta["safe_binaries"]):
            raise RuntimeError("malware-excluded binary count drifted from lock")
        safe_functions = sum(len(group.get("functions") or []) for group in groups)
        if safe_functions != int(config_meta["safe_functions"]):
            raise RuntimeError("malware-excluded function count drifted from lock")

    results: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [
            pool.submit(
                _materialize_group,
                group,
                repo=repo,
                revision=revision,
                corpus_dir=args.corpus_dir,
            )
            for group in groups
        ]
        for index, future in enumerate(concurrent.futures.as_completed(futures), 1):
            result = future.result()
            results.append(result)
            print(
                f"[{index}/{len(futures)}] {result['opt']}/{result['project']}/"
                f"{result['binary']}: {result['resolved']}/{result['requested']}",
                flush=True,
            )

    manifests_dir = args.corpus_dir / "manifests"
    manifests_dir.mkdir(parents=True, exist_ok=True)
    expected_names: set[str] = set()
    for result in results:
        name = _manifest_name(result["opt"], result["project"], result["binary"])
        expected_names.add(name)
        _write_json(
            manifests_dir / name,
            {
                "schema": "fission-external-corpus-v1",
                "dataset": {
                    "name": "decbench",
                    "repository": repo,
                    "revision": revision,
                    "config": args.config,
                    "license": lock["license"],
                },
                "functions": result["functions"],
            },
        )
    if args.prune and not args.max_binaries:
        for path in manifests_dir.glob("*.json"):
            if path.name not in expected_names:
                path.unlink()

    requested = sum(result["requested"] for result in results)
    resolved = sum(result["resolved"] for result in results)
    coverage = resolved / requested if requested else 0.0
    cfg_functions = sum(result["source_cfg_resolved"] for result in results)
    cfg_coverage = cfg_functions / resolved if resolved else 0.0
    if not args.max_binaries and not args.include_malware:
        expected_resolved = config_meta.get("safe_resolved_functions")
        expected_cfg = config_meta.get("safe_source_cfg_functions")
        if expected_resolved is not None and resolved != int(expected_resolved):
            raise RuntimeError("malware-excluded resolved function count drifted from lock")
        if expected_cfg is not None and cfg_functions != int(expected_cfg):
            raise RuntimeError("malware-excluded source CFG count drifted from lock")
    inventory = {
        "schema": "fission-scale-corpus-inventory-v1",
        "dataset": "decbench",
        "repository": repo,
        "revision": revision,
        "license": lock["license"],
        "config": args.config,
        "source_function_count": int(dataset_manifest.get("function_count") or 0),
        "selected_binaries": len(results),
        "requested_functions": requested,
        "resolved_functions": resolved,
        "address_coverage": round(coverage, 6),
        "source_cfg_functions": cfg_functions,
        "source_cfg_coverage": round(cfg_coverage, 6),
        "malware_included": bool(args.include_malware),
        "excluded_projects": excluded,
        "groups": [
            {
                key: value
                for key, value in result.items()
                if key not in {"functions", "unresolved"}
            }
            | {"unresolved_count": len(result["unresolved"])}
            for result in sorted(
                results,
                key=lambda item: (item["opt"], item["project"], item["binary"]),
            )
        ],
        "unresolved_sample": [
            f"{result['opt']}/{result['project']}/{result['binary']}::{name}"
            for result in results
            for name in result["unresolved"][:10]
        ][:200],
    }
    _write_json(args.corpus_dir / "inventory.json", inventory)
    if coverage < args.min_address_coverage:
        raise RuntimeError(
            f"address coverage {coverage:.2%} < required "
            f"{args.min_address_coverage:.2%}; see {args.corpus_dir / 'inventory.json'}"
        )
    if cfg_coverage < args.min_source_cfg_coverage:
        raise RuntimeError(
            f"source CFG coverage {cfg_coverage:.2%} < required "
            f"{args.min_source_cfg_coverage:.2%}; see "
            f"{args.corpus_dir / 'inventory.json'}"
        )
    return inventory


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="unoptimized")
    parser.add_argument("--lock", type=Path, default=LOCK_PATH)
    parser.add_argument("--corpus-dir", type=Path, default=CORPUS_DIR)
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--max-binaries", type=int, default=0)
    parser.add_argument("--min-address-coverage", type=float, default=0.98)
    parser.add_argument("--min-source-cfg-coverage", type=float, default=0.95)
    parser.add_argument(
        "--include-malware",
        action="store_true",
        help="Include DecBench's five real-malware projects (never executed).",
    )
    parser.add_argument(
        "--prune",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Remove generated manifest shards outside this materialization.",
    )
    args = parser.parse_args(argv)
    if args.workers < 1:
        parser.error("--workers must be >= 1")
    inventory = materialize(args)
    print(
        "Materialized "
        f"{inventory['resolved_functions']:,} functions / "
        f"{inventory['selected_binaries']:,} binaries "
        f"({inventory['address_coverage']:.2%} address, "
        f"{inventory['source_cfg_coverage']:.2%} source-CFG coverage)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
