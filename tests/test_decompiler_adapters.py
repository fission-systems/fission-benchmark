from __future__ import annotations

import importlib.util
import subprocess
import sys
import threading
import types
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.remove(str(path.parent))
    return module


def test_fission_uses_addresses_file_batch_cli() -> None:
    server = load_module("fission_server", ROOT / "docker/fission/server.py")

    # Simulate a modern CLI that supports --layer (capability probe can't run
    # in CI without a real fission binary — force the cache directly).
    server._CAPABILITY_CACHE["--layer"] = True
    server._CAPABILITY_PROBED = True

    command = server.decompile_batch_command("/tmp/target.bin", "/tmp/addrs.txt")

    assert command[:3] == ["/usr/local/bin/fission_cli", "decomp", "/tmp/target.bin"]
    assert "--addresses-file" in command
    assert "/tmp/addrs.txt" in command
    assert "--batch" not in command
    assert "--json" in command
    assert "--layer" in command
    assert command[command.index("--layer") + 1] == "nir"


def test_fission_requests_complete_sleigh_validated_function_inventory() -> None:
    server = load_module("fission_server_inventory", ROOT / "docker/fission/server.py")
    server._LIST_CAPABILITY_CACHE.update(
        {
            "--function-discovery-profile": True,
            "--include-nonuser-functions": True,
        }
    )
    server._LIST_CAPABILITY_PROBED = True

    command = server.function_inventory_command("/tmp/target.bin")

    assert command == [
        "list",
        "/tmp/target.bin",
        "--function-discovery-profile",
        "conservative",
        "--include-nonuser-functions",
        "--json",
    ]


def test_fission_function_inventory_falls_back_for_older_cli() -> None:
    server = load_module("fission_server_inventory_fallback", ROOT / "docker/fission/server.py")
    server._LIST_CAPABILITY_CACHE.update(
        {
            "--function-discovery-profile": False,
            "--include-nonuser-functions": False,
        }
    )
    server._LIST_CAPABILITY_PROBED = True

    assert server.function_inventory_command("/tmp/target.bin") == [
        "list",
        "/tmp/target.bin",
        "--json",
    ]


