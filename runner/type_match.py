"""Type correctness metric: decompiled variable types vs. DWARF ground truth.

Compares variable types recovered by a decompiler against the ground-truth
types recorded in the original binary's DWARF debug info (corpus binaries are
always compiled with ``-g``, see ``scripts/build_matrix.py``). Adapted from
decbench's ``type_match`` metric (itself based on the approach from
decompiler-types-benchmark, SURE'25) — see
``vendor/decbench/decbench/metrics/type_match.py`` and
``vendor/decbench/decbench/utils/binfmt.py`` in the Fission monorepo.

fission-benchmark's rows only ever carry raw ``decompiled_code`` text (no
decompiler exposes structured variable objects the way decbench's native
Ghidra/IDA/angr backends do), so this module always uses regex-based
variable extraction from the pseudocode text -- the same code path decbench
uses for its text-only LLM backends. Fission (and Ghidra-style tools
generally) name synthetic stack locals ``local_<hex offset>``, which lets
:func:`_effective_offset` recover a real stack offset even without a
structured decompiler output.

Ground truth extraction handles both ELF and PE (the corpus defaults to
Windows PE via MinGW) -- PE COFF truncates section names to 8 chars, so the
real ``.debug_*`` names + file offsets come from ``objdump -h`` and the bytes
are read straight out of the file to build a self-contained pyelftools
``DWARFInfo``.
"""

from __future__ import annotations

import contextlib
import functools
import logging
import re
import shutil
import struct
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# ── Binary format detection + DWARF extraction (ELF + PE) ──────────────────

_ELF_MACHINES = {0x28: "arm", 0xB7: "aarch64", 0x3E: "x86-64", 0x03: "x86", 0xF3: "riscv"}
_PE_MACHINES = {0x14C: "x86", 0x8664: "x86-64", 0xAA64: "aarch64", 0x1C0: "arm"}

_DWARF_SECS = (
    ".debug_info",
    ".debug_aranges",
    ".debug_abbrev",
    ".debug_frame",
    ".debug_str",
    ".debug_loc",
    ".debug_ranges",
    ".debug_line",
    ".debug_addr",
    ".debug_str_offsets",
    ".debug_line_str",
    ".debug_loclists",
    ".debug_rnglists",
    ".debug_types",
)


@dataclass
class BinInfo:
    fmt: str
    arch: str
    bits: int


def detect(path: Path) -> BinInfo | None:
    """Detect (format, arch, bits) of a linked binary, or None if unrecognized."""
    try:
        with open(path, "rb") as f:
            head = f.read(2)
            if head == b"\x7fE":
                f.seek(0)
                if f.read(4) != b"\x7fELF":
                    return None
                f.seek(18)
                arch = _ELF_MACHINES.get(struct.unpack("<H", f.read(2))[0], "other")
                bits = 64 if arch in ("x86-64", "aarch64") else 32
                return BinInfo("elf", arch, bits)
            if head == b"MZ":
                f.seek(0x3C)
                pe_off = struct.unpack("<I", f.read(4))[0]
                f.seek(pe_off)
                if f.read(4) != b"PE\x00\x00":
                    return None
                arch = _PE_MACHINES.get(struct.unpack("<H", f.read(2))[0], "other")
                bits = 64 if arch in ("x86-64", "aarch64") else 32
                return BinInfo("pe", arch, bits)
    except OSError:
        return None
    return None


def _build_dwarfinfo(secs: dict[str, bytes], little_endian: bool, addr_size: int, march: str):
    import io

    from elftools.dwarf.dwarfinfo import DebugSectionDescriptor, DwarfConfig, DWARFInfo

    def mk(name: str):
        data = secs.get(name)
        return DebugSectionDescriptor(io.BytesIO(data), name, None, len(data), 0) if data else None

    return DWARFInfo(
        config=DwarfConfig(
            little_endian=little_endian, default_address_size=addr_size, machine_arch=march
        ),
        debug_info_sec=mk(".debug_info"),
        debug_aranges_sec=mk(".debug_aranges"),
        debug_abbrev_sec=mk(".debug_abbrev"),
        debug_frame_sec=mk(".debug_frame"),
        eh_frame_sec=None,
        debug_str_sec=mk(".debug_str"),
        debug_loc_sec=mk(".debug_loc"),
        debug_ranges_sec=mk(".debug_ranges"),
        debug_line_sec=mk(".debug_line"),
        debug_addr_sec=mk(".debug_addr"),
        debug_str_offsets_sec=mk(".debug_str_offsets"),
        debug_line_str_sec=mk(".debug_line_str"),
        debug_pubtypes_sec=None,
        debug_pubnames_sec=None,
        debug_loclists_sec=mk(".debug_loclists"),
        debug_rnglists_sec=mk(".debug_rnglists"),
        debug_sup_sec=None,
        gnu_debugaltlink_sec=None,
        debug_types_sec=mk(".debug_types"),
    )


