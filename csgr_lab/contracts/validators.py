"""Contract validation: evaluate clauses against measured values."""

from __future__ import annotations

import operator as op
from collections.abc import Mapping
from dataclasses import dataclass

from csgr_lab.contracts.schema import ClauseSpec, ContractSpec
from csgr_lab.contracts.types import ContractStatus, SeverityLevel

_OPS = {
    ">": op.gt,
    ">=": op.ge,
    "<": op.lt,
    "<=": op.le,
    "==": op.eq,
    "!=": op.ne,
}


@dataclass(frozen=True)
class ClauseResult:
    """Result of evaluating a single clause."""

    clause_id: str
    metric: str
    measured: float
    threshold: float
    operator: str
    status: ContractStatus
    severity: SeverityLevel
    detail: str = ""


@dataclass(frozen=True)
class ContractResult:
    """Aggregate result of evaluating all clauses in a contract."""

    contract_id: str
    contract_name: str
    status: ContractStatus
    clause_results: tuple[ClauseResult, ...]
    pass_count: int
    fail_count: int
    warn_count: int


def _evaluate_clause(clause: ClauseSpec, measured: float) -> ClauseResult:
    """Evaluate a single clause against a measured value."""
    comparator = _OPS[clause.operator]
    passed = comparator(measured, clause.threshold)

    # Check tolerance band for near-misses
    in_tolerance = False
    if not passed and clause.tolerance > 0:
        delta = abs(measured - clause.threshold)
        in_tolerance = delta <= (clause.tolerance * abs(clause.threshold or 1.0))

    if passed:
        status = ContractStatus.PASS
        detail = f"{measured} {clause.operator} {clause.threshold}"
    elif in_tolerance:
        status = ContractStatus.WARN
        detail = f"{measured} within tolerance of {clause.threshold}"
    else:
        status = ContractStatus.FAIL
        detail = f"{measured} NOT {clause.operator} {clause.threshold}"

    return ClauseResult(
        clause_id=clause.clause_id,
        metric=clause.metric,
        measured=measured,
        threshold=clause.threshold,
        operator=clause.operator,
        status=status,
        severity=clause.severity,
        detail=detail,
    )


def validate_contract(
    contract: ContractSpec,
    measurements: Mapping[str, float],
) -> ContractResult:
    """Validate all clauses in a contract against provided measurements.

    Args:
        contract: The contract specification to evaluate.
        measurements: Mapping of metric names to measured values.

    Returns:
        ContractResult with per-clause and aggregate status.

    Raises:
        KeyError: If a required metric is missing from measurements.
    """
    results: list[ClauseResult] = []
    for clause in contract.clauses:
        if clause.metric not in measurements:
            results.append(
                ClauseResult(
                    clause_id=clause.clause_id,
                    metric=clause.metric,
                    measured=float("nan"),
                    threshold=clause.threshold,
                    operator=clause.operator,
                    status=ContractStatus.ERROR,
                    severity=clause.severity,
                    detail=f"Missing metric: {clause.metric}",
                )
            )
            continue

        measured = measurements[clause.metric]
        results.append(_evaluate_clause(clause, measured))

    clause_results = tuple(results)
    pass_count = sum(1 for r in clause_results if r.status == ContractStatus.PASS)
    fail_count = sum(1 for r in clause_results if r.status == ContractStatus.FAIL)
    warn_count = sum(1 for r in clause_results if r.status == ContractStatus.WARN)
    error_count = sum(1 for r in clause_results if r.status == ContractStatus.ERROR)

    if fail_count > 0 or error_count > 0:
        overall = ContractStatus.FAIL
    elif warn_count > 0:
        overall = ContractStatus.WARN
    else:
        overall = ContractStatus.PASS

    return ContractResult(
        contract_id=contract.contract_id,
        contract_name=contract.name,
        status=overall,
        clause_results=clause_results,
        pass_count=pass_count,
        fail_count=fail_count,
        warn_count=warn_count,
    )