def test_fission_function_inventory_capability_probe_is_atomic(monkeypatch) -> None:
    server = load_module("fission_server_inventory_atomic", ROOT / "docker/fission/server.py")
    entered = threading.Event()
    release = threading.Event()
    calls = 0

    def fake_run(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        entered.set()
        assert release.wait(timeout=2)
        return types.SimpleNamespace(
            stdout="--function-discovery-profile --include-nonuser-functions",
            stderr="",
            returncode=0,
        )

    monkeypatch.setattr(server.subprocess, "run", fake_run)
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(server.supports_list, "--function-discovery-profile")
        assert entered.wait(timeout=2)
        second = pool.submit(server.supports_list, "--include-nonuser-functions")
        release.set()

    assert first.result() is True
    assert second.result() is True
    assert calls == 1


def test_fission_function_endpoint_normalizes_internal_provenance_kind(monkeypatch) -> None:
    server = load_module("fission_server_inventory_kind", ROOT / "docker/fission/server.py")
    monkeypatch.setattr(server, "resolve_binary", lambda _binary: "/tmp/target.bin")
    monkeypatch.setattr(server, "_binary_fingerprint", lambda _path: "fixture")
    monkeypatch.setattr(
        server,
        "run_fission_cli",
        lambda _command: [
            {
                "address": "0x401000",
                "name": "validated_thunk",
                "size": 6,
                "kind": "validated_symbol",
            }
        ],
    )

    assert server.functions("target.bin") == [
        {
            "address": "0x401000",
            "name": "validated_thunk",
            "size": 6,
            "kind": "function",
        }
    ]


def test_fission_normalizes_new_batch_json_shape() -> None:
    server = load_module("fission_server_shape", ROOT / "docker/fission/server.py")

    payload = {
        "_meta": {"function_count": 1},
        "functions": [{"address": "0x4015b0", "name": "_fibonacci", "code": "int x;"}],
    }

    assert server.normalize_decompile_results(payload) == [
        {"address": "0x4015b0", "name": "_fibonacci", "code": "int x;"}
    ]


def test_fission_maps_dual_layer_cli_fields() -> None:
    server = load_module("fission_server_dual", ROOT / "docker/fission/server.py")

    item = server.decompile_result_from_cli_item(
        {
            "address": "0x14000158c",
            "name": "signum",
            "code": "int signum(int x) { ulonglong home_0; return x; }",
            "code_nir": "int signum(int x) { ulonglong home_0; return x; }",
            "code_hir": "int signum(int x) { return x; }",
            "layer": "nir",
        }
    )

    assert item.addr == "0x14000158c"
    assert item.name == "signum"
    assert "home_0" in item.code
    assert item.code_nir and "home_0" in item.code_nir
    assert item.code_hir and "home_0" not in item.code_hir
    assert item.layer == "nir"


def test_fission_dual_layer_falls_back_when_only_code_present() -> None:
    server = load_module("fission_server_dual_fallback", ROOT / "docker/fission/server.py")

    item = server.decompile_result_from_cli_item(
        {"address": "0x1", "name": "f", "code": "int f(void) { return 1; }"}
    )

    assert item.code == "int f(void) { return 1; }"
    assert item.code_nir == item.code
    assert item.code_hir == item.code


def test_fission_type_contract_preserves_recovered_signature_types(monkeypatch) -> None:
    server = load_module("fission_server_types", ROOT / "docker/fission/server.py")
    monkeypatch.setattr(
        server,
        "_abi_impl",
        lambda _path, _addr: {
            "status": "ok",
            "name": "list_sum",
            "parameters": [
                {"index": 0, "name": "param_1", "location": "rcx", "size": 8}
            ],
            "return": {"type": "ulonglong", "location": "rax", "size": 8},
        },
    )
    monkeypatch.setattr(
        server,
        "run_fission_cli",
        lambda _command: [
            {
                "name": "list_sum",
                "code": "ulonglong list_sum(int * param_1)\n{\n    return *param_1;\n}",
            }
        ],
    )

    payload = server._types_impl("/missing/type-contract.bin", "0x1000")

    assert payload["return_type"] == "ulonglong"
    assert payload["parameters"] == [
        {"index": 0, "name": "param_1", "type": "int *", "size": 8}
    ]
    assert payload["structs"] == []
    assert payload["source"] == "decomp_signature"


def test_fission_signature_parser_keeps_function_pointer_parameter_together() -> None:
    server = load_module("fission_server_signature", ROOT / "docker/fission/server.py")

    ret, params = server._parse_c_signature(
        "int apply_binop(int (*callback)(int, int), int lhs, unsigned int rhs)\n{"
    )

    assert ret == "int"
    assert params == [
        {"index": 0, "name": "callback", "type": "int (*)(int, int)"},
        {"index": 1, "name": "lhs", "type": "int"},
        {"index": 2, "name": "rhs", "type": "unsigned int"},
    ]


def test_fission_type_contract_extracts_emitted_aggregate_layout(monkeypatch) -> None:
    server = load_module("fission_server_aggregate_types", ROOT / "docker/fission/server.py")
    monkeypatch.setattr(
        server,
        "_abi_impl",
        lambda _path, _addr: {
            "status": "ok",
            "name": "list_sum",
            "parameters": [{"index": 0, "location": "rcx", "size": 8}],
            "return": {"type": "ulonglong", "location": "rax", "size": 8},
        },
    )
    monkeypatch.setattr(
        server,
        "run_fission_cli",
        lambda _command: [
            {
                "name": "list_sum",
                "code": """typedef struct fission_agg16 {
    uint field_0;
    unsigned char _pad_4[4];
    ulonglong field_8;
} fission_agg16;

ulonglong list_sum(fission_agg16 * param_1) { return 0; }
""",
            }
        ],
    )

    payload = server._types_impl("/missing/aggregate-contract.bin", "0x1000")

    assert payload["structs"] == [
        {
            "name": "fission_agg16",
            "size": 16,
            "fields": [
                {"name": "field_0", "offset": 0, "size": 4, "type": "uint"},
                {"name": "field_8", "offset": 8, "size": 8, "type": "ulonglong"},
            ],
        }
    ]
    assert payload["source"] == "decomp_signature+aggregate_typedefs"


def test_fission_dataflow_contract_uses_typed_sink_keys(monkeypatch) -> None:
    server = load_module("fission_server_dataflow", ROOT / "docker/fission/server.py")
    monkeypatch.setattr(
        server,
        "_pcode_impl",
        lambda _path, _addr: [
            {
                "op": "Store",
                "inputs": [
                    {"space": "const", "offset": "0x3", "size": 8},
                    {"space": "register", "offset": "0x20", "size": 8},
                    {"space": "unique", "offset": "0x4f900", "size": 4},
                ],
            },
            {
                "op": "Return",
                "inputs": [
                    {"space": "register", "offset": "0x288", "size": 8}
                ],
            },
        ],
    )

    payload = server._dataflow_impl("/missing/dataflow-contract.bin", "0x1000")

    assert payload["return_sinks"] == ["void"]
    assert payload["store_sinks"] == ["register+0x20:8<-unique+0x4f900:4"]


def test_ghidra_extracts_marker_from_info_prefixed_line(monkeypatch, tmp_path) -> None:
    # Module import creates PROJECT_CACHE; keep it off the host root FS.
    monkeypatch.setenv("GHIDRA_PROJECT_CACHE", str(tmp_path / "ghidra-projects"))
    server = load_module("ghidra_server", ROOT / "docker/ghidra/server.py")

    text = (
        "INFO  DecompileFunction.java> ===BATCH_RESULT==="
        '[{"addr":"0x401000","name":"fn","code":"int fn(void) { return 1; }"}] '
        "(GhidraScript)"
    )

    assert server._extract_marked_json_line(text, server.BATCH_MARKER) == [
        {"addr": "0x401000", "name": "fn", "code": "int fn(void) { return 1; }"}
    ]


def test_revng_prefers_emit_c_as_single_file_artifact(monkeypatch) -> None:
    """Current revng images renamed decompile-to-single-file → emit-c-as-single-file."""
    monkeypatch.setitem(sys.modules, "disasm_helper", types.ModuleType("disasm_helper"))
    server = load_module("revng_server_artifact", ROOT / "docker/revng/server.py")

    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        if cmd[0] == "revng" and cmd[1] == "artifact":
            name = cmd[3] if len(cmd) > 3 else ""
            # First preferred name succeeds.
            if name == "emit-c-as-single-file":
                out = Path(cmd[cmd.index("-o") + 1])
                out.write_text("<ptml>ok</ptml>", encoding="utf-8")
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
            return subprocess.CompletedProcess(
                cmd,
                1,
                stdout="",
                stderr=f"No known artifact named {name}.\n",
            )
        if cmd[0] == "revng" and cmd[1] == "ptml":
            return subprocess.CompletedProcess(
                cmd,
                0,
                stdout=(
                    "_ABI(raw_x86_64)\n"
                    "void function_0x140001530_Code_x86_64(void) { return; }\n"
                ),
                stderr="",
            )
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="unexpected")

    monkeypatch.setattr(server.subprocess, "run", fake_run)

    resp = server.decompile_batch(
        server.BatchDecompileRequest(
            binary_b64=__import__("base64").b64encode(b"MZ").decode(),
            addresses=["0x140001530"],
        )
    )
    assert resp.results
    assert not resp.results[0].error
    assert "function_0x140001530" in (resp.results[0].code or "")
    artifact_names = [c[3] for c in calls if c[:2] == ["revng", "artifact"]]
    assert artifact_names[0] == "emit-c-as-single-file"