def pe_dwarf_info(path: Path):
    """Build a self-contained pyelftools DWARFInfo from a PE's DWARF sections.

    PE COFF truncates section names to 8 chars (``.debug_info`` -> a string-table
    ref like ``/29``), so the real names + file offsets come from ``objdump -h``.

    The MinGW cross objdump is preferred over a bare ``objdump`` in PATH: on
    macOS, ``/usr/bin/objdump`` is Apple's llvm-objdump, whose ``-h`` output
    has no File-off column (breaking the regex below) -- the MinGW-specific
    binary is guaranteed GNU-format for the PE/COFF corpus binaries this
    reads, regardless of host OS.
    """
    objdump = shutil.which("x86_64-w64-mingw32-objdump") or shutil.which("objdump")
    if objdump is None:
        return None
    out = subprocess.run([objdump, "-h", str(path)], capture_output=True, text=True).stdout
    secs: dict[str, bytes] = {}
    raw = Path(path).read_bytes()
    for line in out.splitlines():
        m = re.match(
            r"\s*\d+\s+(\.debug[\w.]*)\s+([0-9a-f]+)\s+[0-9a-f]+\s+[0-9a-f]+\s+([0-9a-f]+)", line
        )
        if m:
            name, size, foff = m.group(1), int(m.group(2), 16), int(m.group(3), 16)
            secs[name] = raw[foff : foff + size]
    if ".debug_info" not in secs:
        return None
    info = detect(path)
    addr_size = 8 if (info and info.bits == 64) else 4
    march = "x64" if addr_size == 8 else "x86"
    return _build_dwarfinfo(secs, little_endian=True, addr_size=addr_size, march=march)


def dwarf_info(path: Path):
    """Return a pyelftools DWARFInfo for an ELF or PE binary, or None."""
    info = detect(path)
    if info is None:
        return None
    if info.fmt == "pe":
        return pe_dwarf_info(path)
    try:
        from elftools.elf.elffile import ELFFile

        with open(path, "rb") as f:
            elf = ELFFile(f)
            if not elf.has_dwarf_info():
                return None
            secs = {}
            for name in _DWARF_SECS:
                s = elf.get_section_by_name(name)
                if s is not None:
                    secs[name] = s.data()
            if ".debug_info" not in secs:
                return None
            addr_size = 8 if info.bits == 64 else 4
            march = {"x86-64": "x64", "x86": "x86", "arm": "ARM", "aarch64": "AArch64"}.get(
                info.arch, "x64"
            )
            return _build_dwarfinfo(secs, elf.little_endian, addr_size, march)
    except Exception:
        return None


# ── Type normalization ──────────────────────────────────────────────────────

TYPE_MAP: dict[str, str] = {
    "undefined8": "long long",
    "undefined4": "int",
    "undefined2": "short",
    "undefined1": "char",
    "undefined": "char",
    "__int64": "long long",
    "__int32": "int",
    "__int16": "short",
    "__int8": "char",
    "_QWORD": "long long",
    "_DWORD": "int",
    "_WORD": "short",
    "_BYTE": "char",
    "_BOOL": "bool",
    "int1": "char",
    "int2": "short",
    "int4": "int",
    "int8": "long long",
    "uint1": "char",
    "uint2": "short",
    "uint4": "int",
    "uint8": "long long",
    "uint": "int",
    "ulong": "long long",
    "ulonglong": "long long",
    "longlong": "long long",
    "float80": "long double",
    "long": "long long",
    "ushort": "short",
    "uchar": "char",
    "uint64_t": "long long",
    "uint32_t": "int",
    "uint16_t": "short",
    "uint8_t": "char",
    "int64_t": "long long",
    "int32_t": "int",
    "int16_t": "short",
    "int8_t": "char",
    "size_t": "long long",
    "ssize_t": "long long",
}

QUALIFIERS = ["unsigned", "signed", "const", "volatile", "register", "static", "extern"]

# A trailing run of ``*``s, so TYPE_MAP can be applied to the POINTEE.
_PTR_SUFFIX = re.compile(r"^(.*?)((?:\s*\*)+)$")

# One C++ namespace/class qualifier, e.g. the ``leveldb::`` of
# ``leveldb::TableBuilder *``. Digits cannot start a token, so a Ghidra symbol
# version prefix like ``GLIBC_2.2.5::`` is left alone.
_NAMESPACE_QUALIFIER = re.compile(r"\b[A-Za-z_]\w*\s*::\s*")


