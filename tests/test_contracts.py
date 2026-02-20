"""Tests for the contracts module."""

import pytest

from csgr_lab.contracts.schema import ClauseSpec, ContractSpec
from csgr_lab.contracts.types import ContractStatus, SeverityLevel
from csgr_lab.contracts.validators import validate_contract


def _make_clause(**overrides) -> ClauseSpec:
    defaults = {
        "description": "Test clause",
        "metric": "accuracy",
        "operator": ">=",
        "threshold": 0.9,
    }
    defaults.update(overrides)
    return ClauseSpec(**defaults)


def _make_contract(clauses=None, **overrides) -> ContractSpec:
    if clauses is None:
        clauses = (_make_clause(),)
    defaults = {
        "name": "Test Contract",
        "model_id": "test-model-v1",
        "clauses": clauses,
    }
    defaults.update(overrides)
    return ContractSpec(**defaults)


class TestClauseSpec:
    def test_create_valid_clause(self):
        clause = _make_clause()
        assert clause.metric == "accuracy"
        assert clause.threshold == 0.9

    def test_clause_is_frozen(self):
        clause = _make_clause()
        with pytest.raises(Exception):
            clause.metric = "changed"

    def test_severity_default(self):
        clause = _make_clause()
        assert clause.severity == SeverityLevel.HIGH


class TestContractSpec:
    def test_create_valid_contract(self):
        contract = _make_contract()
        assert contract.name == "Test Contract"
        assert len(contract.clauses) == 1

    def test_contract_is_frozen(self):
        contract = _make_contract()
        with pytest.raises(Exception):
            contract.name = "changed"

    def test_requires_at_least_one_clause(self):
        with pytest.raises(Exception):
            _make_contract(clauses=())


class TestValidation:
    def test_pass_when_threshold_met(self):
        contract = _make_contract()
        result = validate_contract(contract, {"accuracy": 0.95})
        assert result.status == ContractStatus.PASS
        assert result.pass_count == 1

    def test_fail_when_threshold_not_met(self):
        contract = _make_contract()
        result = validate_contract(contract, {"accuracy": 0.8})
        assert result.status == ContractStatus.FAIL
        assert result.fail_count == 1

    def test_error_on_missing_metric(self):
        contract = _make_contract()
        result = validate_contract(contract, {"other": 0.95})
        assert result.status == ContractStatus.FAIL
        assert result.clause_results[0].status == ContractStatus.ERROR

    def test_warn_within_tolerance(self):
        clause = _make_clause(threshold=0.9, tolerance=0.05)
        contract = _make_contract(clauses=(clause,))
        result = validate_contract(contract, {"accuracy": 0.86})
        assert result.status == ContractStatus.WARN

    def test_multiple_clauses(self):
        c1 = _make_clause(metric="accuracy", threshold=0.9)
        c2 = _make_clause(metric="latency", operator="<=", threshold=100.0)
        contract = _make_contract(clauses=(c1, c2))
        result = validate_contract(
            contract, {"accuracy": 0.95, "latency": 50.0}
        )
        assert result.status == ContractStatus.PASS
        assert result.pass_count == 2