def test_revng_extracts_address_named_function(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "disasm_helper", types.ModuleType("disasm_helper"))
    server = load_module("revng_server", ROOT / "docker/revng/server.py")
    code = """
#include "types-and-globals.h"

_ABI(Microsoft_x86_cdecl)
generic32_t function_0x4015b0_Code_x86(void) {
  if (segment_1.offset_4) {
    return 1;
  }
  return 0;
}

_ABI(Microsoft_x86_cdecl)
generic32_t function_0x4015e7_Code_x86(void) {
  return 2;
}
"""

    name, extracted = server.extract_revng_function(code, "0x4015b0")

    assert name == "function_0x4015b0_Code_x86"
    assert "return 1;" in extracted
    assert "function_0x4015e7_Code_x86" not in extracted


def test_revng_extracts_containing_function_for_interior_address(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "disasm_helper", types.ModuleType("disasm_helper"))
    server = load_module("revng_server_interior", ROOT / "docker/revng/server.py")
    code = """
_ABI(raw_x86_64)
void function_0x140001520_Code_x86_64(void) {
  int local = 1;
  return;
}

_ABI(raw_x86_64)
void function_0x14000155f_Code_x86_64(void) {
  return;
}
"""

    name, extracted = server.extract_revng_function(code, "0x140001530")

    assert name == "function_0x140001520_Code_x86_64"
    assert "local = 1" in extracted
    assert "function_0x14000155f_Code_x86_64" not in extracted