def _map_pointee(form: str) -> str:
    """``TYPE_MAP`` applied through a pointer spelling: ``uchar *`` -> ``char*``.

    The scalar rows already normalize ``uchar``, but a pointer spelling never
    reached them, so a decompiler writing ``uchar *`` could not match DWARF's
    ``char*`` while one writing ``char *`` could.
    """
    m = _PTR_SUFFIX.match(form)
    if m is None:
        return form
    mapped = TYPE_MAP.get(m.group(1).strip())
    return form if mapped is None else mapped + m.group(2)


def _strip_namespaces(form: str) -> str:
    """``leveldb::TableBuilder*`` -> ``TableBuilder*``.

    DWARF records a C++ class/typedef under its UNQUALIFIED ``DW_AT_name``, so
    a decompiler printing the fully-qualified name could never match ground
    truth on a C++ target.
    """
    return _NAMESPACE_QUALIFIER.sub("", form).strip()


def normalize_type(type_str: str) -> set[str]:
    """Normalize a type string to a set of equivalent representations.

    Returns multiple possible forms so that any intersection counts as a match.
    """
    if not type_str:
        return set()

    t = type_str.strip()

    if t in TYPE_MAP:
        t = TYPE_MAP[t]

    forms = {t}

    normalized = t
    for q in QUALIFIERS:
        normalized = normalized.replace(f"{q} ", "")
    normalized = normalized.strip()
    if normalized:
        forms.add(normalized)

    for original, replacement in [
        ("long long int", "long long"),
        ("long int", "long long"),
        ("short int", "short"),
        ("_Bool", "bool"),
        ("Bool", "bool"),
        ("boolean", "bool"),
    ]:
        for form in list(forms):
            if original in form:
                forms.add(form.replace(original, replacement))

    forms = {re.sub(r"\s+", " ", f).strip() for f in forms if f.strip()}
    forms |= {re.sub(r"\s*\*", "*", f) for f in forms}
    forms |= {TYPE_MAP[f] for f in forms if f in TYPE_MAP}
    forms |= {_map_pointee(f) for f in forms}
    forms |= {_strip_namespaces(f) for f in forms}
    forms |= {re.sub(r"\s*\*", "*", f) for f in forms}
    forms = {f for f in forms if f.strip()}

    return forms


# Uncommitted types recover a variable's SIZE but not a committed C type.
# Matching one against a same-width ground-truth SCALAR is fair; against a
# pointer or aggregate it's a real miss.
_UNCOMMITTED_TYPES = re.compile(
    r"^\s*(?:"
    r"undefined\d*"
    r"|__u?int(?:8|16|32|64)"
    r"|_(?:BYTE|WORD|DWORD|QWORD)"
    r"|u?int[1-8]"
    r"|byte|word|dword|qword"
    r"|uchar"
    r")\s*$"
)
_UNCOMMITTED_WIDTH: dict[str, int] = {
    "undefined": 1,
    "undefined1": 1,
    "byte": 1,
    "uchar": 1,
    "_BYTE": 1,
    "int1": 1,
    "uint1": 1,
    "__int8": 1,
    "__uint8": 1,
    "undefined2": 2,
    "word": 2,
    "_WORD": 2,
    "int2": 2,
    "uint2": 2,
    "__int16": 2,
    "__uint16": 2,
    "undefined4": 4,
    "dword": 4,
    "_DWORD": 4,
    "int4": 4,
    "uint4": 4,
    "__int32": 4,
    "__uint32": 4,
    "undefined8": 8,
    "qword": 8,
    "_QWORD": 8,
    "int8": 8,
    "uint8": 8,
    "__int64": 8,
    "__uint64": 8,
}
_SIZE_SCALARS: dict[int, set[str]] = {
    1: {"char", "bool"},
    2: {"short"},
    4: {"int"},
    8: {"long long"},
}

# Ghidra/Fission encode a stack slot's frame offset in the NAME (local_10,
# var_10) when a structured offset isn't available.
_NAME_OFFSET = re.compile(r"^(?:local|var)_([0-9a-fA-F]+)$")


@dataclass
class VariableInfo:
    """Minimal decompiled-variable record -- name/type/position, regex-derived."""

    name: str
    type: str
    arg_index: int | None = None
    stack_offset: int | None = None
    size: int | None = None
    kind: str = ""


def _uncommitted_size(var: VariableInfo) -> int | None:
    """Byte width of an uncommitted (width-only) decompiler type, else None."""
    t = (var.type or "").strip()
    if "*" in t or not _UNCOMMITTED_TYPES.match(t):
        return None
    if var.size in _SIZE_SCALARS:
        return int(var.size)
    return _UNCOMMITTED_WIDTH.get(t)


