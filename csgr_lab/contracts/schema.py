"""Contract schema definitions using Pydantic frozen models.

Every contract is a deterministic, immutable specification.
No defaults. No optionals unless explicitly bounded.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from csgr_lab.contracts.types import (
    ClauseId,
    ContractId,
    SeverityLevel,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_clause_id() -> ClauseId:
    return ClauseId(uuid4().hex[:12])


def _new_contract_id() -> ContractId:
    return ContractId(uuid4().hex[:12])


class ClauseSpec(BaseModel, frozen=True):
    """A single testable clause within a contract."""

    clause_id: ClauseId = Field(default_factory=_new_clause_id)
    description: str = Field(..., min_length=1, max_length=500)
    metric: str = Field(..., description="Name of the metric to evaluate")
    operator: Literal[">", ">=", "<", "<=", "==", "!="] = Field(...)
    threshold: float = Field(..., description="Threshold value for pass/fail")
    severity: SeverityLevel = Field(default=SeverityLevel.HIGH)
    tolerance: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Acceptable tolerance band around threshold",
    )


class ContractSpec(BaseModel, frozen=True):
    """Top-level contract specification.

    A contract binds a model identity to a set of behavioural clauses.
    Once created, it is immutable - the hash is the identity.
    """

    contract_id: ContractId = Field(default_factory=_new_contract_id)
    name: str = Field(..., min_length=1, max_length=200)
    version: str = Field(default="1.0.0")
    created_at: str = Field(default_factory=_utc_now)
    model_id: str = Field(..., description="Identifier for the model under test")
    clauses: tuple[ClauseSpec, ...] = Field(
        ..., min_length=1, description="At least one clause required"
    )
    metadata: dict[str, str] = Field(default_factory=dict)

    @field_validator("clauses")
    @classmethod
    def _no_duplicate_clause_ids(
        cls, v: tuple[ClauseSpec, ...]
    ) -> tuple[ClauseSpec, ...]:
        ids = [c.clause_id for c in v]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate clause IDs detected")
        return v
