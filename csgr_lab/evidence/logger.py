"""Evidence logger: append-only JSONL with SHA-256 hash chain.

Each evidence record is chained to the previous via hash,
creating a tamper-evident audit trail.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


GENESIS_HASH = "0" * 64  # SHA-256 of nothing


class EvidenceLogger:
    """Append-only JSONL logger with hash-chain integrity.

    Each line in the log file is a JSON object containing:
    - The evidence payload
    - A SHA-256 hash of (previous_hash + payload)
    - The previous hash for chain verification
    """

    def __init__(self, log_path: Path | str) -> None:
        self._path = Path(log_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._prev_hash = self._recover_last_hash()

    def _recover_last_hash(self) -> str:
        """Read the last hash from an existing log file."""
        if not self._path.exists() or self._path.stat().st_size == 0:
            return GENESIS_HASH
        with self._path.open("r") as f:
            last_line = ""
            for line in f:
                line = line.strip()
                if line:
                    last_line = line
        if not last_line:
            return GENESIS_HASH
        record = json.loads(last_line)
        return record.get("hash", GENESIS_HASH)

    def _compute_hash(self, prev_hash: str, payload: str) -> str:
        """Compute SHA-256 hash of previous hash concatenated with payload."""
        content = f"{prev_hash}:{payload}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def log(self, evidence: dict[str, Any]) -> dict[str, Any]:
        """Append an evidence record to the log.

        Args:
            evidence: The evidence payload to record.

        Returns:
            The complete record including hash chain metadata.
        """
        payload = json.dumps(evidence, sort_keys=True, separators=(",", ":"))
        current_hash = self._compute_hash(self._prev_hash, payload)

        record = {
            "prev_hash": self._prev_hash,
            "hash": current_hash,
            "payload": evidence,
        }

        with self._path.open("a") as f:
            f.write(json.dumps(record, separators=(",", ":")) + "\n")

        self._prev_hash = current_hash
        return record

    def verify_chain(self) -> tuple[bool, int, str]:
        """Verify the integrity of the entire hash chain.

        Returns:
            Tuple of (is_valid, record_count, detail_message).
        """
        if not self._path.exists():
            return True, 0, "No log file found"

        prev_hash = GENESIS_HASH
        count = 0

        with self._path.open("r") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                count += 1
                record = json.loads(line)

                if record["prev_hash"] != prev_hash:
                    return (
                        False,
                        count,
                        f"Chain break at record {line_num}: "
                        f"expected prev_hash {prev_hash}, "
                        f"got {record['prev_hash']}",
                    )

                payload = json.dumps(
                    record["payload"],
                    sort_keys=True,
                    separators=(",", ":"),
                )
                expected_hash = self._compute_hash(prev_hash, payload)

                if record["hash"] != expected_hash:
                    return (
                        False,
                        count,
                        f"Hash mismatch at record {line_num}: "
                        f"expected {expected_hash}, "
                        f"got {record['hash']}",
                    )

                prev_hash = record["hash"]

        return True, count, f"Chain verified: {count} records intact"

    @property
    def path(self) -> Path:
        return self._path

    @property
    def last_hash(self) -> str:
        return self._prev_hash
