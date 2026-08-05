"""Corpus management with 80/20 holdout split for overfitting prevention."""
from __future__ import annotations

import hashlib
import json
import random
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any

CORPUS_ROOT = Path(__file__).parent.parent / "corpus"
HOLDOUT_SEED = 42  # Fixed seed — never change after initial split
HOLDOUT_RATIO = 0.20


@dataclass
class CompilerVariant:
    compiler: str  # "gcc", "clang", "gcc-m32", "g++", "rustc", "go", ...
    opt: str  # "-O0", "-O2", rust "0"/"2", go "default"
    binary: str  # relative path under corpus/{split}/
    addr: str = "0x0"  # function entry address in this binary
    isa: str = ""  # x86_64 | x86_32 | aarch64
    format: str = ""  # pe | elf
    abi_profile: str = ""  # windows-x86_64 | linux-x86_64 | ...
    preprocessed_source: str = ""  # exact C/C++ TU used for source-CFG GED


@dataclass
class FunctionEntry:
    name: str
    source: str  # relative path to source under corpus/{split}/
    compiler_variants: list[CompilerVariant]
    split: str = "dev"  # "dev" | "holdout" | "realworld"
    language: str = "c"  # c | cpp | rust | go
    semantic: dict[str, Any] = field(default_factory=dict)


def _infer_language(source: str, explicit: str | None = None) -> str:
    if explicit:
        return explicit
    s = source.replace("\\", "/")
    if "/cpp/" in s or s.endswith((".cpp", ".cc", ".cxx")):
        return "cpp"
    if "/rust/" in s or s.endswith(".rs"):
        return "rust"
    if "/go/" in s or s.endswith(".go"):
        return "go"
    return "c"


def _variant_from_dict(raw: dict[str, Any]) -> CompilerVariant:
    known = {f.name for f in fields(CompilerVariant)}
    data = {k: v for k, v in raw.items() if k in known}
    # Defaults for legacy manifests.
    if not data.get("format") and str(data.get("binary", "")).endswith(".exe"):
        data["format"] = "pe"
    if not data.get("isa"):
        comp = str(data.get("compiler", ""))
        data["isa"] = "x86_32" if comp in {"gcc-m32", "clang-m32"} else "x86_64"
    if not data.get("abi_profile"):
        if data.get("format") == "pe":
            data["abi_profile"] = (
                "windows-x86" if data.get("isa") == "x86_32" else "windows-x86_64"
            )
        elif data.get("format") == "elf":
            data["abi_profile"] = (
                "linux-aarch64"
                if data.get("isa") == "aarch64"
                else "linux-x86_64"
            )
    return CompilerVariant(**data)


