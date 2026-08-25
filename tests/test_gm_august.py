from pathlib import Path

from jannat_reports.gm_august import parse_gm_august_report


SAMPLE = Path(__file__).parents[1] / "sample_input" / "GM_JRB_Август2026_v18.xlsx"


def test_uses_last_actually_filled_day():
    data = parse_gm_august_report(SAMPLE)
    assert data["meta"]["latest_sheet"] == "12.08"
    assert data["meta"]["filled_days"] == 12
    assert data["metrics"]["income"]["fact_accum"] == 4_737_134


def test_financial_checks_pass():
    data = parse_gm_august_report(SAMPLE)
    assert data["verified"] is True
    assert all(check["ok"] for check in data["checks"])


def test_reads_room_channels_and_reviews():
    data = parse_gm_august_report(SAMPLE)
    assert data["metrics"]["b2c"]["fact_accum"] == 392_068
    assert data["metrics"]["b2b"]["fact_accum"] == 1_693_845
    assert data["reviews"][0]["platform"] == "Booking.com"
    assert data["reviews"][0]["rating"] == 7.3
