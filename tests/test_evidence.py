"""Tests for the evidence logger with hash-chain integrity."""

from __future__ import annotations

import json
from csgr_lab.evidence.logger import EvidenceLogger, GENESIS_HASH


class TestEvidenceLogger:
    def test_log_creates_file(self, tmp_path):
        log_path = tmp_path / "evidence.jsonl"
        logger = EvidenceLogger(log_path)
        logger.log({"test": "data"})
        assert log_path.exists()

    def test_log_appends_records(self, tmp_path):
        log_path = tmp_path / "evidence.jsonl"
        logger = EvidenceLogger(log_path)
        logger.log({"run": 1})
        logger.log({"run": 2})
        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 2

    def test_hash_chain_integrity(self, tmp_path):
        log_path = tmp_path / "evidence.jsonl"
        logger = EvidenceLogger(log_path)
        logger.log({"a": 1})
        logger.log({"b": 2})
        logger.log({"c": 3})
        is_valid, count, detail = logger.verify_chain()
        assert is_valid
        assert count == 3

    def test_first_record_chains_from_genesis(self, tmp_path):
        log_path = tmp_path / "evidence.jsonl"
        logger = EvidenceLogger(log_path)
        logger.log({"first": True})
        record = json.loads(log_path.read_text().strip())
        assert record["prev_hash"] == GENESIS_HASH

    def test_detect_tampered_record(self, tmp_path):
        log_path = tmp_path / "evidence.jsonl"
        logger = EvidenceLogger(log_path)
        logger.log({"a": 1})
        logger.log({"b": 2})

        # Tamper with the log
        lines = log_path.read_text().strip().split("\n")
        record = json.loads(lines[0])
        record["payload"]["a"] = 999
        lines[0] = json.dumps(record, separators=(",", ":"))
        log_path.write_text("\n".join(lines) + "\n")

        # Re-open and verify
        logger2 = EvidenceLogger(log_path)
        is_valid, count, detail = logger2.verify_chain()
        assert not is_valid

    def test_recovery_from_existing_log(self, tmp_path):
        log_path = tmp_path / "evidence.jsonl"
        logger1 = EvidenceLogger(log_path)
        r1 = logger1.log({"first": True})

        # New logger instance recovers last hash
        logger2 = EvidenceLogger(log_path)
        assert logger2.last_hash == r1["hash"]