def _effective_offset(var: VariableInfo) -> int | None:
    """Stack offset for a decompiled var, recovering it from local_/var_ names
    when stack_offset is unset."""
    if var.stack_offset is not None:
        return var.stack_offset
    m = _NAME_OFFSET.match(var.name or "")
    if m:
        return -int(m.group(1), 16)
    return None


# ── DWARF ground-truth extraction ───────────────────────────────────────────


def extract_ground_truth_types(binary_path: Path) -> dict[str, list[dict[str, Any]]]:
    """Extract ground truth variable types from DWARF debug info.

    Works for both ELF and PE binaries. Returns function_name -> list of
    variable dicts with name/type/rbp_offset/size/is_arg/arg_index.
    """
    result: dict[str, list[dict[str, Any]]] = {}

    try:
        dwarfinfo = dwarf_info(binary_path)
        if dwarfinfo is None:
            logger.debug("No DWARF info in %s", binary_path)
            return result

        for CU in dwarfinfo.iter_CUs():
            top_DIE = CU.get_top_DIE()
            for DIE in top_DIE.iter_children():
                if DIE.tag != "DW_TAG_subprogram":
                    continue
                func_name, variables = _parse_function_die(DIE, dwarfinfo)
                if func_name and variables:
                    result[func_name] = variables

    except Exception as e:
        logger.warning("Failed to extract DWARF types from %s: %s", binary_path, e)

    return result


def _parse_function_die(die: Any, dwarfinfo: Any) -> tuple[str | None, list[dict[str, Any]]]:
    if "DW_AT_name" not in die.attributes:
        return None, []

    func_name = die.attributes["DW_AT_name"].value.decode("utf-8", "replace")
    variables: list[dict[str, Any]] = []

    arg_index = 0
    for child in die.iter_children():
        if child.tag in ("DW_TAG_lexical_block", "DW_TAG_inlined_subroutine"):
            variables.extend(_parse_lexical_block(child, dwarfinfo))
        elif child.tag == "DW_TAG_formal_parameter":
            var = _parse_variable_die(child, dwarfinfo, is_arg=True, arg_index=arg_index)
            arg_index += 1
            if var:
                variables.append(var)
        elif child.tag == "DW_TAG_variable":
            var = _parse_variable_die(child, dwarfinfo)
            if var:
                variables.append(var)

    return func_name, variables


def _parse_lexical_block(die: Any, dwarfinfo: Any) -> list[dict[str, Any]]:
    variables: list[dict[str, Any]] = []
    for child in die.iter_children():
        if child.tag == "DW_TAG_lexical_block":
            variables.extend(_parse_lexical_block(child, dwarfinfo))
        elif child.tag in ("DW_TAG_formal_parameter", "DW_TAG_variable"):
            var = _parse_variable_die(child, dwarfinfo)
            if var:
                variables.append(var)
    return variables


def _parse_variable_die(
    die: Any,
    dwarfinfo: Any,
    is_arg: bool = False,
    arg_index: int | None = None,
) -> dict[str, Any] | None:
    """Parse a variable DIE. Variables with ANY DWARF location (stack OR
    register) are kept -- at -O2 most locals/args live in registers and have
    no stack offset, but still exist at runtime."""
    offsets, has_location = _get_location(die, dwarfinfo)
    if not has_location:
        return None

    if "DW_AT_abstract_origin" in die.attributes:
        try:
            attr = die.attributes["DW_AT_abstract_origin"]
            die = dwarfinfo.get_DIE_from_refaddr(attr.value + die.cu.cu_offset)
        except Exception:
            pass

    name = ""
    if "DW_AT_name" in die.attributes:
        name = die.attributes["DW_AT_name"].value.decode("utf-8", "replace")

    type_names: list[str] = []
    size = 0
    with contextlib.suppress(Exception):
        type_names, size = _parse_type_die(die, dwarfinfo)

    if not type_names:
        return None

    all_forms: set[str] = set()
    for t in type_names:
        all_forms.update(normalize_type(t))

    return {
        "name": name,
        "type": list(all_forms),
        "rbp_offset": list(set(offsets)),
        "size": size,
        "is_arg": is_arg,
        "arg_index": arg_index if is_arg else None,
    }


