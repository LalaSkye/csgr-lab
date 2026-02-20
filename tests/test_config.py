"""Tests for the configuration settings module."""

from pathlib import Path

from csgr_lab.config.settings import Settings


class TestSettings:
    def test_default_evidence_dir(self):
        s = Settings()
        assert s.evidence_dir == Path(".csgr/evidence")

    def test_default_evidence_filename(self):
        s = Settings()
        assert s.evidence_filename == "evidence.jsonl"

    def test_evidence_path_property(self):
        s = Settings()
        assert s.evidence_path == Path(".csgr/evidence/evidence.jsonl")

    def test_default_drift_threshold(self):
        s = Settings()
        assert s.drift_z_threshold == 2.0

    def test_default_drift_min_baseline(self):
        s = Settings()
        assert s.drift_min_baseline == 5

    def test_default_determinism_runs(self):
        s = Settings()
        assert s.determinism_check_runs == 3

    def test_default_json_output(self):
        s = Settings()
        assert s.json_output is False

    def test_default_verbose(self):
        s = Settings()
        assert s.verbose is False

    def test_custom_evidence_dir(self):
        s = Settings(evidence_dir=Path("/tmp/custom"))
        assert s.evidence_dir == Path("/tmp/custom")
        assert s.evidence_path == Path("/tmp/custom/evidence.jsonl")

    def test_env_prefix(self):
        assert Settings.model_config["env_prefix"] == "CSGR_"
