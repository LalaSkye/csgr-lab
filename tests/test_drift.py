"""Tests for the drift detector module."""

import math

from csgr_lab.contracts.types import DriftDirection
from csgr_lab.drift.detector import DriftDetector, DriftReport, _mean, _std


class TestStatHelpers:
    def test_mean_of_values(self):
        assert _mean([1.0, 2.0, 3.0]) == 2.0

    def test_mean_empty(self):
        assert _mean([]) == 0.0

    def test_std_single_value(self):
        assert _std([5.0]) == 0.0

    def test_std_known_values(self):
        vals = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
        result = _std(vals)
        assert abs(result - 2.0) < 0.15  # sample std approx 2.0


class TestDriftDetector:
    def test_stable_metric(self):
        detector = DriftDetector(z_threshold=2.0)
        report = detector.analyze(
            metric="accuracy",
            baseline_values=[0.90, 0.91, 0.89, 0.90, 0.92],
            current_value=0.91,
        )
        assert isinstance(report, DriftReport)
        assert report.direction == DriftDirection.STABLE
        assert report.is_drifted is False

    def test_regression_detected(self):
        detector = DriftDetector(z_threshold=2.0)
        report = detector.analyze(
            metric="accuracy",
            baseline_values=[0.90, 0.91, 0.89, 0.90, 0.92],
            current_value=0.50,
        )
        assert report.is_drifted is True
        assert report.direction == DriftDirection.REGRESSION

    def test_improvement_detected(self):
        detector = DriftDetector(z_threshold=2.0)
        report = detector.analyze(
            metric="accuracy",
            baseline_values=[0.50, 0.51, 0.49, 0.50, 0.52],
            current_value=0.95,
        )
        assert report.is_drifted is True
        assert report.direction == DriftDirection.IMPROVEMENT

    def test_custom_z_threshold(self):
        detector = DriftDetector(z_threshold=1.0)
        report = detector.analyze(
            metric="latency",
            baseline_values=[100.0, 102.0, 98.0, 101.0, 99.0],
            current_value=105.0,
        )
        # With tighter threshold, more likely to flag drift
        assert report.threshold_z == 1.0

    def test_zero_std_same_value(self):
        detector = DriftDetector()
        report = detector.analyze(
            metric="score",
            baseline_values=[1.0, 1.0, 1.0],
            current_value=1.0,
        )
        assert report.z_score == 0.0
        assert report.is_drifted is False

    def test_zero_std_different_value(self):
        detector = DriftDetector()
        report = detector.analyze(
            metric="score",
            baseline_values=[1.0, 1.0, 1.0],
            current_value=2.0,
        )
        assert math.isinf(report.z_score)
        assert report.is_drifted is True

    def test_analyze_batch(self):
        detector = DriftDetector(z_threshold=2.0)
        baselines = {
            "accuracy": [0.9, 0.91, 0.89, 0.90, 0.92],
            "latency": [100.0, 102.0, 98.0, 101.0, 99.0],
        }
        current = {
            "accuracy": 0.91,
            "latency": 100.0,
        }
        reports = detector.analyze_batch(baselines, current)
        assert len(reports) == 2
        assert all(isinstance(r, DriftReport) for r in reports)

    def test_analyze_batch_partial_overlap(self):
        detector = DriftDetector()
        baselines = {"a": [1.0, 2.0, 3.0], "b": [4.0, 5.0, 6.0]}
        current = {"a": 2.0, "c": 10.0}
        reports = detector.analyze_batch(baselines, current)
        assert len(reports) == 1
        assert reports[0].metric == "a"

    def test_drift_report_is_frozen(self):
        detector = DriftDetector()
        report = detector.analyze("m", [1.0, 2.0, 3.0], 2.0)
        try:
            report.metric = "tampered"
            assert False, "Should have raised"
        except AttributeError:
            pass
