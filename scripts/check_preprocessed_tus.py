#!/usr/bin/env python3
"""Fail closed when C/C++ variants lack compiler-matched preprocessed TUs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def missing_preprocessed_tus(split_root: Path) -> list[str]:
    missing: list[str] = []
    for manifest in sorted((split_root / "manifests").glob("*.json")):
        data = json.loads(manifest.read_text(encoding="utf-8"))
        for function in data.get("functions", []):
            source = str(function.get("source") or "")
            language = str(function.get("language") or "").lower()
            if not language:
                language = (
                    "cpp"
                    if Path(source).suffix.lower() in {".cc", ".cpp", ".cxx"}
                    else "c"
                )
            if language not in {"c", "cpp"}:
                continue
            for variant in function.get("compiler_variants", []):
                preprocessed = str(variant.get("preprocessed_source") or "")
                label = (
                    f"{manifest.name}:{function.get('name')}:"
                    f"{variant.get('compiler')} {variant.get('opt')}"
                )
                if not preprocessed:
                    missing.append(f"{label}: missing manifest field")
                elif not (split_root / preprocessed).is_file():
                    missing.append(f"{label}: missing file {preprocessed}")
    return missing


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("split_roots", nargs="+", type=Path)
    args = parser.parse_args()
    failures: list[str] = []
    for split_root in args.split_roots:
        failures.extend(missing_preprocessed_tus(split_root))
    if failures:
        for failure in failures:
            print(f"FAIL {failure}")
        raise SystemExit(f"preprocessed TU contract failed ({len(failures)} variants)")
    print("preprocessed TU contract ok")


if __name__ == "__main__":
    main()
