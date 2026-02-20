"""Scoring engine: deterministic contract evaluation with evidence capture.

Design principles:
- Same input always produces same output (deterministic)
- Every run produces an evidence record
- No hidden state, no side effects during scoring
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from csgr_lab.contracts.schema import ContractSpec
from csgr_lab.contracts.types import RunId
from csgr_lab.contracts.validators import ContractResult, validate_contract


def _make_run_id() -> RunId:
    return RunId(uuid4().hex[:16])


def _hash_inputs(contract: ContractSpec, measurements: dict[str, float]) -> str:
    """Create a deterministic hash of the scoring inputs."""
    payload = json.dumps(
        {
            "contract": contract.model_dump(mode="json"),
            "measurements": dict(sorted(measurements.items())),
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode()).hexdigest()


class ScoringRun:
    """Immutable record of a single scoring run."""

    __slots__ = (
        "_run_id",
        "_contract_id",
        "_input_hash",
        "_result",
        "_timestamp",
        "_measurements",
    )

    def __init__(
        self,
        run_id: RunId,
        contract_id: str,
        input_hash: str,
        result: ContractResult,
        timestamp: str,
        measurements: dict[str, float],
    ) -> None:
        object.__setattr__(self, "_run_id", run_id)
        object.__setattr__(self, "_contract_id", contract_id)
        object.__setattr__(self, "_input_hash", input_hash)
        object.__setattr__(self, "_result", result)
        object.__setattr__(self, "_timestamp", timestamp)
        object.__setattr__(self, "_measurements", measurements)

    def __setattr__(self, *_: object) -> None:
        raise AttributeError("ScoringRun is immutable")

    @property
    def run_id(self) -> RunId:
        return self._run_id  # type: ignore[attr-defined]

    @property
    def contract_id(self) -> str:
        return self._contract_id  # type: ignore[attr-defined]

    @property
    def input_hash(self) -> str:
        return self._input_hash  # type: ignore[attr-defined]

    @property
    def result(self) -> ContractResult:
        return self._result  # type: ignore[attr-defined]

    @property
    def timestamp(self) -> str:
        return self._timestamp  # type: ignore[attr-defined]

    @property
    def measurements(self) -> dict[str, float]:
        return dict(self._measurements)  # type: ignore[attr-defined]

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self._run_id,  # type: ignore[attr-defined]
            "contract_id": self._contract_id,  # type: ignore[attr-defined]
            "input_hash": self._input_hash,  # type: ignore[attr-defined]
            "timestamp": self._timestamp,  # type: ignore[attr-defined]
            "measurements": self._measurements,  # type: ignore[attr-defined]
            "result": asdict(self._result),  # type: ignore[attr-defined]
        }


class ScoringEngine:
    """Stateless scoring engine.

    Evaluates contracts against measurements and produces
    immutable ScoringRun records.
    """

    def score(
        self,
        contract: ContractSpec,
        measurements: dict[str, float],
    ) -> ScoringRun:
        """Execute a scoring run.

        Args:
            contract: The contract to evaluate.
            measurements: Metric name -> measured value mapping.

        Returns:
            An immutable ScoringRun with results and evidence.
        """
        run_id = _make_run_id()
        input_hash = _hash_inputs(contract, measurements)
        timestamp = datetime.now(timezone.utc).isoformat()
        result = validate_contract(contract, measurements)

        return ScoringRun(
            run_id=run_id,
            contract_id=contract.contract_id,
            input_hash=input_hash,
            result=result,
            timestamp=timestamp,
            measurements=dict(measurements),
        )

    def verify_determinism(
        self,
        contract: ContractSpec,
        measurements: dict[str, float],
        n_runs: int = 3,
    ) -> bool:
        """Verify that scoring is deterministic across multiple runs."""
        hashes = set()
        for _ in range(n_runs):
            _hash_inputs(contract, measurements)
            run = self.score(contract, measurements)
            hashes.add(run.result.status.value)
        return len(hashes) == 1
