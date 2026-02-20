"""Drift detector: compare scoring runs over time to identify regression.

Uses simple statistical methods (no scipy dependency) to detect
whether metric values have shifted beyond acceptable bounds.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence

from csgr_lab.contracts.types import DriftDirection


@dataclass(frozen=True)
class DriftReport:
    """Result of a drift analysis for a single metric."""

    metric: str
    baseline_mean: float
    baseline_std: float
    current_value: float
    z_score: float
    direction: DriftDirection
    is_drifted: bool
    threshold_z: float


def _mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


def _std(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    m = _mean(values)
    variance = sum((x - m) ** 2 for x in values) / (len(values) - 1)
    return math.sqrt(variance)


class DriftDetector:
    """Detect metric drift using z-score analysis.

    Compares current metric values against a baseline distribution
    to identify statistically significant changes.
    """

    def __init__(self, z_threshold: float = 2.0) -> None:
        self._z_threshold = z_threshold

    def analyze(
        self,
        metric: str,
        baseline_values: Sequence[float],
        current_value: float,
    ) -> DriftReport:
        """Analyze a single metric for drift.

        Args:
            metric: Name of the metric.
            baseline_values: Historical values forming the baseline.
            current_value: The current measured value to compare.

        Returns:
            DriftReport with analysis results.
        """
        b_mean = _mean(baseline_values)
        b_std = _std(baseline_values)

        if b_std == 0.0:
            z = 0.0 if current_value == b_mean else float("inf")
        else:
            z = (current_value - b_mean) / b_std

        abs_z = abs(z)
        is_drifted = abs_z > self._z_threshold

        if abs_z <= self._z_threshold:
            direction = DriftDirection.STABLE
        elif z > 0:
            direction = DriftDirection.IMPROVEMENT
        else:
            direction = DriftDirection.REGRESSION

        return DriftReport(
            metric=metric,
            baseline_mean=b_mean,
            baseline_std=b_std,
            current_value=current_value,
            z_score=z,
            direction=direction,
            is_drifted=is_drifted,
            threshold_z=self._z_threshold,
        )

    def analyze_batch(
        self,
        baselines: dict[str, Sequence[float]],
        current: dict[str, float],
    ) -> list[DriftReport]:
        """Analyze multiple metrics for drift.

        Args:
            baselines: Mapping of metric name to historical values.
            current: Mapping of metric name to current values.

        Returns:
            List of DriftReports for all metrics present in both inputs.
        """
        reports = []
        for metric in sorted(set(baselines) & set(current)):
            reports.append(
                self.analyze(metric, baselines[metric], current[metric])
            )
        return reports
