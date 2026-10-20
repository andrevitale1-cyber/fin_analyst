"""Keep unit tests offline; runtime metrics and queue workers have dedicated tests."""
from pathlib import Path
import sys
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(autouse=True)
def isolate_runtime_side_effects(monkeypatch):
    import full_reports
    import agents.report_pipeline as pipeline
    monkeypatch.setenv("REPORT_JOB_WORKER", "0")
    monkeypatch.setattr(full_reports, "record_run", lambda *args, **kwargs: None)
    monkeypatch.setattr(pipeline, "checkpoint", lambda stage, identity, compute: compute())
