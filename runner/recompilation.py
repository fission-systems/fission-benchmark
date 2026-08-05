"""Same-toolchain recompilation bytematch diagnostic.

The metric follows DecBench's byte-match contract: compile decompiled C for
the original binary ABI and optimization level, extract the function bytes,
normalize relocation-dependent operands, and compare ordered assembly lines.
It is deliberately non-ranking; semantic execution remains the headline.
"""
from __future__ import annotations

import difflib
import hashlib
import functools
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Mapping

try:
    from .metric_cache import load as cache_load, store as cache_store
except ImportError:
    from metric_cache import load as cache_load, store as cache_store

try:
    from .bare_compile import build_bare_tu
    from .type_match import BinInfo, detect, dwarf_info
except ImportError:
    from bare_compile import build_bare_tu
    from type_match import BinInfo, detect, dwarf_info

_BRANCH_MNEMONICS = frozenset(
    {
        "call", "jmp", "loop", "loope", "loopne", "jecxz", "jrcxz",
        "je", "jne", "jz", "jnz", "jg", "jge", "jl", "jle", "ja",
        "jae", "jb", "jbe", "jc", "jnc", "js", "jns", "jo", "jno",
        "jp", "jnp", "jpe", "jpo", "jcxz",
    }
)
_HEX_TOKEN = re.compile(r"#?-?(?:0x[0-9a-fA-F]+|\d+)")
_PC_REL_MEM = re.compile(
    r"\[(rip|pc)(?:\s*[+\-,]\s*#?-?(?:0x[0-9a-fA-F]+|\d+))?\]"
)


@functools.lru_cache(maxsize=256)
def _file_sha256(path: str, mtime_ns: int, size: int) -> str:
    _ = mtime_ns, size
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _compiler_command(info: BinInfo, compiler_variant: str) -> tuple[str, list[str]] | None:
    compiler, _, opt = compiler_variant.partition(" ")
    flags = [opt or "-O0", "-c", "-fno-builtin", "-w", "-std=c11"]
    if info.fmt == "pe":
        if compiler == "clang":
            target = "x86_64-w64-windows-gnu" if info.bits == 64 else "i686-w64-windows-gnu"
            return "clang", [f"--target={target}", *flags]
        executable = (
            "x86_64-w64-mingw32-gcc" if info.bits == 64 else "i686-w64-mingw32-gcc"
        )
        return executable, flags
    if info.fmt == "elf" and info.arch == "x86-64":
        return ("clang" if compiler == "clang" else "gcc"), flags
    if info.fmt == "elf" and info.arch == "x86":
        return ("clang" if compiler == "clang" else "gcc"), ["-m32", *flags]
    if info.fmt == "elf" and info.arch == "aarch64":
        return "aarch64-linux-gnu-gcc", flags
    return None


def _function_range(path: Path, function_name: str) -> tuple[int, int] | None:
    info = dwarf_info(path)
    if info is None:
        return None
    for cu in info.iter_CUs():
        for die in cu.iter_DIEs():
            if die.tag != "DW_TAG_subprogram":
                continue
            name_attr = die.attributes.get("DW_AT_name")
            value = name_attr.value if name_attr else None
            name = value.decode(errors="replace") if isinstance(value, bytes) else str(value or "")
            if name != function_name or "DW_AT_low_pc" not in die.attributes:
                continue
            low = int(die.attributes["DW_AT_low_pc"].value)
            high_attr = die.attributes.get("DW_AT_high_pc")
            if high_attr is None:
                return None
            high_value = int(high_attr.value)
            high = high_value if high_attr.form == "DW_FORM_addr" else low + high_value
            return (low, high) if high > low else None
    return None


def _original_function_bytes(
    path: Path, function_name: str, address: int | None
) -> bytes | None:
    info = detect(path)
    if info is None:
        return None
    if info.fmt == "elf":
        try:
            from elftools.elf.elffile import ELFFile

            with path.open("rb") as stream:
                elf = ELFFile(stream)
                symtab = elf.get_section_by_name(".symtab")
                if symtab is not None:
                    for symbol in symtab.iter_symbols():
                        if (
                            symbol.name == function_name
                            or (address is not None and symbol["st_value"] == address)
                        ) and symbol["st_size"] > 0:
                            section = elf.get_section(symbol["st_shndx"])
                            offset = symbol["st_value"] - section["sh_addr"]
                            return section.data()[offset : offset + symbol["st_size"]]
        except Exception:
            pass
    function_range = _function_range(path, function_name)
    if function_range is None:
        return None
    low, high = function_range
    try:
        import lief

        binary = lief.parse(str(path))
        if binary is None:
            return None
        content = binary.get_content_from_virtual_address(low, high - low)
        return bytes(content) if content else None
    except Exception:
        return None