def _get_location(die: Any, dwarfinfo: Any) -> tuple[list[int], bool]:
    """(stack offsets from DW_OP_fbreg, whether the var has ANY location)."""
    from elftools.dwarf.dwarf_expr import DWARFExprParser

    offsets: list[int] = []
    has_location = False

    if "DW_AT_location" not in die.attributes:
        return offsets, has_location

    loc_attr = die.attributes["DW_AT_location"]
    expr_parser = DWARFExprParser(dwarfinfo.structs)

    try:
        if loc_attr.form == "DW_FORM_exprloc":
            ops = expr_parser.parse_expr(loc_attr.value)
            if ops:
                has_location = True
            for op in ops:
                if op.op_name == "DW_OP_fbreg":
                    offsets.append(op.args[0] + 16)

        elif loc_attr.form == "DW_FORM_sec_offset":
            loclists = dwarfinfo.location_lists()
            loclist = loclists.get_location_list_at_offset(loc_attr.value, die=die)

            for entry in loclist:
                expr = getattr(entry, "loc_expr", None) or getattr(entry, "location_expr", None)
                if expr is None:
                    continue
                ops = expr_parser.parse_expr(expr)
                if ops:
                    has_location = True
                if len(ops) != 1:
                    continue
                for op in ops:
                    if op.op_name == "DW_OP_fbreg":
                        offsets.append(op.args[0] + 16)
    except Exception:
        pass

    return offsets, has_location


def _parse_type_die(die: Any, dwarfinfo: Any) -> tuple[list[str], int]:
    if "DW_AT_type" not in die.attributes:
        return ["void"], 0

    attr = die.attributes["DW_AT_type"]
    type_offset = attr.value + die.cu.cu_offset
    type_die = dwarfinfo.get_DIE_from_refaddr(type_offset)
    tag = type_die.tag

    if tag == "DW_TAG_base_type":
        name = ""
        if "DW_AT_name" in type_die.attributes:
            name = type_die.attributes["DW_AT_name"].value.decode("utf-8", "replace")
        size = type_die.attributes.get("DW_AT_byte_size", None)
        size = size.value if size else 0
        return [name] if name else ["void"], size

    elif tag == "DW_TAG_typedef":
        names = []
        if "DW_AT_name" in type_die.attributes:
            names.append(type_die.attributes["DW_AT_name"].value.decode("utf-8", "replace"))
        child_names, size = _parse_type_die(type_die, dwarfinfo)
        names.extend(child_names)
        return names, size

    elif tag == "DW_TAG_pointer_type":
        child_names, _ = _parse_type_die(type_die, dwarfinfo)
        if not child_names:
            child_names = ["void"]
        ptr_names = [n + "*" for n in child_names]
        size = 8
        if "DW_AT_byte_size" in type_die.attributes:
            size = type_die.attributes["DW_AT_byte_size"].value
        return ptr_names, size

    elif tag == "DW_TAG_array_type":
        child_names, elem_size = _parse_type_die(type_die, dwarfinfo)
        dims = _get_array_dims(type_die)
        length = dims[0] if dims and dims[0] else 1
        arr_names = [f"{n}[{length}]" for n in child_names]
        return child_names + arr_names, elem_size * length

    elif tag in ("DW_TAG_const_type", "DW_TAG_volatile_type"):
        return _parse_type_die(type_die, dwarfinfo)

    elif tag == "DW_TAG_structure_type":
        names = []
        if "DW_AT_name" in type_die.attributes:
            names.append(type_die.attributes["DW_AT_name"].value.decode("utf-8", "replace"))
        if not names:
            names = ["struct"]
        size = 0
        if "DW_AT_byte_size" in type_die.attributes:
            size = type_die.attributes["DW_AT_byte_size"].value
        return names, size

    elif tag in ("DW_TAG_union_type", "DW_TAG_class_type"):
        names = []
        if "DW_AT_name" in type_die.attributes:
            names.append(type_die.attributes["DW_AT_name"].value.decode("utf-8", "replace"))
        if not names:
            names = ["union"]
        size = 0
        if "DW_AT_byte_size" in type_die.attributes:
            size = type_die.attributes["DW_AT_byte_size"].value
        return names, size

    elif tag == "DW_TAG_enumeration_type":
        names = []
        if "DW_AT_name" in type_die.attributes:
            names.append(type_die.attributes["DW_AT_name"].value.decode("utf-8", "replace"))
        names.append("int")
        size = 4
        if "DW_AT_byte_size" in type_die.attributes:
            size = type_die.attributes["DW_AT_byte_size"].value
        return names, size

    elif tag == "DW_TAG_subroutine_type":
        return ["FUNCTION"], 0

    return ["void"], 0


def _get_array_dims(die: Any) -> list[int | None]:
    dims: list[int | None] = []
    try:
        for sub in die.iter_children():
            if sub.tag == "DW_TAG_subrange_type":
                ub_attr = sub.attributes.get("DW_AT_upper_bound")
                lb_attr = sub.attributes.get("DW_AT_lower_bound")
                lb = lb_attr.value if lb_attr else 0
                ub = ub_attr.value if ub_attr else None
                count = ub - lb + 1 if ub is not None else None
                dims.append(count)
    except Exception:
        pass
    return dims