@dataclass
class Corpus:
    functions: list[FunctionEntry] = field(default_factory=list)

    @classmethod
    def load(cls, manifest_path: Path) -> "Corpus":
        data = json.loads(manifest_path.read_text())
        functions = []
        for fn in data["functions"]:
            variants = []
            for v in fn.get("compiler_variants", []):
                addr = v.get("addr", "0x0")
                if not addr or addr == "0x0":
                    import warnings

                    warnings.warn(
                        f"[corpus] {manifest_path.name}: function '{fn['name']}' variant "
                        f"'{v.get('compiler', '?')} {v.get('opt', '?')}' has addr='{addr}'. "
                        "Decompiler will likely fail to locate the function. "
                        "Set a correct entry address in the manifest.",
                        stacklevel=2,
                    )
                variants.append(_variant_from_dict(v))
            language = _infer_language(fn.get("source", ""), fn.get("language"))
            semantic = fn.get("semantic") if isinstance(fn.get("semantic"), dict) else {}
            functions.append(
                FunctionEntry(
                    name=fn["name"],
                    source=fn["source"],
                    compiler_variants=variants,
                    language=language,
                    semantic=dict(semantic or {}),
                )
            )
        return cls(functions=functions)

    @classmethod
    def load_all(cls, split: str = "dev") -> "Corpus":
        """Load all manifests from corpus/{split}/manifests/.

        ``split`` must be one of ``"dev"``, ``"holdout"``, ``"full"``, or
        ``"realworld"`` (reserved track; empty until populated).
        ``"full"`` loads both dev and holdout (used for release evaluation).
        """
        if split == "full":
            dev = cls.load_all("dev")
            holdout = cls.load_all("holdout")
            return cls(functions=dev.functions + holdout.functions)
        if split not in ("dev", "holdout", "realworld"):
            raise ValueError(
                f"Invalid corpus split: {split!r}. "
                f"Must be one of 'dev', 'holdout', 'realworld', or 'full'."
            )
        manifest_dir = CORPUS_ROOT / split / "manifests"
        all_functions: list[FunctionEntry] = []
        seen_names: dict[str, str] = {}  # function_name -> manifest filename
        if not manifest_dir.is_dir():
            return cls(functions=[])
        for manifest in sorted(manifest_dir.glob("*.json")):
            c = cls.load(manifest)
            for fn in c.functions:
                fn.split = split
                if fn.name in seen_names:
                    import warnings

                    warnings.warn(
                        f"[corpus] Duplicate function name '{fn.name}' found in "
                        f"'{manifest.name}' and '{seen_names[fn.name]}'. "
                        "This will produce duplicate cells and fail the matrix validity gate. "
                        "Rename one of the entries.",
                        stacklevel=2,
                    )
                else:
                    seen_names[fn.name] = manifest.name
                all_functions.append(fn)
        return cls(functions=all_functions)

    def apply_profile(self, profile_name: str | None) -> "Corpus":
        """Return a filtered copy according to corpus/matrix/profiles.yaml."""
        if not profile_name:
            return self
        try:
            from matrix_profile import apply_profile_to_functions, get_profile
        except ImportError:  # pragma: no cover
            from runner.matrix_profile import (  # type: ignore
                apply_profile_to_functions,
                get_profile,
            )

        prof = get_profile(profile_name)
        if not prof:
            return self
        return Corpus(functions=apply_profile_to_functions(self.functions, prof))


def split_corpus_to_holdout(
    manifest_path: Path,
    out_dev: Path,
    out_holdout: Path,
    seed: int = HOLDOUT_SEED,
    holdout_ratio: float = HOLDOUT_RATIO,
) -> tuple[int, int]:
    """
    Deterministically split a manifest into dev/holdout by function unit.
    Holdout functions are locked — never use them during development.

    Returns: (n_dev, n_holdout)
    """
    corpus = Corpus.load(manifest_path)
    rng = random.Random(seed)

    # Deterministic shuffle by function name hash for reproducibility
    functions = sorted(
        corpus.functions, key=lambda f: hashlib.sha256(f.name.encode()).hexdigest()
    )
    rng.shuffle(functions)

    n_holdout = max(1, int(len(functions) * holdout_ratio))
    holdout = functions[:n_holdout]
    dev = functions[n_holdout:]

    def serialize(fns: list[FunctionEntry]) -> dict:
        return {
            "functions": [
                {
                    "name": fn.name,
                    "language": fn.language,
                    "source": fn.source,
                    "semantic": fn.semantic or {
                        "mode": "c_wrapper",
                        "wrapper_id": fn.name,
                        "oracle": "pe_wine",
                    },
                    "compiler_variants": [
                        {
                            k: v
                            for k, v in asdict(var).items()
                            if v not in ("", None)
                        }
                        for var in fn.compiler_variants
                    ],
                }
                for fn in fns
            ]
        }

    out_dev.parent.mkdir(parents=True, exist_ok=True)
    out_holdout.parent.mkdir(parents=True, exist_ok=True)
    out_dev.write_text(json.dumps(serialize(dev), indent=2) + "\n")
    out_holdout.write_text(json.dumps(serialize(holdout), indent=2) + "\n")

    return len(dev), n_holdout
