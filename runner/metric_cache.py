"""Versioned, content-addressed cache for deterministic benchmark metrics."""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any


CACHE_SCHEMA = "metric-content-cache-v1"
ROOT = Path(__file__).resolve().parents[1]


def cache_disabled() -> bool:
    return os.environ.get("FISSION_BENCHMARK_NO_CACHE", "").lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def cache_root() -> Path:
    configured = os.environ.get("FISSION_BENCHMARK_CACHE_DIR", "").strip()
    return Path(configured) if configured else ROOT / ".cache" / "metric-cache"


def content_digest(value: Any) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _path(metric: str, version: str, key: Any) -> tuple[Path, str]:
    digest = content_digest(key)
    safe_metric = "".join(c if c.isalnum() or c in "-_" else "-" for c in metric)
    safe_version = "".join(c if c.isalnum() or c in "-_" else "-" for c in version)
    return cache_root() / f"{safe_metric}-{safe_version}" / f"{digest}.json", digest


def load(metric: str, version: str, key: Any) -> Any | None:
    if cache_disabled():
        return None
    path, digest = _path(metric, version, key)
    try:
        envelope = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if (
        envelope.get("schema") != CACHE_SCHEMA
        or envelope.get("metric") != metric
        or envelope.get("version") != version
        or envelope.get("key_sha256") != digest
    ):
        return None
    return envelope.get("value")


def store(metric: str, version: str, key: Any, value: Any) -> None:
    if cache_disabled():
        return
    path, digest = _path(metric, version, key)
    path.parent.mkdir(parents=True, exist_ok=True)
    envelope = {
        "schema": CACHE_SCHEMA,
        "metric": metric,
        "version": version,
        "key_sha256": digest,
        "value": value,
    }
    encoded = json.dumps(envelope, sort_keys=True, separators=(",", ":"))
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