@functools.lru_cache(maxsize=1024)
def ground_truth_for_binary(binary_path: str) -> dict[str, list[dict[str, Any]]]:
    """Cached per-binary DWARF ground truth (many rows share one binary)."""
    return extract_ground_truth_types(Path(binary_path))


# ── Decompiled-code regex extraction ────────────────────────────────────────

_DECL_PATTERN = re.compile(
    r"^\s*"
    r"((?:(?:unsigned|signed|const|volatile|static|struct|union|enum)\s+)*"
    r"(?:(?:long\s+long|longlong|long|short|int|char|float|float80|double|void|bool|"
    r"__int\d+|_DWORD|_QWORD|_WORD|_BYTE|_BOOL|"
    r"u?int\d+_t|size_t|ssize_t|"
    r"undefined\d?|ulonglong|ulong|uint|ushort|uchar|"
    r"fission_agg\d*|"
    r"\w+_t)\s*\**)"
    r")"
    r"\s+"
    r"(\w+)"
    r"\s*(?:\[[^\]]*\])?"
    r"\s*(?:=[^;]*)?"
    r"\s*;",
    re.MULTILINE,
)

_DECL_SKIP = frozenset({"if", "else", "while", "for", "return", "switch", "case", "break"})


def _extract_local_decls(code: str) -> list[tuple[str, str]]:
    """(name, RAW type string) for each local declaration in ``code``."""
    out: list[tuple[str, str]] = []
    for match in _DECL_PATTERN.finditer(code):
        var_name = match.group(2).strip()
        if var_name in _DECL_SKIP:
            continue
        out.append((var_name, match.group(1).strip()))
    return out


def _split_top_level_commas(s: str) -> list[str]:
    """Split ``s`` on commas not nested inside (), [], or {}."""
    parts: list[str] = []
    depth = 0
    cur: list[str] = []
    for ch in s:
        if ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth = max(0, depth - 1)
        if ch == "," and depth == 0:
            parts.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    if cur:
        parts.append("".join(cur))
    return parts


def _find_definition_params(code: str, func_name: str) -> str | None:
    """Raw parameter-list text of ``func_name``'s DEFINITION, or None.

    The definition is the occurrence whose matching ``)`` is followed by
    ``{`` (a call or prototype ending in ``;`` is not).

    32-bit PE decorates cdecl symbols with a leading underscore, so a manifest
    naming ``list_sum`` must still find a definition printed ``_list_sum``.
    ``\b`` will not straddle that underscore -- it is a word character -- so the
    decorated spelling is tried as its own candidate.
    """
    if not func_name:
        return None
    candidates = [func_name]
    for alt in ("_" + func_name, func_name.lstrip("_")):
        if alt and alt not in candidates:
            candidates.append(alt)
    pattern = "|".join(re.escape(c) for c in candidates)
    for m in re.finditer(r"(?<![A-Za-z0-9])(?:" + pattern + r")\s*\(", code):
        open_i = code.index("(", m.start())
        depth = 0
        close_i: int | None = None
        for j in range(open_i, len(code)):
            c = code[j]
            if c == "(":
                depth += 1
            elif c == ")":
                depth -= 1
                if depth == 0:
                    close_i = j
                    break
        if close_i is None:
            continue
        if code[close_i + 1 :].lstrip().startswith("{"):
            return code[open_i + 1 : close_i]
    return None


def _parse_param(param: str) -> tuple[str, str] | None:
    """(name, RAW type) for one C parameter, or None for void/unnamed."""
    p = param.strip()
    if not p or p == "void":
        return None
    m = re.search(r"\(\s*\*+\s*(\w+)\s*(?:\[[^\]]*\])?\s*\)", p)
    if m:
        return m.group(1), (p[: m.start()] + "(*)" + p[m.end() :]).strip()
    p = re.sub(r"\[[^\]]*\]\s*$", "", p).strip()
    m = re.search(r"([A-Za-z_]\w*)\s*$", p)
    if not m:
        return None
    name = m.group(1)
    type_ = p[: m.start()].strip()
    if not type_:
        return None
    return name, type_


