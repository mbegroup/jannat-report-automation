from pathlib import Path

from jannat_reports.commercial import parse_commercial_report


SAMPLE = Path(__file__).parents[1] / "sample_input" / "Jannat_Sales_Daily_Template.xlsx"


def test_parses_verified_manager_total():
    data = parse_commercial_report(SAMPLE)
    assert data["meta"]["date"] == "2026-07-16T00:00:00"
    assert data["detail_totals"]["revenue"] == 1_812_170
    assert data["reported_totals"]["revenue"] == 1_812_170


def test_detects_kpi_omissions():
    data = parse_commercial_report(SAMPLE)
    failed = {x["name"] for x in data["checks"] if not x["ok"]}
    assert "KPI встреч" in failed
    assert "KPI выручки дня" in failed

