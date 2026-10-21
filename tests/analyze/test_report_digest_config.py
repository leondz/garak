"""Keep rebuilt digest scores and labels tied to the intended configuration."""

import json
from pathlib import Path
from types import SimpleNamespace

from garak import _config
from garak.analyze.report_digest import build_digest


def _report_with_scores(tmp_path, aggregation_function):
    source = Path(__file__).parents[1] / "_assets" / "analyze" / "test.report.jsonl"
    with source.open(encoding="utf-8") as report:
        setup = json.loads(next(report))
        init = next(report)
    if aggregation_function is None:
        setup.pop("reporting.group_aggregation_function", None)
    else:
        setup["reporting.group_aggregation_function"] = aggregation_function

    report_path = tmp_path / "different_aggregation.report.jsonl"
    evaluations = [
        {
            "entry_type": "eval",
            "probe": "test.Test",
            "detector": detector,
            "passed": passed,
            "total_evaluated": 1,
        }
        for detector, passed in (("always.Pass", 1), ("always.Fail", 0))
    ]
    report_path.write_text(
        json.dumps(setup)
        + "\n"
        + init
        + "".join(json.dumps(entry) + "\n" for entry in evaluations),
        encoding="utf-8",
    )
    return report_path


def test_rebuilt_digest_uses_saved_aggregation(tmp_path, monkeypatch):
    _config.load_base_config()
    monkeypatch.setattr(
        _config.reporting, "group_aggregation_function", "lower_quartile"
    )
    report_path = _report_with_scores(tmp_path, "mean")

    digest = build_digest(str(report_path))

    summary = digest["eval"]["test"]["_summary"]
    assert summary["score"] == 0.5, "the saved mean should determine the group score"
    assert (
        summary["group_aggregation_function"] == "mean"
    ), "group metadata should name the saved aggregation"
    assert (
        digest["meta"]["group_aggregation_function"] == "mean"
    ), "report metadata should name the saved aggregation"


def test_explicit_digest_config_overrides_saved_aggregation(tmp_path, monkeypatch):
    _config.load_base_config()
    monkeypatch.setattr(
        _config.reporting, "group_aggregation_function", "lower_quartile"
    )
    report_path = _report_with_scores(tmp_path, "minimum")

    config = SimpleNamespace(
        reporting=SimpleNamespace(group_aggregation_function="mean", taxonomy=None)
    )
    digest = build_digest(str(report_path), config=config)

    summary = digest["eval"]["test"]["_summary"]
    assert summary["score"] == 0.5, "the explicit mean should determine the group score"
    assert (
        summary["group_aggregation_function"] == "mean"
    ), "group metadata should name the explicit aggregation"
    assert (
        digest["meta"]["group_aggregation_function"] == "mean"
    ), "report metadata should name the explicit aggregation"


def test_rebuilt_digest_uses_current_aggregation_for_older_reports(
    tmp_path, monkeypatch
):
    _config.load_base_config()
    monkeypatch.setattr(
        _config.reporting, "group_aggregation_function", "lower_quartile"
    )
    report_path = _report_with_scores(tmp_path, None)

    digest = build_digest(str(report_path))

    summary = digest["eval"]["test"]["_summary"]
    assert summary["score"] == 0.25, "older reports should use the current method"
    assert (
        summary["group_aggregation_function"] == "lower_quartile"
    ), "group metadata should name the current method"
