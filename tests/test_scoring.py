"""Tests for the scoring engine module."""

import pytest

from csgr_lab.contracts.schema import ClauseSpec, ContractSpec
from csgr_lab.contracts.types import ContractStatus
from csgr_lab.scoring.engine import ScoringEngine, ScoringRun, _hash_inputs


def _make_contract(**overrides):
    """Helper to build a minimal ContractSpec for testing."""
    clause = ClauseSpec(
        description="accuracy above 0.9",
        metric="accuracy",
        operator=">=",
        threshold=0.9,
    )
    defaults = dict(
        name="test-contract",
        model_id="model-abc",
        clauses=(clause,),
    )
    defaults.update(overrides)
    return ContractSpec(**defaults)


class TestScoringEngine:
    def test_score_returns_scoring_run(self):
        engine = ScoringEngine()
        contract = _make_contract()
        run = engine.score(contract, {"accuracy": 0.95})
        assert isinstance(run, ScoringRun)

    def test_passing_contract(self):
        engine = ScoringEngine()
        contract = _make_contract()
        run = engine.score(contract, {"accuracy": 0.95})
        assert run.result.status == ContractStatus.PASS
        assert run.result.pass_count == 1
        assert run.result.fail_count == 0

    def test_failing_contract(self):
        engine = ScoringEngine()
        contract = _make_contract()
        run = engine.score(contract, {"accuracy": 0.5})
        assert run.result.status == ContractStatus.FAIL
        assert run.result.fail_count == 1

    def test_scoring_run_immutability(self):
        engine = ScoringEngine()
        contract = _make_contract()
        run = engine.score(contract, {"accuracy": 0.95})
        with pytest.raises(AttributeError, match="immutable"):
            run.run_id = "tampered"

    def test_scoring_run_to_dict(self):
        engine = ScoringEngine()
        contract = _make_contract()
        run = engine.score(contract, {"accuracy": 0.95})
        d = run.to_dict()
        assert "run_id" in d
        assert "input_hash" in d
        assert "result" in d
        assert d["contract_id"] == contract.contract_id

    def test_deterministic_hashing(self):
        contract = _make_contract()
        m = {"accuracy": 0.95}
        h1 = _hash_inputs(contract, m)
        h2 = _hash_inputs(contract, m)
        assert h1 == h2

    def test_different_inputs_different_hash(self):
        contract = _make_contract()
        h1 = _hash_inputs(contract, {"accuracy": 0.95})
        h2 = _hash_inputs(contract, {"accuracy": 0.80})
        assert h1 != h2

    def test_verify_determinism(self):
        engine = ScoringEngine()
        contract = _make_contract()
        assert engine.verify_determinism(contract, {"accuracy": 0.95}) is True

    def test_run_has_timestamp(self):
        engine = ScoringEngine()
        contract = _make_contract()
        run = engine.score(contract, {"accuracy": 0.95})
        assert run.timestamp is not None
        assert "T" in run.timestamp  # ISO format

    def test_measurements_property_returns_copy(self):
        engine = ScoringEngine()
        contract = _make_contract()
        run = engine.score(contract, {"accuracy": 0.95})
        m = run.measurements
        m["tampered"] = 999
        assert "tampered" not in run.measurements