def parse_c_variables(code: str, func_name: str) -> list[VariableInfo]:
    """Best-effort ``VariableInfo`` list from decompiled C text.

    Recovers function arguments (ABI ``arg_index``, name-independent) from
    ``func_name``'s signature plus local declarations from the body.
    """
    out: list[VariableInfo] = []
    params = _find_definition_params(code, func_name)
    argnames: set[str] = set()
    if params is not None:
        for i, raw in enumerate(_split_top_level_commas(params)):
            parsed = _parse_param(raw)
            if parsed is None:
                token = raw.strip()
                if token and token != "void":
                    out.append(VariableInfo(name="", type=token, arg_index=i, kind="arg"))
                continue
            name, type_ = parsed
            argnames.add(name)
            out.append(VariableInfo(name=name, type=type_, arg_index=i, kind="arg"))
    for name, type_ in _extract_local_decls(code):
        if name in argnames:
            continue
        out.append(VariableInfo(name=name, type=type_, kind="stack"))
    return out


# ── Offset calibration ──────────────────────────────────────────────────────


def _candidate_shifts(gt_offsets: list[int], decomp_offsets: list[int]) -> list[int]:
    """Additive shifts worth testing to align decompiled to GT offsets."""
    candidates = {g - d for g in gt_offsets for d in decomp_offsets}
    candidates.add(0)
    return sorted(candidates, key=lambda x: (abs(x), x))


def _calibrate_shift(gt_offsets: list[int], decomp_offsets: list[int]) -> int | None:
    """Find an additive shift aligning decompiled offsets to GT offsets."""
    if not gt_offsets or not decomp_offsets:
        return None

    gt_set = set(gt_offsets)
    best_k: int | None = None
    best_count = 0
    for k in _candidate_shifts(gt_offsets, decomp_offsets):
        count = len({d + k for d in decomp_offsets} & gt_set)
        if count > best_count:
            best_count = count
            best_k = k

    if best_k is None or best_count == 0:
        return None

    if best_k != 0 and len(decomp_offsets) >= 2 and best_count < 2:
        zero_count = len(set(decomp_offsets) & gt_set)
        return 0 if zero_count >= 1 else None

    return best_k


def _calibrate_shift_multi(pairs: list[tuple[list[int], list[int]]]) -> int | None:
    """Calibrate one additive shift across many functions' offset sets.

    Each pair is (gt_offsets, decomp_offsets) for one function. A function
    votes with max(0, unique_matches - 1) so a lone coincidental alignment
    contributes nothing while multi-variable alignments accumulate.
    """
    pairs = [(g, d) for g, d in pairs if g and d]
    if not pairs:
        return None

    candidates = sorted(range(-32, 33), key=lambda x: (abs(x), x))

    def matches(gt_offs: list[int], dec_offs: list[int], k: int) -> int:
        return len({d + k for d in dec_offs} & set(gt_offs))

    best_k: int | None = None
    best_votes = 0
    for k in candidates:
        votes = sum(max(0, matches(g, d, k) - 1) for g, d in pairs)
        if votes > best_votes:
            best_votes = votes
            best_k = k

    if best_k is not None:
        return best_k

    for k in candidates:
        votes = sum(matches(g, d, k) for g, d in pairs)
        if votes > best_votes:
            best_votes = votes
            best_k = k

    if best_k is None or best_votes == 0:
        return None
    if best_k != 0:
        zero_votes = sum(matches(g, d, 0) for g, d in pairs)
        if zero_votes >= 1:
            return 0
        if best_votes < 2:
            return None
    return best_k


def calibrate_binary_shift(
    gt_types: dict[str, list[dict[str, Any]]],
    decompiled_by_function: dict[str, str],
) -> int | None:
    """Calibrate the offset shift across all functions of one binary+decompiler.

    ``decompiled_by_function`` maps function_name -> decompiled_code for
    every function decompiled from this binary in this batch.
    """
    pairs: list[tuple[list[int], list[int]]] = []
    for func_name, code in decompiled_by_function.items():
        gt_vars = gt_types.get(func_name, [])
        if not gt_vars or not code:
            continue
        func_gt = [o for gv in gt_vars for o in gv.get("rbp_offset", [])]
        func_dec = [
            o
            for o in (_effective_offset(v) for v in parse_c_variables(code, func_name))
            if o is not None
        ]
        if func_gt and func_dec:
            pairs.append((func_gt, func_dec))

    return _calibrate_shift_multi(pairs)


# ── Matching ─────────────────────────────────────────────────────────────────


