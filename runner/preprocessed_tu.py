"""Preprocessed translation-unit helpers for source-CFG ground truth.

Each compiled C/C++ binary is bound to the translation unit produced by the
same compiler configuration.  Line markers let us discard expanded system
headers while retaining the primary source and corpus-local headers.
"""
from __future__ import annotations

import re
from pathlib import Path


PREPROCESSED_TU_SCHEMA = "preprocessed-tu-v1"
_LINE_MARKER = re.compile(r'^\s*#\s+\d+\s+"([^"]+)"(?:\s+.*)?$')


def preprocessed_tu_path(binary: str, *, language: str = "c") -> str:
    """Return a stable corpus-relative TU path for a binary variant."""
    binary_path = Path(binary)
    parts = binary_path.parts
    if parts and parts[0] == "binaries":
        binary_path = Path(*parts[1:])
    suffix = ".ii" if language == "cpp" else ".i"
    return str(Path("preprocessed") / binary_path.with_suffix(suffix))


def strip_system_headers(
    preprocessed: str,
    *,
    source_path: Path,
    corpus_root: Path,
) -> str:
    """Keep only the primary TU and corpus-local includes from ``cc -E``.

    Compiler line markers switch the active source file.  Files outside the
    split's corpus root (including built-ins and standard headers) are omitted.
    The markers themselves are omitted because Joern does not need them.
    """
    source_path = source_path.resolve()
    corpus_root = corpus_root.resolve()
    keep = True
    kept: list[str] = []

    for line in preprocessed.splitlines():
        marker = _LINE_MARKER.match(line)
        if marker:
            raw_path = marker.group(1)
            if raw_path.startswith("<"):
                keep = False
                continue
            candidate = Path(raw_path)
            if not candidate.is_absolute():
                candidate = source_path.parent / candidate
            try:
                resolved = candidate.resolve()
                keep = resolved == source_path or resolved.is_relative_to(corpus_root)
            except (OSError, RuntimeError):
                keep = False
            continue
        if keep:
            kept.append(line)

    # Always end with a newline so the artifact is stable across compilers.
    return "\n".join(kept).rstrip() + "\n"