def test_boomerang_extracts_function_by_rva_address(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "disasm_helper", types.ModuleType("disasm_helper"))
    server = load_module("boomerang_server", ROOT / "docker/boomerang/server.py")
    code = """
/* File: target.c */
/** address: 0x00001181 */
void proc_0x00001181(int pc) { return; }

/** address: 0x0000155f */
int proc_0x0000155f(int value, int lo, int hi) { return value; }
"""

    name, extracted = server.extract_function_by_address(code, "0x14000155f")

    assert name == "proc_0x0000155f"
    assert "return value" in extracted
    assert "proc_0x00001181" not in extracted


def test_boomerang_extracts_function_by_32bit_pe_rva_address(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "disasm_helper", types.ModuleType("disasm_helper"))
    server = load_module("boomerang_server_32", ROOT / "docker/boomerang/server.py")
    code = """
/** address: 0x000015d6 */
int proc_0x000015d6(int value, int lo, int hi) { return value; }
"""

    name, extracted = server.extract_function_by_address(code, "0x4015d6")

    assert name == "proc_0x000015d6"
    assert "return value" in extracted


def test_boomerang_cli_entry_address_uses_pe_rva(monkeypatch, tmp_path) -> None:
    monkeypatch.setitem(sys.modules, "disasm_helper", types.ModuleType("disasm_helper"))
    server = load_module("boomerang_server_entry", ROOT / "docker/boomerang/server.py")

    class OptionalHeader:
        ImageBase = 0x140000000
        Magic = 0x20B

    class PE:
        OPTIONAL_HEADER = OptionalHeader()

    pefile = types.ModuleType("pefile")
    pefile.PE = lambda *_args, **_kwargs: PE()
    monkeypatch.setitem(sys.modules, "pefile", pefile)

    assert server.boomerang_entry_address(tmp_path / "target.exe", "0x14000155f") == "0x155f"


def test_boomerang_cli_entry_address_keeps_pe32_va(monkeypatch, tmp_path) -> None:
    monkeypatch.setitem(sys.modules, "disasm_helper", types.ModuleType("disasm_helper"))
    server = load_module("boomerang_server_entry32", ROOT / "docker/boomerang/server.py")

    class OptionalHeader:
        ImageBase = 0x400000
        Magic = 0x10B

    class PE:
        OPTIONAL_HEADER = OptionalHeader()

    pefile = types.ModuleType("pefile")
    pefile.PE = lambda *_args, **_kwargs: PE()
    monkeypatch.setitem(sys.modules, "pefile", pefile)

    assert server.boomerang_entry_address(tmp_path / "target.exe", "0x4015d6") == "0x4015d6"


def test_boomerang_reports_missing_requested_address(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "disasm_helper", types.ModuleType("disasm_helper"))
    server = load_module("boomerang_server_missing", ROOT / "docker/boomerang/server.py")
    code = """
/** address: 0x00001181 */
void proc_0x00001181(int pc) { return; }
"""

    name, error = server.extract_function_by_address(code, "0x14000155f")

    assert name == ""
    assert "not found" in error


def test_boomerang_batch_falls_back_to_single_address_runs(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "disasm_helper", types.ModuleType("disasm_helper"))
    server = load_module("boomerang_server_fallback", ROOT / "docker/boomerang/server.py")
    calls = []

    def fake_run_boomerang(binary_path, workdir, addresses):
        calls.append(list(addresses))
        result = subprocess.CompletedProcess(args=["boomerang-cli"], returncode=0, stdout="failed", stderr="")
        if len(addresses) > 1:
            return "", result
        if addresses == ["0x140001624"]:
            return (
                "/** address: 0x00001624 */\n"
                "void proc_0x00001624(void) { return; }\n",
                result,
            )
        return "", result

    monkeypatch.setattr(server, "run_boomerang", fake_run_boomerang)
    req = server.BatchDecompileRequest(
        binary_b64="AA==",
        addresses=["0x140001530", "0x140001624"],
    )

    resp = server.decompile_batch(req)

    assert calls == [["0x140001530", "0x140001624"], ["0x140001530"], ["0x140001624"]]
    assert resp.results[0].error
    assert resp.results[1].error is None
    # Stable VA name + address anchor (adapter normalizes proc_0x00001624 → proc_140001624)
    assert resp.results[1].name == "proc_140001624"
    assert "/* address: 0x140001624" in resp.results[1].code
    assert "return" in resp.results[1].code


