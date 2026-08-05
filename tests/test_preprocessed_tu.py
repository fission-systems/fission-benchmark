import json
from pathlib import Path

from runner.corpus import Corpus
from runner.preprocessed_tu import preprocessed_tu_path, strip_system_headers
from scripts.check_preprocessed_tus import missing_preprocessed_tus


def test_preprocessed_tu_path_is_binary_specific() -> None:
    assert (
        preprocessed_tu_path("binaries/c/foo_gcc_O2.exe")
        == "preprocessed/c/foo_gcc_O2.i"
    )
    assert (
        preprocessed_tu_path("binaries/cpp/foo_clang_O0", language="cpp")
        == "preprocessed/cpp/foo_clang_O0.ii"
    )


def test_strip_system_headers_keeps_primary_and_corpus_headers(tmp_path: Path) -> None:
    corpus_root = tmp_path / "dev"
    source = corpus_root / "source/c/example.c"
    header = corpus_root / "source/c/local.h"
    source.parent.mkdir(parents=True)
    source.write_text("#include <stdint.h>\n#include \"local.h\"\n")
    header.write_text("#define LOCAL 7\n")
    preprocessed = f'''# 1 "{source}"
int before;
# 1 "/usr/include/stdint.h" 1 3 4
typedef int system_type;
# 2 "{source}" 2
# 1 "{header}" 1
int local_decl;
# 3 "{source}" 2
int after = LOCAL;
'''

    stripped = strip_system_headers(
        preprocessed,
        source_path=source,
        corpus_root=corpus_root,
    )

    assert "int before;" in stripped
    assert "int local_decl;" in stripped
    assert "int after = LOCAL;" in stripped
    assert "system_type" not in stripped
    assert "# 1" not in stripped


def test_manifest_loads_preprocessed_source(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps(
            {
                "functions": [
                    {
                        "name": "foo",
                        "source": "source/c/foo.c",
                        "compiler_variants": [
                            {
                                "compiler": "gcc",
                                "opt": "-O2",
                                "binary": "binaries/c/foo.exe",
                                "addr": "0x401000",
                                "preprocessed_source": "preprocessed/c/foo.i",
                            }
                        ],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    variant = Corpus.load(manifest).functions[0].compiler_variants[0]
    assert variant.preprocessed_source == "preprocessed/c/foo.i"


def test_preprocessed_tu_contract_detects_missing_file(tmp_path: Path) -> None:
    split = tmp_path / "dev"
    manifests = split / "manifests"
    manifests.mkdir(parents=True)
    (manifests / "sample.json").write_text(
        json.dumps(
            {
                "functions": [
                    {
                        "name": "foo",
                        "language": "c",
                        "source": "source/c/foo.c",
                        "compiler_variants": [
                            {
                                "compiler": "gcc",
                                "opt": "-O2",
                                "binary": "binaries/c/foo.exe",
                                "preprocessed_source": "preprocessed/c/foo.i",
                            }
                        ],
                    }
                ]
            }
        )
    )

    failures = missing_preprocessed_tus(split)
    assert failures == ["sample.json:foo:gcc -O2: missing file preprocessed/c/foo.i"]

    tu = split / "preprocessed/c/foo.i"
    tu.parent.mkdir(parents=True)
    tu.write_text("int foo(void) { return 0; }\n")
    assert missing_preprocessed_tus(split) == []
