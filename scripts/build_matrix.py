#!/usr/bin/env python3
"""Multi-language / multi-opt corpus builder.

Extends the legacy C mingw path with:
  - optional language/isa/format tags on variants
  - inventory.json fingerprint
  - profile-aware no-op (profiles filter at run time; build still builds manifests)

Usage:
  CORPUS_TARGET=windows-x86_64 python scripts/build_matrix.py --split dev
  python scripts/build_matrix.py --split dev --languages c
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CORPUS_ROOT = ROOT / "corpus"
CORPUS_TARGET = os.environ.get("CORPUS_TARGET", "host")
sys.path.insert(0, str(ROOT))
from runner.preprocessed_tu import (  # noqa: E402
    preprocessed_tu_path,
    strip_system_headers,
)


def target_tool(compiler: str, tool: str) -> str:
    if CORPUS_TARGET == "windows-x86_64":
        if compiler in {"gcc", "clang"}:
            if tool == "gcc":
                return "clang" if compiler == "clang" else "x86_64-w64-mingw32-gcc"
            return f"x86_64-w64-mingw32-{tool}"
        if compiler in {"gcc-m32", "clang-m32"}:
            if tool == "gcc":
                return "clang" if compiler == "clang-m32" else "i686-w64-mingw32-gcc"
            return f"i686-w64-mingw32-{tool}"
        if compiler in {"g++", "cpp", "cxx"}:
            if tool == "gcc":
                return "x86_64-w64-mingw32-g++"
            return f"x86_64-w64-mingw32-{tool}"
    if compiler in {"g++", "cpp", "cxx"} and tool == "gcc":
        return "g++"
    return compiler if tool == "gcc" else tool


def target_binary(binary: str, fmt: str = "") -> str:
    # ELF / non-PE must never get a forced .exe suffix.
    if fmt == "elf":
        return binary
    if fmt == "pe" or CORPUS_TARGET == "windows-x86_64":
        if not binary.endswith(".exe") and not binary.endswith(".dll"):
            return f"{binary}.exe"
    return binary


def compiler_binary(name: str) -> str:
    binary = shutil.which(name)
    if not binary:
        raise SystemExit(f"Compiler/tool not found on PATH: {name}")
    return binary


def _select_c_tool(compiler: str, *, language: str, fmt: str, isa: str) -> str:
    """Pick the actual compiler binary for a C/C++ variant."""
    is_cpp = language == "cpp" or compiler in {"g++", "cpp", "cxx", "clang++"}
    if fmt == "elf":
        if isa == "aarch64" or compiler in {"gcc-aarch64", "aarch64"}:
            return "aarch64-linux-gnu-g++" if is_cpp else "aarch64-linux-gnu-gcc"
        # Host Linux ELF x86_64 (docker corpus-builder). On macOS this is usually
        # unavailable; build will fail with a clear missing-tool message.
        if is_cpp:
            return "g++"
        if compiler in {"gcc-elf", "gcc"}:
            return "gcc"
        if compiler == "clang":
            return "clang"
        return "gcc"
    # PE / windows path (existing)
    if is_cpp:
        return (
            "x86_64-w64-mingw32-g++"
            if CORPUS_TARGET == "windows-x86_64"
            else "g++"
        )
    return target_tool(compiler, "gcc")


def compile_c_family(
    compiler: str,
    opt: str,
    source: Path,
    output: Path,
    *,
    language: str = "c",
    fmt: str = "",
    isa: str = "",
) -> None:
    """Compile C or C++ for PE (mingw) or ELF (host / aarch64 cross)."""
    is_cpp = language == "cpp" or compiler in {"g++", "cpp", "cxx", "clang++"}
    fmt = fmt or ("pe" if CORPUS_TARGET == "windows-x86_64" else "elf")
    isa = isa or (
        "x86_32"
        if compiler in {"gcc-m32", "clang-m32"}
        else ("aarch64" if compiler in {"gcc-aarch64", "aarch64"} else "x86_64")
    )
    selected = _select_c_tool(compiler, language=language, fmt=fmt, isa=isa)

    output.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        compiler_binary(selected),
        opt,
        "-g",
        "-fno-inline",
        "-fno-omit-frame-pointer",
        "-o",
        str(output),
        str(source),
    ]
    if is_cpp:
        cmd[1:1] = ["-std=c++17", "-fno-exceptions"]

    if fmt == "elf":
        # Static aarch64 helps qemu-user; x64 static optional.
        if isa == "aarch64":
            cmd.insert(1, "-static")
        if "-fno-pie" not in cmd:
            cmd[1:1] = ["-fno-pie", "-no-pie"]
    else:
        # PE / mingw clang cross
        if not is_cpp and compiler == "clang" and CORPUS_TARGET == "windows-x86_64":
            cmd.insert(1, "-target")
            cmd.insert(2, "x86_64-w64-mingw32")
            cmd.append("-L/usr/lib/gcc/x86_64-w64-mingw32/12-posix/")
        elif not is_cpp and compiler == "clang-m32" and CORPUS_TARGET == "windows-x86_64":
            cmd.insert(1, "-target")
            cmd.insert(2, "i686-w64-mingw32")
            cmd.append("-L/usr/lib/gcc/i686-w64-mingw32/12-posix/")

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        if "-no-pie" not in cmd and "-static" not in cmd:
            print(f"Compilation error ({source.name}): {e.stderr}", file=sys.stderr)
            raise
        fallback = [part for part in cmd if part not in {"-fno-pie", "-no-pie", "-static"}]
        try:
            subprocess.run(fallback, check=True, capture_output=True, text=True)
        except subprocess.CalledProcessError as e2:
            print(f"Compilation error ({source.name}): {e2.stderr}", file=sys.stderr)
            raise


def preprocess_c_family(
    compiler: str,
    opt: str,
    source: Path,
    output: Path,
    *,
    corpus_root: Path,
    language: str = "c",
    fmt: str = "",
    isa: str = "",
) -> None:
    """Emit the exact compiler-specific C/C++ TU used as GED ground truth."""
    is_cpp = language == "cpp" or compiler in {"g++", "cpp", "cxx", "clang++"}
    fmt = fmt or ("pe" if CORPUS_TARGET == "windows-x86_64" else "elf")
    isa = isa or (
        "x86_32"
        if compiler in {"gcc-m32", "clang-m32"}
        else ("aarch64" if compiler in {"gcc-aarch64", "aarch64"} else "x86_64")
    )
    selected = _select_c_tool(compiler, language=language, fmt=fmt, isa=isa)
    cmd = [compiler_binary(selected), "-E", opt, "-g", "-fno-inline"]
    if is_cpp:
        cmd.extend(["-std=c++17", "-fno-exceptions"])
    if not is_cpp and compiler == "clang" and CORPUS_TARGET == "windows-x86_64":
        cmd.extend(["-target", "x86_64-w64-mingw32"])
    elif not is_cpp and compiler == "clang-m32" and CORPUS_TARGET == "windows-x86_64":
        cmd.extend(["-target", "i686-w64-mingw32"])
    cmd.append(str(source))

    try:
        proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr or exc.stdout or str(exc)
        print(f"Preprocessing error ({source.name}): {detail}", file=sys.stderr)
        raise

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        strip_system_headers(
            proc.stdout,
            source_path=source,
            corpus_root=corpus_root,
        ),
        encoding="utf-8",
    )


def symbol_addresses(binary: Path, compiler: str) -> dict[str, str]:
    nm_name = _nm_for_compiler(compiler)
    nm = shutil.which(nm_name) or shutil.which("nm")
    if not nm:
        raise SystemExit(f"{nm_name} not found on PATH")

    proc = subprocess.run(
        [nm, "-n", str(binary)], check=True, capture_output=True, text=True
    )
    symbols: dict[str, str] = {}
    for line in proc.stdout.splitlines():
        parts = line.split()
        if len(parts) < 3:
            continue
        addr, sym_type, name = parts[-3], parts[-2], parts[-1]
        if sym_type.lower() not in {"t", "t"} and sym_type not in {"T", "t", "W", "w"}:
            # Keep text symbols; also accept some weak text.
            if sym_type not in {"T", "t", "W", "w"}:
                continue
        try:
            parsed_addr = hex(int(addr, 16))
            symbols[name] = parsed_addr
            if name.startswith("_"):
                symbols[name[1:]] = parsed_addr
            # MSVC/mingw C++ sometimes prefix
            if name.startswith("__Z") or name.startswith("_Z"):
                symbols[name] = parsed_addr
        except ValueError:
            continue
    return symbols


def _tag_variant(variant: dict[str, Any], compiler: str) -> None:
    if not variant.get("format"):
        if str(variant.get("binary", "")).endswith(".exe"):
            variant["format"] = "pe"
        else:
            variant["format"] = "elf" if CORPUS_TARGET != "windows-x86_64" else "pe"
    if not variant.get("isa"):
        variant["isa"] = (
            "x86_32" if compiler in {"gcc-m32", "clang-m32"} else "x86_64"
        )
    if not variant.get("abi_profile"):
        if variant.get("format") == "pe":
            variant["abi_profile"] = (
                "windows-x86"
                if variant.get("isa") == "x86_32"
                else "windows-x86_64"
            )
        else:
            variant["abi_profile"] = "linux-x86_64"


def _nm_for_compiler(compiler: str) -> str:
    if compiler in {"gcc-aarch64", "aarch64"}:
        return "aarch64-linux-gnu-nm"
    if compiler in {"gcc-elf"}:
        return "nm"
    if CORPUS_TARGET == "windows-x86_64":
        if compiler in {"gcc-m32", "clang-m32"}:
            return "i686-w64-mingw32-nm"
        return "x86_64-w64-mingw32-nm"
    return "nm"


def _rust_opt_level(opt: str) -> str:
    o = (opt or "").strip()
    mapping = {
        "-O0": "0",
        "0": "0",
        "-O1": "1",
        "1": "1",
        "-O2": "2",
        "2": "2",
        "-O3": "3",
        "3": "3",
        "-Os": "s",
        "s": "s",
    }
    return mapping.get(o, "0")


def compile_go(opt: str, source: Path, output: Path) -> None:
    """Compile a Go CGO package directory (or main.go parent) for CORPUS_TARGET."""
    go = shutil.which("go")
    if not go:
        raise SystemExit("go not found on PATH")
    # source may be a directory (module) or a .go file
    if source.is_file():
        pkg_dir = source.parent
    else:
        pkg_dir = source
    if not (pkg_dir / "go.mod").is_file() and not list(pkg_dir.glob("*.go")):
        raise SystemExit(f"Go package not found at {pkg_dir}")

    output.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["CGO_ENABLED"] = "1"
    cmd = [go, "build", "-o", str(output)]
    o = (opt or "default").strip()
    if o in {"noopt", "-N", "-N -l", "-O0", "0"}:
        # Disable optimizations / inlining for a clearer decomp surface.
        cmd.extend(["-gcflags=all=-N -l"])
    if CORPUS_TARGET == "windows-x86_64":
        cc = shutil.which("x86_64-w64-mingw32-gcc")
        if not cc:
            raise SystemExit(
                "x86_64-w64-mingw32-gcc required for CGO windows PE (GOOS=windows)"
            )
        env["GOOS"] = "windows"
        env["GOARCH"] = "amd64"
        env["CC"] = cc
        # Help cgo find mingw headers/libs on some hosts.
        env.setdefault("CGO_CFLAGS", "-O2")
        env.setdefault("CGO_LDFLAGS", "-static-libgcc")
    cmd.append(".")
    try:
        subprocess.run(
            cmd,
            check=True,
            capture_output=True,
            text=True,
            cwd=str(pkg_dir),
            env=env,
        )
    except subprocess.CalledProcessError as e:
        detail = e.stderr or e.stdout or str(e)
        print(f"Go compilation error ({pkg_dir.name}): {detail}", file=sys.stderr)
        raise


def compile_rust(opt: str, source: Path, output: Path) -> None:
    """Compile a Rust bin crate (single .rs with main) for CORPUS_TARGET."""
    rustc = shutil.which("rustc")
    if not rustc:
        raise SystemExit("rustc not found on PATH (install rustup + rustc)")
    output.parent.mkdir(parents=True, exist_ok=True)
    level = _rust_opt_level(opt)
    cmd = [
        rustc,
        str(source),
        "--edition",
        "2021",
        "--crate-type",
        "bin",
        f"-Copt-level={level}",
        "-Cdebuginfo=1",
        "-Cpanic=abort",
        "-o",
        str(output),
    ]
    if CORPUS_TARGET == "windows-x86_64":
        linker = shutil.which("x86_64-w64-mingw32-gcc")
        if not linker:
            raise SystemExit(
                "x86_64-w64-mingw32-gcc required to link rustc windows-gnu PE"
            )
        cmd.extend(
            [
                "--target",
                "x86_64-pc-windows-gnu",
                f"-Clinker={linker}",
            ]
        )
    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        detail = e.stderr or e.stdout or str(e)
        print(f"Rust compilation error ({source.name}): {detail}", file=sys.stderr)
        raise


def _compile_one(
    language: str,
    compiler: str,
    opt: str,
    source: Path,
    output: Path,
    *,
    fmt: str = "",
    isa: str = "",
) -> None:
    if language == "go" or compiler == "go":
        compile_go(opt, source, output)
    elif language == "rust" or compiler == "rustc":
        compile_rust(opt, source, output)
    elif language in {"c", "cpp"} or compiler in {
        "gcc",
        "clang",
        "gcc-m32",
        "clang-m32",
        "g++",
        "clang++",
        "gcc-elf",
        "gcc-aarch64",
        "aarch64",
    }:
        compile_c_family(
            compiler,
            opt,
            source,
            output,
            language="cpp" if language == "cpp" or compiler in {"g++", "clang++"} else "c",
            fmt=fmt,
            isa=isa,
        )
    else:
        raise SystemExit(f"Unsupported language/compiler: {language}/{compiler}")


def build_manifest(manifest_path: Path, split: str, languages: set[str] | None) -> None:
    data = json.loads(manifest_path.read_text())
    built: set[tuple[str, str, str, str]] = set()
    supported = {"c", "cpp", "rust", "go"}

    for fn in data["functions"]:
        language = fn.get("language") or "c"
        if language == "c" and "/c/" not in fn.get("source", "") and not fn.get(
            "source", ""
        ).startswith("source/c/"):
            language = "c"
        if languages is not None and language not in languages:
            continue
        if language not in supported:
            print(
                f"[skip] {fn.get('name')}: language={language} not built yet "
                f"(supported: {sorted(supported)})"
            )
            continue

        source = CORPUS_ROOT / split / fn["source"]
        if not source.is_file() and not source.is_dir():
            alt = CORPUS_ROOT / split / "source" / language / Path(fn["source"]).name
            if alt.is_file() or alt.is_dir():
                fn["source"] = str(Path("source") / language / alt.name)
                source = alt
            else:
                print(f"[warn] missing source {source}", file=sys.stderr)
                continue

        if not fn.get("language"):
            fn["language"] = language
        if not fn.get("semantic"):
            fn["semantic"] = {
                "mode": "c_wrapper",
                "wrapper_id": fn["name"],
                "oracle": "pe_wine",
            }

        for variant in fn.get("compiler_variants", []):
            compiler = variant["compiler"]
            _tag_variant(variant, compiler)
            variant["binary"] = target_binary(
                variant["binary"], variant.get("format", "")
            )
            if language in {"c", "cpp"}:
                variant["preprocessed_source"] = preprocessed_tu_path(
                    variant["binary"], language=language
                )
            key = (
                fn["source"],
                compiler,
                variant["opt"],
                variant["binary"],
            )
            if key in built:
                continue
            out = CORPUS_ROOT / split / variant["binary"]
            _compile_one(
                language,
                compiler,
                variant["opt"],
                source,
                out,
                fmt=str(variant.get("format") or ""),
                isa=str(variant.get("isa") or ""),
            )
            if language in {"c", "cpp"}:
                preprocess_c_family(
                    compiler,
                    variant["opt"],
                    source,
                    CORPUS_ROOT / split / variant["preprocessed_source"],
                    corpus_root=CORPUS_ROOT / split,
                    language=language,
                    fmt=str(variant.get("format") or ""),
                    isa=str(variant.get("isa") or ""),
                )
            built.add(key)

    addr_cache: dict[str, dict[str, str]] = {}
    for fn in data["functions"]:
        language = fn.get("language") or "c"
        if languages is not None and language not in languages:
            continue
        if language not in supported:
            continue
        for variant in fn.get("compiler_variants", []):
            binary = variant["binary"]
            if binary not in addr_cache:
                path = CORPUS_ROOT / split / binary
                if not path.is_file():
                    continue
                addr_cache[binary] = symbol_addresses(path, variant["compiler"])
            resolved = addr_cache.get(binary, {}).get(fn["name"])
            if not resolved:
                resolved = addr_cache.get(binary, {}).get(f"_{fn['name']}")
            if resolved:
                variant["addr"] = resolved
            _tag_variant(variant, variant["compiler"])

    manifest_path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"[✓] Synced manifest: {manifest_path.name}")


def write_inventory(split: str) -> None:
    split_root = CORPUS_ROOT / split
    binaries = sorted((split_root / "binaries").rglob("*")) if (split_root / "binaries").exists() else []
    files = [p for p in binaries if p.is_file()]
    h = hashlib.sha256()
    for p in files:
        h.update(p.name.encode())
        h.update(str(p.stat().st_size).encode())
    inv = {
        "split": split,
        "corpus_target": CORPUS_TARGET,
        "binary_count": len(files),
        "fingerprint": h.hexdigest()[:16],
        "builder": "build_matrix.py",
    }
    path = split_root / "inventory.json"
    path.write_text(json.dumps(inv, indent=2) + "\n")
    print(f"[✓] Wrote {path.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build multi-language corpus binaries")
    parser.add_argument("--split", default="dev", choices=["dev", "holdout"])
    parser.add_argument(
        "--languages",
        default="c,cpp,rust,go",
        help="Comma-separated languages to build (default: c,cpp,rust,go)",
    )
    parser.add_argument(
        "--profile",
        default=None,
        help="Optional profile name (informational; run-time filter is in runner)",
    )
    args = parser.parse_args()
    languages = {x.strip() for x in args.languages.split(",") if x.strip()}
    if args.profile:
        print(f"[i] profile={args.profile} (variants still built from manifests; filter at run)")

    manifests_dir = CORPUS_ROOT / args.split / "manifests"
    if not manifests_dir.is_dir():
        raise SystemExit(f"No manifests at {manifests_dir}")
    for manifest_path in sorted(manifests_dir.glob("*.json")):
        build_manifest(manifest_path, args.split, languages)
    write_inventory(args.split)


if __name__ == "__main__":
    main()