def _object_function_bytes(path: Path, function_name: str) -> bytes | None:
    info = detect(path)
    if info is not None and info.fmt == "elf":
        try:
            from elftools.elf.elffile import ELFFile

            with path.open("rb") as stream:
                elf = ELFFile(stream)
                text = elf.get_section_by_name(".text")
                symtab = elf.get_section_by_name(".symtab")
                if text is not None and symtab is not None:
                    for symbol in symtab.iter_symbols():
                        if symbol.name == function_name and symbol["st_size"] > 0:
                            start = int(symbol["st_value"])
                            return text.data()[start : start + int(symbol["st_size"])]
        except Exception:
            pass
    try:
        import lief

        obj = lief.parse(str(path))
        if obj is None:
            return None
        for section in obj.sections:
            if section.name == ".text" or section.name.startswith(".text$"):
                return bytes(section.content)
    except Exception:
        pass
    return None


def _normalize_operands(mnemonic: str, operands: str) -> str:
    operands = _PC_REL_MEM.sub(lambda match: f"[{match.group(1)}+X]", operands)
    if mnemonic in _BRANCH_MNEMONICS and "[" not in operands:
        operands = _HEX_TOKEN.sub("X", operands)
    return operands


def _disassemble(data: bytes, info: BinInfo, address: int = 0) -> list[str]:
    import capstone

    if info.arch not in {"x86", "x86-64"}:
        return []
    mode = capstone.CS_MODE_64 if info.bits == 64 else capstone.CS_MODE_32
    disassembler = capstone.Cs(capstone.CS_ARCH_X86, mode)
    lines = []
    for instruction in disassembler.disasm(data, address):
        if instruction.mnemonic == "nop":
            continue
        operands = _normalize_operands(instruction.mnemonic, instruction.op_str)
        lines.append(f"{instruction.mnemonic} {operands}".strip())
    return lines


def _ordered_jaccard(left: list[str], right: list[str]) -> tuple[float, int]:
    if not left and not right:
        return 1.0, 0
    if not left or not right:
        return 0.0, len(left) + len(right)
    matcher = difflib.SequenceMatcher(a=left, b=right, autojunk=False)
    shared = sum(block.size for block in matcher.get_matching_blocks())
    changed = (len(left) - shared) + (len(right) - shared)
    union = len(left) + len(right) - shared
    return (shared / union if union else 1.0), changed


