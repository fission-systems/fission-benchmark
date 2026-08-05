"""Append-only row checkpoints for resumable benchmark matrix runs."""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, fields
from pathlib import Path
from typing import Any, Iterable

try:
    from .scoring import FunctionScore
except ImportError:
    from scoring import FunctionScore


CHECKPOINT_SCHEMA = "benchmark-checkpoint-v1"


def cell_key(value: Any) -> tuple[str, str, str]:
    if isinstance(value, dict):
        return (
            str(value.get("decompiler") or ""),
            str(value.get("function_name") or ""),
            str(value.get("compiler_variant") or ""),
        )
    return (
        str(value.decompiler),
        str(value.function_name),
        str(value.compiler_variant),
    )


def contract_sha256(contract: dict[str, Any]) -> str:
    encoded = json.dumps(
        contract, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class BenchmarkCheckpoint:
    def __init__(
        self,
        path: Path,
        *,
        contract: dict[str, Any],
        reset: bool = False,
    ) -> None:
        self.path = path
        self.contract = contract
        self.contract_sha256 = contract_sha256(contract)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if reset and self.path.exists():
            self.path.unlink()
        self._rows = self._load_or_initialize()

    def _load_or_initialize(self) -> dict[tuple[str, str, str], FunctionScore]:
        if not self.path.exists():
            self._append_record(
                {
                    "record": "meta",
                    "schema": CHECKPOINT_SCHEMA,
                    "contract_sha256": self.contract_sha256,
                    "contract": self.contract,
                }
            )
            return {}

        rows: dict[tuple[str, str, str], FunctionScore] = {}
        known = {field.name for field in fields(FunctionScore)}
        meta_seen = False
        with self.path.open(encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    # A process may have died during the final append. Only a
                    # truncated final record is recoverable; earlier damage is not.
                    if line_number == sum(1 for _ in self.path.open(encoding="utf-8")):
                        break
                    raise ValueError(f"invalid checkpoint JSON at line {line_number}")
                if record.get("record") == "meta":
                    meta_seen = True
                    if (
                        record.get("schema") != CHECKPOINT_SCHEMA
                        or record.get("contract_sha256") != self.contract_sha256
                    ):
                        raise ValueError(
                            "checkpoint contract does not match this benchmark run"
                        )
                    continue
                if record.get("record") != "row":
                    continue
                raw = record.get("row") or {}
                score = FunctionScore(**{k: v for k, v in raw.items() if k in known})
                rows[cell_key(score)] = score
        if not meta_seen:
            raise ValueError("checkpoint is missing its metadata record")
        return rows

    def _append_record(self, record: dict[str, Any]) -> None:
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, sort_keys=True, separators=(",", ":")))
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())

    @property
    def recovered_rows(self) -> list[FunctionScore]:
        return list(self._rows.values())

    def contains(self, key: tuple[str, str, str]) -> bool:
        return key in self._rows

    def append(self, rows: Iterable[FunctionScore]) -> None:
        for row in rows:
            key = cell_key(row)
            if key in self._rows:
                continue
            self._append_record(
                {
                    "record": "row",
                    "cell": list(key),
                    "row": asdict(row),
                }
            )
            self._rows[key] = row
