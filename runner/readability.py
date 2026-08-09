"""Readability proxy metrics for decompiled C output.

These metrics are intentionally stored as raw/normalized proxy values, not as a
final readability score. The final composite must wait for the human validation
study described in benchmark/readability/.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

from pycparser import c_ast, c_parser
from zss import Node as ZssNode
from zss import simple_distance


TYPE_PREAMBLE = """
typedef unsigned char undefined;
typedef unsigned char undefined1;
typedef unsigned short undefined2;
typedef unsigned int undefined4;
typedef unsigned long long undefined8;
typedef unsigned char byte;
typedef unsigned short word;
typedef unsigned int dword;
typedef unsigned long long qword;
typedef unsigned char uchar;
typedef unsigned short ushort;
typedef unsigned int uint;
typedef unsigned long ulong;
typedef unsigned long long ulonglong;
typedef unsigned char uint8_t;
typedef unsigned short uint16_t;
typedef unsigned int uint32_t;
typedef unsigned long long uint64_t;
typedef signed char int8_t;
typedef signed short int16_t;
typedef signed int int32_t;
typedef signed long long int64_t;
typedef unsigned long size_t;
typedef int bool;
"""


GENERIC_IDENTIFIER_PATTERNS: dict[str, list[str]] = {
    "default": [
        r"^v\d+$",
        r"^var_\w+$",
        r"^tmp\d*$",
        r"^temp\d*$",
        r"^param_\d+$",
        r"^arg\d+$",
        r"^result\d*$",
    ],
    "fission": [
        r"^v\d+$",
        r"^tmp\d*$",
        r"^var_\w+$",
        r"^arg\d+$",
        r"^local_\w+$",
    ],
    "ghidra": [
        r"^undefined\d*$",
        r"^uVar\d+$",
        r"^iVar\d+$",
        r"^bVar\d+$",
        r"^cVar\d+$",
        r"^lVar\d+$",
        r"^local_[0-9a-fA-F]+$",
        r"^param_\d+$",
        r"^in_[A-Z0-9_]+$",
        r"^unaff_[A-Z0-9_]+$",
    ],
    "boomerang": [
        r"^local\d+$",
        r"^param\d+$",
        r"^tmp\d*$",
        r"^v\d+$",
    ],
    "radare2": [
        r"^var_\w+$",
        r"^arg_\w+$",
        r"^local_\w+$",
    ],
    "angr": [
        r"^v\d+$",
        r"^tmp\d*$",
        r"^var_\w+$",
    ],
    "snowman": [
        r"^v\d+$",
        r"^a\d+$",
        r"^tmp\d*$",
    ],
    "revng": [
        r"^var_\w+$",
        r"^local_\w+$",
        r"^tmp\d*$",
    ],
    "reko": [
        r"^v\d+$",
        r"^r\d+$",
        r"^tmp\d*$",
    ],
}

RAW_WIDTH_TYPES = {
    "char",
    "short",
    "int",
    "long",
    "signed",
    "unsigned",
    "float",
    "double",
    "void",
    "bool",
    "byte",
    "word",
    "dword",
    "qword",
    "uchar",
    "ushort",
    "uint",
    "ulong",
    "ulonglong",
    "size_t",
    "uint8_t",
    "uint16_t",
    "uint32_t",
    "uint64_t",
    "int8_t",
    "int16_t",
    "int32_t",
    "int64_t",
}

COLLAPSED_TYPE_PATTERNS = [
    re.compile(r"^undefined\d*$", re.IGNORECASE),
    re.compile(r"^unknown\d*$", re.IGNORECASE),
    re.compile(r"^conflict", re.IGNORECASE),
    re.compile(r"^unk", re.IGNORECASE),
]

UNRESOLVED_ARTIFACT_PATTERNS: dict[str, str] = {
    "sleigh_intrinsic": r"\b__(?:carry|scarry|sborrow|borrow|overflow|popcount|parity)\b",
    "word_macro": r"\b(?:LOW|HIGH|LO|HI)(?:WORD|DWORD|BYTE)\b",
    "register_name": r"\b(?:in_|unaff_)?(?:RAX|RBX|RCX|RDX|RSI|RDI|RSP|RBP|EAX|EBX|ECX|EDX|ESI|EDI|ESP|EBP|AL|AH|BL|BH|CL|CH|DL|DH)\b",
    "collapsed_type": r"\b(?:undefined\d*|unknown\d*|UNK_TYPE|BADSPACEBASE)\b",
}


@dataclass(frozen=True)
class ParsedC:
    ast: c_ast.FileAST | None
    parse_error: str | None
    sanitized: str


def _strip_comments(code: str) -> str:
    code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)
    return re.sub(r"//[^\n]*", "", code)


def _sanitize_for_parse(code: str) -> str:
    code = _strip_comments(code)
    code = "\n".join(line for line in code.splitlines() if not line.lstrip().startswith("#"))
    code = re.sub(r"\b__attribute__\s*\(\([^)]*\)\)", "", code)
    code = re.sub(r"\b__declspec\s*\([^)]*\)", "", code)
    code = re.sub(r"\b(register|__cdecl|__stdcall|__fastcall|__thiscall)\b", "", code)
    code = code.replace("__restrict", "").replace("restrict", "")
    return code.strip()


def parse_c(code: str) -> ParsedC:
    sanitized = _sanitize_for_parse(code)
    if not sanitized:
        return ParsedC(None, "empty input", sanitized)
    try:
        return ParsedC(c_parser.CParser().parse(TYPE_PREAMBLE + "\n" + sanitized), None, sanitized)
    except Exception as exc:
        return ParsedC(None, str(exc), sanitized)


class IdentifierCollector(c_ast.NodeVisitor):
    def __init__(self) -> None:
        self.names: list[str] = []

    def visit_ID(self, node: c_ast.ID) -> None:
        self.names.append(node.name)

    def visit_Decl(self, node: c_ast.Decl) -> None:
        if node.name:
            self.names.append(node.name)
        self.generic_visit(node)

    def visit_FuncCall(self, node: c_ast.FuncCall) -> None:
        if isinstance(node.name, c_ast.ID):
            self.names.append(node.name.name)
        self.generic_visit(node)


class TypeCollector(c_ast.NodeVisitor):
    def __init__(self) -> None:
        self.nodes: list[c_ast.Node] = []

    def visit_Decl(self, node: c_ast.Decl) -> None:
        self.nodes.append(node.type)
        self.generic_visit(node)

    def visit_Typename(self, node: c_ast.Typename) -> None:
        self.nodes.append(node.type)
        self.generic_visit(node)


class ExpressionCollector(c_ast.NodeVisitor):
    def __init__(self) -> None:
        self.operator_count = 0
        self.expression_depths: list[int] = []
        self.max_cast_depth = 0
        self.ternary_count = 0
        self.comma_count = 0

    def visit_BinaryOp(self, node: c_ast.BinaryOp) -> None:
        self.operator_count += 1
        if node.op == ",":
            self.comma_count += 1
        self.expression_depths.append(_expr_depth(node))
        self.generic_visit(node)

    def visit_UnaryOp(self, node: c_ast.UnaryOp) -> None:
        self.operator_count += 1
        self.expression_depths.append(_expr_depth(node))
        self.generic_visit(node)

    def visit_Assignment(self, node: c_ast.Assignment) -> None:
        self.operator_count += 1
        self.expression_depths.append(_expr_depth(node))
        self.generic_visit(node)

    def visit_TernaryOp(self, node: c_ast.TernaryOp) -> None:
        self.operator_count += 1
        self.ternary_count += 1
        self.expression_depths.append(_expr_depth(node))
        self.generic_visit(node)

    def visit_Cast(self, node: c_ast.Cast) -> None:
        self.operator_count += 1
        self.max_cast_depth = max(self.max_cast_depth, _cast_depth(node))
        self.expression_depths.append(_expr_depth(node))
        self.generic_visit(node)


class ControlFlowCollector(c_ast.NodeVisitor):
    def __init__(self) -> None:
        self.structured = 0
        self.unstructured = 0
        self.state_flags = 0
        self.switch_count = 0

    def visit_If(self, node: c_ast.If) -> None:
        self.structured += 1
        self.generic_visit(node)

    def visit_For(self, node: c_ast.For) -> None:
        self.structured += 1
        self.generic_visit(node)

    def visit_While(self, node: c_ast.While) -> None:
        self.structured += 1
        self.generic_visit(node)

    def visit_DoWhile(self, node: c_ast.DoWhile) -> None:
        self.structured += 1
        self.generic_visit(node)

    def visit_Switch(self, node: c_ast.Switch) -> None:
        self.structured += 1
        self.switch_count += 1
        self.generic_visit(node)

    def visit_Goto(self, node: c_ast.Goto) -> None:
        self.unstructured += 1

    def visit_Decl(self, node: c_ast.Decl) -> None:
        if node.name and re.search(r"(state|flag|done|next|loop|again)", node.name, re.IGNORECASE):
            self.state_flags += 1
        self.generic_visit(node)


def _expr_depth(node: c_ast.Node | None) -> int:
    if node is None:
        return 0
    child_depths = [_expr_depth(child) for _, child in node.children()]
    return 1 + (max(child_depths) if child_depths else 0)


def _cast_depth(node: c_ast.Node | None) -> int:
    if isinstance(node, c_ast.Cast):
        return 1 + _cast_depth(node.expr)
    if node is None:
        return 0
    child_depths = [_cast_depth(child) for _, child in node.children()]
    return max(child_depths) if child_depths else 0


def _type_names(node: c_ast.Node) -> list[str]:
    if isinstance(node, c_ast.IdentifierType):
        return node.names
    names: list[str] = []
    for _, child in node.children():
        names.extend(_type_names(child))
    return names


def _type_score(node: c_ast.Node) -> float:
    if isinstance(node, (c_ast.Struct, c_ast.Enum)):
        return 1.0
    if isinstance(node, c_ast.PtrDecl) and isinstance(node.type, c_ast.FuncDecl):
        return 1.0

    names = _type_names(node)
    if not names:
        return 0.0

    joined = " ".join(names)
    if any(pattern.match(name) for name in names for pattern in COLLAPSED_TYPE_PATTERNS):
        return 0.0
    if all(name in RAW_WIDTH_TYPES for name in names):
        return 0.5
    if joined in RAW_WIDTH_TYPES:
        return 0.5
    return 1.0


def _compiled_generic_patterns(decompiler: str) -> list[re.Pattern[str]]:
    patterns = GENERIC_IDENTIFIER_PATTERNS["default"] + GENERIC_IDENTIFIER_PATTERNS.get(
        decompiler,
        [],
    )
    return [re.compile(pattern) for pattern in patterns]


def generic_naming_ratio(ast: c_ast.FileAST | None, decompiler: str) -> dict[str, Any]:
    if ast is None:
        return {"raw": {"generic": 0, "total": 0, "ratio": 1.0}, "normalized": 0.0}

    collector = IdentifierCollector()
    collector.visit(ast)
    names = [name for name in collector.names if not name.startswith("__")]
    patterns = _compiled_generic_patterns(decompiler)
    generic = sum(1 for name in names if any(pattern.match(name) for pattern in patterns))
    total = len(names)
    ratio = generic / total if total else 1.0
    return {
        "raw": {"generic": generic, "total": total, "ratio": round(ratio, 4)},
        "normalized": round(1.0 - ratio, 4),
    }


def type_specificity_score(ast: c_ast.FileAST | None) -> dict[str, Any]:
    if ast is None:
        return {"raw": {"average": 0.0, "typed_nodes": 0}, "normalized": 0.0}

    collector = TypeCollector()
    collector.visit(ast)
    scores = [_type_score(node) for node in collector.nodes]
    average = sum(scores) / len(scores) if scores else 0.0
    return {
        "raw": {"average": round(average, 4), "typed_nodes": len(scores)},
        "normalized": round(average, 4),
    }


def _temporary_identifier_count(ast: c_ast.FileAST | None, decompiler: str) -> int:
    if ast is None:
        return 0
    collector = IdentifierCollector()
    collector.visit(ast)
    tmp_patterns = [
        re.compile(r"^tmp\d*$"),
        re.compile(r"^temp\d*$"),
        re.compile(r"^local_[0-9a-fA-F]+$"),
        re.compile(r"^uVar\d+$"),
        re.compile(r"^iVar\d+$"),
        *_compiled_generic_patterns(decompiler),
    ]
    return sum(1 for name in collector.names if any(pattern.match(name) for pattern in tmp_patterns))


def expression_complexity(ast: c_ast.FileAST | None, code: str, decompiler: str) -> dict[str, Any]:
    if ast is None:
        return {
            "raw": {
                "operator_count": 0,
                "avg_expression_depth": 0.0,
                "max_cast_depth": 0,
                "ternary_count": 0,
                "comma_count": 0,
                "temporary_identifier_count": 0,
                "loc": _logical_loc(code),
                "temporary_identifier_loc_ratio": 0.0,
            },
            "normalized": 0.0,
        }

    collector = ExpressionCollector()
    collector.visit(ast)
    loc = _logical_loc(code)
    tmp_count = _temporary_identifier_count(ast, decompiler)
    avg_depth = (
        sum(collector.expression_depths) / len(collector.expression_depths)
        if collector.expression_depths
        else 0.0
    )
    tmp_loc_ratio = tmp_count / loc if loc else 0.0
    complexity = (
        min(collector.operator_count / 40.0, 1.0) * 0.25
        + min(avg_depth / 8.0, 1.0) * 0.25
        + min(collector.max_cast_depth / 4.0, 1.0) * 0.15
        + min((collector.ternary_count + collector.comma_count) / 5.0, 1.0) * 0.15
        + min(tmp_loc_ratio / 2.0, 1.0) * 0.20
    )
    return {
        "raw": {
            "operator_count": collector.operator_count,
            "avg_expression_depth": round(avg_depth, 4),
            "max_cast_depth": collector.max_cast_depth,
            "ternary_count": collector.ternary_count,
            "comma_count": collector.comma_count,
            "temporary_identifier_count": tmp_count,
            "loc": loc,
            "temporary_identifier_loc_ratio": round(tmp_loc_ratio, 4),
        },
        "normalized": round(1.0 - complexity, 4),
    }


def _logical_loc(code: str) -> int:
    clean = _strip_comments(code)
    return sum(1 for line in clean.splitlines() if line.strip())


def structured_control_flow_ratio(ast: c_ast.FileAST | None, code: str) -> dict[str, Any]:
    goto_count = len(re.findall(r"\bgoto\b", code))
    nesting_depth = _brace_depth(code)
    irreducible_loop = bool(re.search(r"\bgoto\b[\s\S]{0,200}\b(label|LAB_)", code))

    if ast is None:
        structured = 0
        state_flags = len(re.findall(r"\b(?:state|flag|done|next|loop|again)\w*\b", code))
    else:
        collector = ControlFlowCollector()
        collector.visit(ast)
        structured = collector.structured
        state_flags = collector.state_flags
        goto_count = max(goto_count, collector.unstructured)

    total = structured + goto_count + state_flags
    structured_ratio = structured / total if total else 1.0
    normalized = structured_ratio
    if irreducible_loop:
        normalized *= 0.75
    normalized *= max(0.0, 1.0 - min(state_flags / 8.0, 1.0) * 0.25)
    return {
        "raw": {
            "structured_constructs": structured,
            "goto_count": goto_count,
            "nesting_depth": nesting_depth,
            "irreducible_loop_suspected": irreducible_loop,
            "state_flag_count": state_flags,
            "structured_ratio": round(structured_ratio, 4),
        },
        "normalized": round(normalized, 4),
    }


def _brace_depth(code: str) -> int:
    depth = 0
    max_depth = 0
    for ch in code:
        if ch == "{":
            depth += 1
            max_depth = max(max_depth, depth)
        elif ch == "}":
            depth = max(0, depth - 1)
    return max_depth


def unresolved_artifact_count(code: str) -> dict[str, Any]:
    details = {
        name: len(re.findall(pattern, code))
        for name, pattern in UNRESOLVED_ARTIFACT_PATTERNS.items()
    }
    total = sum(details.values())
    return {
        "raw": {"total": total, "details": details},
        "normalized": round(1.0 - min(total / 12.0, 1.0), 4),
    }


def summarize_readability_proxy_score(metrics: dict[str, Any]) -> float | None:
    """Unvalidated 0-1 readability proxy summary; never used for correctness ranking."""
    if not metrics:
        return None

    values = [
        metrics.get("generic_naming_ratio", {}).get("normalized"),
        metrics.get("type_specificity", {}).get("normalized"),
        metrics.get("expression_complexity", {}).get("normalized"),
        metrics.get("structured_control_flow", {}).get("normalized"),
        metrics.get("unresolved_artifacts", {}).get("normalized"),
    ]
    numeric = [float(value) for value in values if isinstance(value, (int, float))]
    if not numeric:
        return None
    return round(sum(numeric) / len(numeric), 4)


def compare_readability_layers(
    code_nir: str,
    code_hir: str,
    metrics_nir: dict[str, Any],
    metrics_hir: dict[str, Any],
) -> dict[str, Any]:
    """Record factual NIR/HIR deltas without declaring either surface better."""

    if not code_nir or not code_hir:
        return {
            "available": False,
            "text_differs": False,
            "reason": "missing_nir_or_hir",
        }

    def raw(metrics: dict[str, Any], family: str, key: str) -> int:
        value = metrics.get(family, {}).get("raw", {}).get(key, 0)
        return int(value) if isinstance(value, (int, float)) else 0

    nir = {
        "bytes": len(code_nir.encode("utf-8")),
        "loc": raw(metrics_nir, "expression_complexity", "loc"),
        "goto_count": raw(metrics_nir, "structured_control_flow", "goto_count"),
        "nesting_depth": raw(
            metrics_nir, "structured_control_flow", "nesting_depth"
        ),
        "temporary_identifiers": raw(
            metrics_nir, "expression_complexity", "temporary_identifier_count"
        ),
        "generic_identifiers": raw(
            metrics_nir, "generic_naming_ratio", "generic"
        ),
        "proxy_score": summarize_readability_proxy_score(metrics_nir),
    }
    hir = {
        "bytes": len(code_hir.encode("utf-8")),
        "loc": raw(metrics_hir, "expression_complexity", "loc"),
        "goto_count": raw(metrics_hir, "structured_control_flow", "goto_count"),
        "nesting_depth": raw(
            metrics_hir, "structured_control_flow", "nesting_depth"
        ),
        "temporary_identifiers": raw(
            metrics_hir, "expression_complexity", "temporary_identifier_count"
        ),
        "generic_identifiers": raw(
            metrics_hir, "generic_naming_ratio", "generic"
        ),
        "proxy_score": summarize_readability_proxy_score(metrics_hir),
    }
    integer_fields = (
        "bytes",
        "loc",
        "goto_count",
        "nesting_depth",
        "temporary_identifiers",
        "generic_identifiers",
    )
    delta: dict[str, int | float | None] = {
        field: hir[field] - nir[field] for field in integer_fields
    }
    nir_score = nir["proxy_score"]
    hir_score = hir["proxy_score"]
    delta["proxy_score"] = (
        round(hir_score - nir_score, 4)
        if isinstance(nir_score, float) and isinstance(hir_score, float)
        else None
    )
    return {
        "available": True,
        "text_differs": code_nir.strip() != code_hir.strip(),
        "interpretation": "hir_minus_nir",
        "validated_against_humans": False,
        "nir": nir,
        "hir": hir,
        "delta": delta,
    }


def analyze_readability(code: str, decompiler: str) -> dict[str, Any]:
    parsed = parse_c(code)
    return {
        "validated_against_humans": False,
        "composite_score": None,
        "parse_ok": parsed.ast is not None,
        "parse_error": parsed.parse_error,
        "generic_naming_ratio": generic_naming_ratio(parsed.ast, decompiler),
        "type_specificity": type_specificity_score(parsed.ast),
        "expression_complexity": expression_complexity(parsed.ast, parsed.sanitized, decompiler),
        "structured_control_flow": structured_control_flow_ratio(parsed.ast, parsed.sanitized),
        "unresolved_artifacts": unresolved_artifact_count(code),
    }


def ast_structure_similarity(source: str, decompiled: str) -> dict[str, Any]:
    src = parse_c(source)
    dec = parse_c(decompiled)
    if src.ast is None or dec.ast is None:
        return {
            "available": False,
            "algorithm": "zhang_shasha",
            "error": src.parse_error or dec.parse_error,
            "identifier_placeholder": None,
            "type_erased": None,
            "control_flow_normalized": None,
        }

    return {
        "available": True,
        "algorithm": "zhang_shasha",
        "identifier_placeholder": _normalized_tree_similarity(src.ast, dec.ast, "identifier"),
        "type_erased": _normalized_tree_similarity(src.ast, dec.ast, "type_erased"),
        "control_flow_normalized": _normalized_tree_similarity(src.ast, dec.ast, "control_flow"),
    }


def _normalized_tree_similarity(
    src_ast: c_ast.FileAST,
    dec_ast: c_ast.FileAST,
    mode: str,
) -> dict[str, Any]:
    left = _to_zss(src_ast, mode)
    right = _to_zss(dec_ast, mode)
    distance = simple_distance(left, right)
    size = max(_tree_size(left), _tree_size(right), 1)
    normalized_distance = min(distance / size, 1.0)
    return {
        "raw_distance": int(distance) if float(distance).is_integer() else round(distance, 4),
        "normalized_distance": round(normalized_distance, 4),
        "similarity": round(1.0 - normalized_distance, 4),
    }


def _to_zss(node: c_ast.Node, mode: str) -> ZssNode:
    label = _node_label(node, mode)
    znode = ZssNode(label)
    for _, child in node.children():
        znode.addkid(_to_zss(child, mode))
    return znode


def _node_label(node: c_ast.Node, mode: str) -> str:
    if mode == "identifier":
        if isinstance(node, c_ast.ID):
            return "ID"
        if isinstance(node, c_ast.Decl):
            return "Decl"
    if mode == "type_erased" and isinstance(
        node,
        (c_ast.TypeDecl, c_ast.IdentifierType, c_ast.PtrDecl, c_ast.Typename),
    ):
        return type(node).__name__
    if mode == "control_flow" and isinstance(
        node,
        (c_ast.For, c_ast.While, c_ast.DoWhile),
    ):
        return "Loop"
    if mode == "control_flow" and isinstance(node, (c_ast.Case, c_ast.Default)):
        return "SwitchArm"

    parts = [type(node).__name__]
    for attr in ("op", "name"):
        value = getattr(node, attr, None)
        if value and mode not in {"identifier", "type_erased"}:
            parts.append(str(value))
    return ":".join(parts)


def _tree_size(node: ZssNode) -> int:
    return 1 + sum(_tree_size(child) for child in node.children)


def geometric_mean(values: list[float]) -> float:
    if not values:
        return 0.0
    clipped = [max(min(value, 1.0), 0.0001) for value in values]
    return round(math.prod(clipped) ** (1 / len(clipped)), 4)
