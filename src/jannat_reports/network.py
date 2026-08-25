from __future__ import annotations

from pathlib import Path
import re
from typing import Any, Iterable

from openpyxl import load_workbook

from jannat_reports.commercial import parse_commercial_report
from jannat_reports.gm_august import parse_gm_august_report


def _day_key(value: str) -> tuple[int, int]:
    day, month = map(int, value.split("."))
    return month, day


def _sum_metric(hotels: list[dict[str, Any]], key: str, field: str) -> float:
    return sum(float(hotel["metrics"][key][field] or 0) for hotel in hotels)


CLAUDE_SLUGS = {
    "jrb": "bishkek",
    "jrkt": "koitash",
    "jrja": "jalalabad",
    "jro": "osh",
    "skk": "sultankk",
    "sb": "sultanbsh",
}


def _integer(value: Any) -> int:
    return round(float(value or 0))


def _top3(value: Any) -> list[str]:
    text = str(value or "").strip()
    if not text or (text.startswith("[") and text.endswith("]")):
        return []
    parts = [part.strip(" -•\t") for part in text.replace(";", "\n").splitlines()]
    return [part for part in parts if part][:3]


def _review_map(reviews: list[dict[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for item in reviews:
        platform = str(item.get("platform") or "").strip().casefold()
        if platform:
            result[platform] = item.get("rating") or 0
    return result


def _iso_date(hotel: dict[str, Any], sheet: str) -> str:
    value = str(hotel.get("meta", {}).get("date") or "")
    match = re.match(r"(20\d{2})-(\d{2})-(\d{2})", value)
    if match:
        return "-".join(match.groups())
    year = re.search(r"20\d{2}", str(hotel.get("source_file") or ""))
    day, month = sheet.split(".")
    return f"{year.group(0) if year else '2026'}-{month}-{day}"


def _claude_hotel(hotel: dict[str, Any]) -> dict[str, Any]:
    metric = lambda key: hotel["metrics"][key]
    day = lambda key: _integer(metric(key)["fact_day"])
    plans = {
        key: {
            "day": _integer(metric(key)["plan_day"]),
            "month": _integer(metric(key)["plan_month"]),
            "period": _integer(metric(key)["plan_accum"]),
        }
        for key in ("rooms_sold", "income", "variable_expenses", "fixed_expenses", "operating_expenses", "ebitda")
    }
    warnings = [check["name"] for check in hotel["checks"] if not check["ok"]]
    b2c, b2b, online, nf, income = (day(key) for key in ("b2c", "b2b", "online", "rooms_revenue", "income"))
    if abs(b2c + b2b + online - nf) > 2:
        warnings.append("Каналы B2C + B2B + Online не сходятся с ИТОГО НФ")
    if max(b2c, b2b, online) > income:
        warnings.append("Один из каналов номерного фонда превышает общий доход")
    return {
        "slug": CLAUDE_SLUGS[hotel["object_key"]],
        "source_file": hotel["source_file"],
        "rooms_sold": day("rooms_sold"),
        "occupancy": float(metric("occupancy")["fact_day"] or 0),
        "adr": day("adr"),
        "revpar": day("revpar"),
        "trevpar": day("trevpar"),
        "b2c": b2c,
        "b2b": b2b,
        "online": online,
        "nf": nf,
        "conf": day("conference"),
        "rest": day("restaurant"),
        "poolbar": day("pool_bar"),
        "banquet": day("banquet"),
        "sbt": day("sbt"),
        "med": day("medical"),
        "rent": day("rent"),
        "other_income": day("other_income"),
        "income": day("income"),
        "varexp": day("variable_expenses"),
        "fixexp": day("fixed_expenses"),
        "totexp": day("operating_expenses"),
        "gop": day("ebitda"),
        "plans": plans,
        "gm_notes": {
            "problem": hotel["operational"]["incident"],
            "action": hotel["operational"]["action"],
            "escalation": hotel["operational"]["escalation"],
            "top3": _top3(hotel["operational"]["tomorrow"]),
            "idea": hotel["operational"]["idea"],
        },
        "subscriptions": day("memberships"),
        "reviews": _review_map(hotel["reviews"]),
        "_warning": warnings,
        "_verified": not warnings,
    }


def build_claude_export(data: dict[str, Any]) -> dict[str, Any]:
    commercial = data.get("commercial")
    sales = None
    if commercial:
        sales = {
            "report_date": commercial["meta"]["date"],
            "head": commercial["meta"]["leader"],
            "managers_present": commercial["meta"]["staff"],
            "kpi": {
                "calls_plan": commercial["kpi"]["calls"]["plan_day"],
                "calls_fact": commercial["kpi"]["calls"]["fact_day"],
                "meetings_plan": commercial["kpi"]["meetings"]["plan_day"],
                "meetings_fact": commercial["kpi"]["meetings"]["fact_day"],
                "revenue_day": commercial["kpi"]["revenue"]["fact_day"],
                "revenue_month_plan": commercial["kpi"]["revenue"]["plan_month"],
                "revenue_month_fact": commercial["kpi"]["revenue"]["fact_month"],
            },
            "managers": commercial["managers"],
            "pipeline": commercial["pipeline"],
            "text": commercial["texts"],
            "_verified": commercial["verified"],
        }
    director_tasks = [
        {"icon": "📄", "title": title, "desc": text}
        for title, text in (data.get("director_notes") or {}).items()
    ]
    report_date = _iso_date(data["hotels"][0], data["report_sheet"])
    return {
        "schema_version": "jannat_daily_v1",
        "report_date": report_date,
        "report_sheet": data["report_sheet"],
        "period": {"from": data["daily_reports"][0]["sheet"], "to": data["daily_reports"][-1]["sheet"]},
        "days": [
            {
                "report_date": _iso_date(item["hotels"][0], item["sheet"]),
                "objects": [_claude_hotel(hotel) for hotel in item["hotels"]],
            }
            for item in data["daily_reports"]
        ],
        "objects": [_claude_hotel(hotel) for hotel in data["hotels"]],
        "sales_dept": sales,
        "director_tasks": director_tasks,
        "checks": data["checks"],
        "verified": data["verified"],
    }


def parse_network_report(
    gm_paths: Iterable[str | Path],
    commercial_path: str | Path | None = None,
    director_notes: dict[str, Any] | None = None,
    target_sheet: str | None = None,
) -> dict[str, Any]:
    gm_paths = [Path(path) for path in gm_paths]
    if not gm_paths:
        raise ValueError("Для консолидации нужен хотя бы один GM-отчёт")

    workbooks = {path: load_workbook(path, data_only=True) for path in gm_paths}
    previews = [parse_gm_august_report(path, workbook=workbooks[path]) for path in gm_paths]
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

    ordered_common_dates = sorted(common_dates, key=_day_key)
    daily_reports = []
    for sheet_name in ordered_common_dates:
        day_hotels = [
            parse_gm_august_report(path, target_sheet=sheet_name, workbook=workbooks[path])
            for path in gm_paths
        ]
        day_hotels.sort(key=lambda item: item["object_key"] or "")
        daily_reports.append({"sheet": sheet_name, "hotels": day_hotels})
    hotels = daily_reports[-1]["hotels"]
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
        "daily_reports": daily_reports,
    }
