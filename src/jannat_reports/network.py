from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from jannat_reports.commercial import parse_commercial_report
from jannat_reports.gm_august import parse_gm_august_report


def _day_key(value: str) -> tuple[int, int]:
    day, month = map(int, value.split("."))
    return month, day


def _sum_metric(hotels: list[dict[str, Any]], key: str, field: str) -> float:
    return sum(float(hotel["metrics"][key][field] or 0) for hotel in hotels)


def parse_network_report(
    gm_paths: Iterable[str | Path],
    commercial_path: str | Path | None = None,
    director_notes: dict[str, Any] | None = None,
    target_sheet: str | None = None,
) -> dict[str, Any]:
    gm_paths = [Path(path) for path in gm_paths]
    if not gm_paths:
        raise ValueError("Для консолидации нужен хотя бы один GM-отчёт")

    previews = [parse_gm_august_report(path) for path in gm_paths]
    object_keys = [item["object_key"] for item in previews]
    if None in object_keys:
        raise ValueError("Не удалось определить объект одного из GM-файлов")
    if len(set(object_keys)) != len(object_keys):
        raise ValueError("Получено несколько GM-файлов одного объекта")

    common_dates = set(previews[0]["filled_sheet_names"])
    for preview in previews[1:]:
        common_dates &= set(preview["filled_sheet_names"])
    if target_sheet:
        if target_sheet not in common_dates:
            raise ValueError(f"Дата {target_sheet} заполнена не во всех полученных отчётах")
        report_sheet = target_sheet
    else:
        if not common_dates:
            raise ValueError("У GM-отчётов нет общей заполненной даты")
        report_sheet = max(common_dates, key=_day_key)

    hotels = [parse_gm_august_report(path, target_sheet=report_sheet) for path in gm_paths]
    hotels.sort(key=lambda item: item["object_key"] or "")
    metric_keys = (
        "rooms_sold", "b2c", "b2b", "online", "rooms_revenue", "income",
        "income_net", "operating_expenses", "ebitda", "net_profit",
    )
    totals = {
        key: {
            "plan_month": _sum_metric(hotels, key, "plan_month"),
            "fact_day": _sum_metric(hotels, key, "fact_day"),
            "fact_accum": _sum_metric(hotels, key, "fact_accum"),
        }
        for key in metric_keys
    }
    totals["room_fund"] = sum(int(hotel["meta"]["room_fund"] or 0) for hotel in hotels)
    totals["income_completion"] = (
        totals["income"]["fact_accum"] / totals["income"]["plan_month"]
        if totals["income"]["plan_month"] else 0
    )
    totals["ebitda_margin"] = (
        totals["ebitda"]["fact_accum"] / totals["income"]["fact_accum"]
        if totals["income"]["fact_accum"] else 0
    )

    commercial = parse_commercial_report(commercial_path) if commercial_path else None
    checks = [
        {
            "name": f"{hotel['meta']['hotel']}: контроль формул",
            "ok": hotel["verified"],
        }
        for hotel in hotels
    ]
    if commercial:
        checks.append({"name": "Коммерческий отдел: контроль итогов", "ok": commercial["verified"]})

    return {
        "report_type": "network_consolidated",
        "report_sheet": report_sheet,
        "hotels": hotels,
        "totals": totals,
        "commercial": commercial,
        "director_notes": director_notes or {},
        "checks": checks,
        "verified": all(check["ok"] for check in checks),
        "included_objects": object_keys,
    }