def compute_type_match(
    ground_truth_vars: list[dict[str, Any]],
    decompiled_code: str,
    function_name: str,
    calibration_shift: int | None = None,
) -> dict[str, Any]:
    """Type match accuracy for one function: TP / (TP + FP + FN).

    - TP: decompiled variable at matching position/offset/name with matching type.
    - FP: matched position/offset/name but wrong type.
    - FN: ground-truth variable not found in the decompiled output.

    Matching proceeds in three passes, each decompiled variable credited at
    most once: (1) arguments by ABI position, (2) stack variables by
    calibrated offset, (3) everything else by exact name.
    """
    if not ground_truth_vars:
        return {"accuracy": 0.0, "tp": 0, "fp": 0, "fn": 0, "error": "no ground truth types"}

    variables = parse_c_variables(decompiled_code, function_name)
    if not variables:
        return {
            "accuracy": 0.0,
            "tp": 0,
            "fp": 0,
            "fn": len(ground_truth_vars),
            "gt_vars": len(ground_truth_vars),
            "decomp_vars": 0,
        }

    gt_offsets: list[int] = []
    for gv in ground_truth_vars:
        gt_offsets.extend(gv.get("rbp_offset", []))
    var_offsets: list[int | None] = [_effective_offset(v) for v in variables]
    decomp_offsets = [o for o in var_offsets if o is not None]
    gt_off_set = set(gt_offsets)

    def _aligned(kk: int | None) -> int:
        if kk is None or not decomp_offsets:
            return 0
        return len({d + kk for d in decomp_offsets} & gt_off_set)

    # IDA/Fission-style frame-bottom-relative offsets can need a per-function
    # override when the binary-wide shift doesn't align anything here.
    shift: int | None = calibration_shift if calibration_shift is not None else 0
    func_shift = _calibrate_shift(gt_offsets, decomp_offsets)
    if func_shift is not None and _aligned(shift) == 0 and _aligned(func_shift) > 0:
        shift = func_shift
    k = shift if shift is not None else 0

    var_types: list[set[str]] = [normalize_type(v.type) for v in variables]
    var_unc: list[int | None] = [_uncommitted_size(v) for v in variables]
    by_arg_index: dict[int, int] = {}
    by_off: dict[int, list[int]] = {}
    by_name: dict[str, list[int]] = {}
    for i, v in enumerate(variables):
        if v.arg_index is not None and v.arg_index not in by_arg_index:
            by_arg_index[v.arg_index] = i
        if var_offsets[i] is not None:
            by_off.setdefault(var_offsets[i] + k, []).append(i)
        if v.name:
            by_name.setdefault(v.name, []).append(i)

    def _matches(gt_forms: set[str], i: int) -> bool:
        if gt_forms & var_types[i]:
            return True
        sz = var_unc[i]
        return sz is not None and bool(_SIZE_SCALARS.get(sz, set()) & gt_forms)

    used: set[int] = set()

    def claim(candidates: list[int], gt_types: set[str]) -> bool | None:
        avail = [i for i in candidates if i not in used]
        if not avail:
            return None
        hit = next((i for i in avail if _matches(gt_types, i)), None)
        if hit is not None:
            used.add(hit)
            return True
        used.add(avail[0])
        return False

    n = len(ground_truth_vars)
    verdicts: list[bool | None] = [None] * n
    decided: list[bool] = [False] * n
    pass_counts = {"arg": 0, "offset": 0, "name": 0}

    for gi, gv in enumerate(ground_truth_vars):
        arg_index = gv.get("arg_index")
        if not gv.get("is_arg") or arg_index is None:
            continue
        di = by_arg_index.get(arg_index)
        if di is None or di in used:
            continue
        used.add(di)
        decided[gi] = True
        verdicts[gi] = _matches(set(gv.get("type", [])), di)
        pass_counts["arg"] += 1

    for gi, gv in enumerate(ground_truth_vars):
        if decided[gi]:
            continue
        candidates: list[int] = []
        for off in gv.get("rbp_offset", []):
            candidates.extend(by_off.get(off, []))
        if not candidates:
            continue
        verdict = claim(candidates, set(gv.get("type", [])))
        if verdict is not None:
            decided[gi] = True
            verdicts[gi] = verdict
            pass_counts["offset"] += 1

    for gi, gv in enumerate(ground_truth_vars):
        if decided[gi]:
            continue
        gt_name = gv.get("name", "")
        if not gt_name:
            continue
        verdict = claim(by_name.get(gt_name, []), set(gv.get("type", [])))
        if verdict is not None:
            decided[gi] = True
            verdicts[gi] = verdict
            pass_counts["name"] += 1

    tp = sum(1 for d, v in zip(decided, verdicts, strict=True) if d and v)
    fp = sum(1 for d, v in zip(decided, verdicts, strict=True) if d and not v)
    fn = sum(1 for d in decided if not d)
    total = tp + fp + fn
    accuracy = tp / total if total > 0 else 0.0

    return {
        "accuracy": accuracy,
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "gt_vars": len(ground_truth_vars),
        "decomp_vars": len(variables),
        "calibration_shift": shift,
        "matched_by_arg": pass_counts["arg"],
        "matched_by_offset": pass_counts["offset"],
        "matched_by_name": pass_counts["name"],
    }