def test_snowman_detects_whole_program_output(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "disasm_helper", types.ModuleType("disasm_helper"))
    server = load_module("snowman_server", ROOT / "docker/snowman/server.py")
    code = "\n".join(f"int fun_{i}(void) {{ return {i}; }}" for i in range(5))

    assert server.function_definition_count(code) == 5
    assert server.is_whole_program_output(code) is True


def test_snowman_allows_single_function_output(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "disasm_helper", types.ModuleType("disasm_helper"))
    server = load_module("snowman_server_single", ROOT / "docker/snowman/server.py")
    code = "int fun_14000155f(int value, int lo, int hi) { return value; }"

    assert server.function_definition_count(code) == 1
    assert server.is_whole_program_output(code) is False


def test_snowman_extracts_pe_symbol_and_text_standin(monkeypatch) -> None:
    """Unstripped MinGW m32: PE keeps _clamp; count_bits is renamed to text."""
    disasm = types.ModuleType("disasm_helper")
    # PE layout mirrors control_flow_gcc-m32_O0.exe .text entries
    pe_syms = [
        (0x4015B0, "_count_bits"),
        (0x4015D6, "_clamp"),
        (0x4015F8, "_signum"),
    ]

    def list_pe_function_symbols(_binary):
        return list(pe_syms)

    def symbol_names_for_address(_binary, addr):
        target = int(str(addr), 16) if str(addr).startswith("0x") else int(addr)
        for va, name in pe_syms:
            if va == target:
                bare = name[1:] if name.startswith("_") else name
                return [name, bare]
        return []

    disasm.list_pe_function_symbols = list_pe_function_symbols
    disasm.symbol_names_for_address = symbol_names_for_address
    monkeypatch.setitem(sys.modules, "disasm_helper", disasm)

    server = load_module("snowman_server_pe", ROOT / "docker/snowman/server.py")
    # Whole-program-ish dump: stub text, real text (=count_bits), PE-named neighbors
    code = """
/* .text */
int32_t text(int32_t a1) {
    return 0;
}

uint32_t _clamp(uint32_t a1, uint32_t a2, uint32_t a3) {
    if (a1 < a2) return a2;
    if (a1 > a3) return a3;
    return a1;
}

/* .text */
void text(int32_t a1, int32_t* a2, int32_t* a3, int32_t a4) {
    __asm__("fninit ");
    return;
}

uint32_t text(uint32_t a1) {
    uint32_t v2;
    v2 = 0;
    while (a1) {
        v2 = v2 + (a1 & 1);
        a1 = a1 >> 1;
    }
    return v2;
}

int32_t _signum(int32_t a1, uint32_t a2, uint32_t a3) {
    if (a1 > 0) return 1;
    if (a1 < 0) return -1;
    return 0;
}
"""
    fake_bin = b"MZ" + b"\x00" * 64

    name, body, err = server.normalize_snowman_unit(code, "0x4015b0", fake_bin)
    assert err is None
    assert name == "fun_4015b0"
    assert "/* address: 0x4015b0" in body
    assert "while (a1)" in body
    assert "fninit" not in body

    name, body, err = server.normalize_snowman_unit(code, "0x4015d6", fake_bin)
    assert err is None
    assert name == "fun_4015d6"
    assert "return a2" in body or "a2" in body

    # Address-based fun_* still works without PE bytes
    strip_code = "uint32_t fun_4015b0(uint32_t a1) {\n    return a1;\n}\n"
    name, body, err = server.normalize_snowman_unit(strip_code, "0x4015b0", None)
    assert err is None
    assert "fun_4015b0" in body