def _measure_recompilation_uncached(
    decompiled_code: str,
    *,
    function_name: str,
    binary_path: Path,
    function_address: str | int | None,
    compiler_variant: str,
    timeout_s: float = 10.0,
) -> tuple[float | None, dict[str, Any]]:
    """Return ``(score, evidence)``; ``None`` means the toolchain cannot measure."""
    metadata: dict[str, Any] = {
        "schema": "recompilation-bytematch-v1",
        "ranking": False,
        "comparison": "ordered normalized assembly Jaccard",
    }
    info = detect(binary_path)
    if info is None:
        return None, {**metadata, "category": "unsupported_binary"}
    command = _compiler_command(info, compiler_variant)
    if command is None:
        return None, {
            **metadata,
            "category": "unsupported_abi",
            "binary_format": info.fmt,
            "arch": info.arch,
        }
    compiler, flags = command
    metadata.update(
        compiler=compiler,
        flags=flags,
        binary_format=info.fmt,
        arch=info.arch,
    )
    if shutil.which(compiler) is None:
        return None, {**metadata, "category": "toolchain_missing", "compilable": None}
    if not decompiled_code.strip():
        return 0.0, {**metadata, "category": "empty", "compilable": False}

    try:
        address = (
            int(function_address, 0)
            if isinstance(function_address, str)
            else int(function_address or 0)
        )
    except ValueError:
        address = 0
    original = _original_function_bytes(binary_path, function_name, address or None)
    if original is None:
        return 0.0, {**metadata, "category": "original_bytes_missing", "compilable": None}

    with tempfile.TemporaryDirectory() as tmp:
        source_path = Path(tmp) / "recompile.c"
        object_path = Path(tmp) / "recompile.o"
        source_path.write_text(build_bare_tu(decompiled_code), encoding="utf-8")
        try:
            process = subprocess.run(
                [compiler, *flags, str(source_path), "-o", str(object_path)],
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
        except subprocess.TimeoutExpired:
            return 0.0, {**metadata, "category": "timeout", "compilable": False}
        if process.returncode != 0:
            error = re.sub(r"\s+", " ", process.stderr or process.stdout).strip()[:400]
            return 0.0, {
                **metadata,
                "category": "compile_error",
                "compilable": False,
                "error": error,
            }
        recompiled = _object_function_bytes(object_path, function_name)
        if recompiled is None:
            return 0.0, {
                **metadata,
                "category": "recompiled_bytes_missing",
                "compilable": True,
            }

    if recompiled == original:
        return 1.0, {
            **metadata,
            "category": "ok",
            "compilable": True,
            "exact_match": True,
            "changed_lines": 0,
            "original_size": len(original),
            "recompiled_size": len(recompiled),
        }
    original_asm = _disassemble(original, info, address)
    recompiled_asm = _disassemble(recompiled, info)
    score, changed = _ordered_jaccard(original_asm, recompiled_asm)
    return round(score, 4), {
        **metadata,
        "category": "ok",
        "compilable": True,
        "exact_match": score == 1.0,
        "changed_lines": changed,
        "original_size": len(original),
        "recompiled_size": len(recompiled),
        "original_asm_lines": len(original_asm),
        "recompiled_asm_lines": len(recompiled_asm),
    }


def measure_recompilation(
    decompiled_code: str,
    *,
    function_name: str,
    binary_path: Path,
    function_address: str | int | None,
    compiler_variant: str,
    timeout_s: float = 10.0,
) -> tuple[float | None, dict[str, Any]]:
    """Content-cached wrapper around recompilation bytematch."""
    try:
        stat = binary_path.stat()
        binary_sha256 = _file_sha256(
            str(binary_path.resolve()), stat.st_mtime_ns, stat.st_size
        )
    except OSError:
        binary_sha256 = "missing"
    key = {
        "binary_sha256": binary_sha256,
        "decompiled_code": decompiled_code,
        "function_name": function_name,
        "function_address": str(function_address or ""),
        "compiler_variant": compiler_variant,
        "timeout_s": timeout_s,
    }
    cached = cache_load("recompilation", "v1", key)
    if isinstance(cached, dict) and "metadata" in cached:
        metadata = dict(cached["metadata"])
        metadata["cache"] = {"schema": "metric-content-cache-v1", "hit": True}
        return cached.get("score"), metadata

    score, metadata = _measure_recompilation_uncached(
        decompiled_code,
        function_name=function_name,
        binary_path=binary_path,
        function_address=function_address,
        compiler_variant=compiler_variant,
        timeout_s=timeout_s,
    )
    cache_store(
        "recompilation",
        "v1",
        key,
        {"score": score, "metadata": metadata},
    )
    metadata = dict(metadata)
    metadata["cache"] = {"schema": "metric-content-cache-v1", "hit": False}
    return score, metadata


def aggregate_recompilation(rows: list[Mapping[str, Any]]) -> dict[str, Any]:
    cells = {
        (
            str(row.get("corpus") or ""),
            str(row.get("function_name") or ""),
            str(row.get("compiler_variant") or ""),
        )
        for row in rows
        if row.get("recompilation_score") is not None
    }
    by_tool: dict[str, dict[str, Any]] = {}
    for tool in sorted({str(row.get("decompiler") or "unknown") for row in rows}):
        tool_rows = [row for row in rows if str(row.get("decompiler") or "unknown") == tool]
        scores = [float(row["recompilation_score"]) for row in tool_rows if row.get("recompilation_score") is not None]
        perfect = sum(score >= 1.0 for score in scores)
        compilable = sum(bool((row.get("recompilation") or {}).get("compilable")) for row in tool_rows)
        by_tool[tool] = {
            "observed_rows": len(scores),
            "shared_rows": len(cells),
            "compilable_rows": compilable,
            "mean_similarity": round(sum(scores) / len(scores), 4) if scores else None,
            "perfect_rows": perfect,
            "perfect_rate": round(perfect / len(cells), 4) if cells else None,
        }
    return {
        "schema": "recompilation-bytematch-v1",
        "ranking": False,
        "denominator": "shared-by-subject-v1",
        "note": "Same-ABI/toolchain normalized assembly match; semantic execution remains ranking.",
        "by_decompiler": by_tool,
    }
