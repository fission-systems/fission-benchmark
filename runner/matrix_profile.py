"""Load and apply corpus/matrix/profiles.yaml filters."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore

ROOT = Path(__file__).resolve().parent.parent
PROFILES_PATH = ROOT / "corpus" / "matrix" / "profiles.yaml"


def load_profiles(path: Path | None = None) -> dict[str, Any]:
    p = path or PROFILES_PATH
    if not p.is_file():
        return {"version": 1, "profiles": {}}
    text = p.read_text(encoding="utf-8")
    if yaml is not None:
        data = yaml.safe_load(text) or {}
    else:
        # Minimal fallback: no PyYAML — only support empty / refuse complex.
        raise RuntimeError(
            "PyYAML is required to load corpus/matrix/profiles.yaml "
            "(pip install pyyaml)"
        )
    if not isinstance(data, dict):
        return {"version": 1, "profiles": {}}
    return data


def get_profile(name: str | None, path: Path | None = None) -> dict[str, Any] | None:
    if not name:
        return None
    data = load_profiles(path)
    profiles = data.get("profiles") or {}
    prof = profiles.get(name)
    if prof is None:
        known = ", ".join(sorted(profiles)) or "(none)"
        raise KeyError(f"Unknown BENCHMARK_PROFILE/profile {name!r}. Known: {known}")
    return dict(prof)


def resolve_profile_name(cli_profile: str | None = None) -> str | None:
    if cli_profile:
        return cli_profile.strip() or None
    env = os.environ.get("BENCHMARK_PROFILE", "").strip()
    return env or None


def _norm_opt(opt: str) -> str:
    return (opt or "").strip()


def apply_profile_to_functions(
    functions: list[Any],
    profile: dict[str, Any],
) -> list[Any]:
    """Filter FunctionEntry list in-place-safe (returns new list with filtered variants)."""
    try:
        from corpus import FunctionEntry  # local import to avoid cycles
    except ImportError:  # pragma: no cover
        from runner.corpus import FunctionEntry  # type: ignore

    languages = set(profile.get("languages") or [])
    formats = set(profile.get("formats") or [])
    isas = set(profile.get("isas") or [])
    opts = {_norm_opt(o) for o in (profile.get("opts") or []) if o is not None}
    compilers = set(profile.get("compilers") or [])
    allow = profile.get("function_allowlist") or []
    allow_set = set(allow) if allow else None
    max_functions = int(profile.get("max_functions") or 0)
    max_variants = int(profile.get("max_variants_per_function") or 0)

    selected: list[Any] = []
    for fn in functions:
        if allow_set is not None and fn.name not in allow_set:
            continue
        lang = getattr(fn, "language", None) or "c"
        if languages and lang not in languages:
            continue

        kept_variants = []
        for v in fn.compiler_variants:
            if compilers and v.compiler not in compilers:
                continue
            if opts and _norm_opt(v.opt) not in opts:
                continue
            isa = getattr(v, "isa", "") or ""
            fmt = getattr(v, "format", "") or ""
            # Infer PE from .exe when tags missing (legacy manifests).
            if not fmt and str(v.binary).endswith(".exe"):
                fmt = "pe"
            if not isa:
                if v.compiler in {"gcc-m32", "clang-m32"}:
                    isa = "x86_32"
                else:
                    isa = "x86_64"
            if formats and fmt and fmt not in formats:
                continue
            if formats and not fmt and "pe" not in formats:
                continue
            if isas and isa and isa not in isas:
                continue
            kept_variants.append(v)

        if max_variants > 0:
            kept_variants = kept_variants[:max_variants]
        if not kept_variants:
            continue

        selected.append(
            FunctionEntry(
                name=fn.name,
                source=fn.source,
                compiler_variants=kept_variants,
                split=fn.split,
                language=lang,
                semantic=getattr(fn, "semantic", None) or {},
            )
        )

    # If allowlist order is specified, preserve that order first.
    if allow:
        order = {name: i for i, name in enumerate(allow)}
        selected.sort(key=lambda f: (order.get(f.name, 10_000), f.name))
    if max_functions > 0:
        selected = selected[:max_functions]
    return selected


def validate_release_contract(
    profile_name: str | None,
    profile: dict[str, Any] | None,
    functions: list[Any],
    decompilers: list[str],
) -> dict[str, Any] | None:
    """Validate and return the immutable subject contract for an official run.

    Profiles without ``release_contract`` remain usable for diagnostic runs.
    A contracted profile fails closed when a function, compiler variant, or
    compared decompiler drifts, so a release cannot silently publish a new
    denominator under the old chart series.
    """
    contract = (profile or {}).get("release_contract")
    if not contract:
        return None

    expected_functions = [str(name) for name in contract.get("functions") or []]
    expected_variants = [str(name) for name in contract.get("compiler_variants") or []]
    expected_decompilers = [str(name) for name in contract.get("decompilers") or []]
    actual_functions = [str(fn.name) for fn in functions]
    if actual_functions != expected_functions:
        missing = sorted(set(expected_functions) - set(actual_functions))
        extra = sorted(set(actual_functions) - set(expected_functions))
        raise ValueError(
            f"release contract {contract.get('id')!r} function drift "
            f"(missing={missing}, extra={extra}, order_changed="
            f"{not missing and not extra})"
        )

    expected_variant_set = set(expected_variants)
    variant_drift: list[str] = []
    subject_count = 0
    for fn in functions:
        actual = [f"{variant.compiler} {variant.opt}" for variant in fn.compiler_variants]
        subject_count += len(actual)
        if set(actual) != expected_variant_set or len(actual) != len(expected_variants):
            variant_drift.append(f"{fn.name}: {actual}")
    if variant_drift:
        raise ValueError(
            f"release contract {contract.get('id')!r} compiler variant drift: "
            + "; ".join(variant_drift[:5])
        )

    if decompilers != expected_decompilers:
        raise ValueError(
            f"release contract {contract.get('id')!r} decompiler drift "
            f"(expected={expected_decompilers}, actual={decompilers})"
        )

    expected_subjects = int(contract.get("subject_count") or 0)
    if expected_subjects and subject_count != expected_subjects:
        raise ValueError(
            f"release contract {contract.get('id')!r} subject drift "
            f"(expected={expected_subjects}, actual={subject_count})"
        )

    return {
        "id": str(contract.get("id") or f"{profile_name or 'profile'}-v1"),
        "version": int(contract.get("version") or 1),
        "profile": profile_name,
        "function_count": len(actual_functions),
        "compiler_variant_count": len(expected_variants),
        "subject_count": subject_count,
        "row_count": subject_count * len(decompilers),
        "decompilers": list(decompilers),
        "compiler_variants": expected_variants,
    }
