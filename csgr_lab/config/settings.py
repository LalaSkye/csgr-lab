"""Application settings using pydantic-settings.

All configuration is loaded from environment variables
with the CSGR_ prefix.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """CSGR-Lab configuration."""

    model_config = {"env_prefix": "CSGR_"}

    # Evidence storage
    evidence_dir: Path = Path(".csgr/evidence")
    evidence_filename: str = "evidence.jsonl"

    # Drift detection
    drift_z_threshold: float = 2.0
    drift_min_baseline: int = 5

    # Scoring
    determinism_check_runs: int = 3

    # Output
    json_output: bool = False
    verbose: bool = False

    @property
    def evidence_path(self) -> Path:
        return self.evidence_dir / self.evidence_filename
