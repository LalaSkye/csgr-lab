"""Core type definitions for the CSGR contract system."""

from enum import Enum, auto
from typing import NewType


class ContractStatus(str, Enum):
    """Status of a contract evaluation."""
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    ERROR = "error"


class SeverityLevel(str, Enum):
    """Severity classification for clause violations."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class DriftDirection(str, Enum):
    """Direction of detected drift."""
    REGRESSION = "regression"
    IMPROVEMENT = "improvement"
    STABLE = "stable"


# Semantic type aliases for clarity
ContractId = NewType("ContractId", str)
ClauseId = NewType("ClauseId", str)
RunId = NewType("RunId", str)
Score = NewType("Score", float)
HashDigest = NewType("HashDigest", str)
