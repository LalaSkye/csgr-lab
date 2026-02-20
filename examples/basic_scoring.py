#!/usr/bin/env python3
"""Basic scoring example for CSGR-Lab.

Demonstrates how to:
1. Define a contract with behavioural clauses
2. Score measurements against the contract
3. Log evidence with tamper-evident hash chain
4. Verify evidence integrity

Usage:
    python examples/basic_scoring.py
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from csgr_lab.contracts.schema import ClauseSpec, ContractSpec
from csgr_lab.contracts.types import SeverityLevel
from csgr_lab.drift.detector import DriftDetector
from csgr_lab.evidence.logger import EvidenceLogger
from csgr_lab.scoring.engine import ScoringEngine


def main() -> None:
    # --- 1. Define a contract ---
    clauses = (
        ClauseSpec(
            description="Model accuracy must be at least 90%",
            metric="accuracy",
            operator=">=",
            threshold=0.90,
            severity=SeverityLevel.CRITICAL,
        ),
        ClauseSpec(
            description="Latency must be under 200ms",
            metric="latency_ms",
            operator="<",
            threshold=200.0,
            severity=SeverityLevel.HIGH,
        ),
        ClauseSpec(
            description="Hallucination rate below 5%",
            metric="hallucination_rate",
            operator="<",
            threshold=0.05,
            severity=SeverityLevel.CRITICAL,
            tolerance=0.01,
        ),
    )

    contract = ContractSpec(
        name="GPT-4o Safety Contract",
        model_id="gpt-4o-2024-05-13",
        clauses=clauses,
        metadata={"environment": "staging", "owner": "governance-team"},
    )

    print(f"Contract: {contract.name}")
    print(f"  ID: {contract.contract_id}")
    print(f"  Clauses: {len(contract.clauses)}")
    print()

    # --- 2. Score against measurements ---
    engine = ScoringEngine()
    measurements = {
        "accuracy": 0.93,
        "latency_ms": 145.0,
        "hallucination_rate": 0.03,
    }

    run = engine.score(contract, measurements)
    print(f"Scoring Run: {run.run_id}")
    print(f"  Status: {run.result.status.value.upper()}")
    print(f"  Pass: {run.result.pass_count} | Fail: {run.result.fail_count} | Warn: {run.result.warn_count}")
    print(f"  Input Hash: {run.input_hash[:16]}...")
    print()

    for cr in run.result.clause_results:
        icon = "PASS" if cr.status.value == "pass" else "FAIL"
        print(f"  [{icon}] {cr.metric}: {cr.detail}")
    print()

    # --- 3. Log evidence ---
    with tempfile.TemporaryDirectory() as tmp:
        log_path = Path(tmp) / "evidence.jsonl"
        logger = EvidenceLogger(log_path)
        record = logger.log(run.to_dict())
        print(f"Evidence logged to: {log_path}")
        print(f"  Hash: {record['hash'][:16]}...")

        # --- 4. Verify chain ---
        is_valid, count, detail = logger.verify_chain()
        print(f"  Chain valid: {is_valid} ({detail})")
        print()

    # --- 5. Drift detection ---
    detector = DriftDetector(z_threshold=2.0)
    baseline_accuracy = [0.91, 0.92, 0.90, 0.93, 0.91]
    report = detector.analyze("accuracy", baseline_accuracy, 0.93)
    print(f"Drift Analysis: {report.metric}")
    print(f"  Direction: {report.direction.value}")
    print(f"  Z-score: {report.z_score:.2f}")
    print(f"  Drifted: {report.is_drifted}")

    # --- 6. Determinism check ---
    print()
    is_deterministic = engine.verify_determinism(contract, measurements)
    print(f"Determinism verified: {is_deterministic}")


if __name__ == "__main__":
    main()
