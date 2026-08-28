from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


def _number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def build_analysis_payload(report: dict[str, Any]) -> dict[str, Any]:
    """Build a compact management payload so API usage stays predictable."""
    latest = report.get("objects") or []
    period_rows: list[dict[str, Any]] = []
    for current in latest:
        slug = current.get("slug")
        rows = [
            item
            for day in report.get("days") or []
            for item in day.get("objects") or []
            if item.get("slug") == slug
        ]
        period_rows.append({
            "hotel": current.get("name") or slug,
            "income": round(sum(_number(row.get("income")) for row in rows)),
            "expenses": round(sum(_number(row.get("totexp")) for row in rows)),
            "gop": round(sum(_number(row.get("gop")) for row in rows)),
            "rooms_sold": round(sum(_number(row.get("rooms_sold")) for row in rows)),
            "plan_income": round(sum(_number((row.get("plans") or {}).get("income", {}).get("day")) for row in rows)),
            "plan_gop": round(sum(_number((row.get("plans") or {}).get("ebitda", {}).get("day")) for row in rows)),
        })
    return {
        "report_date": report.get("report_date"),
        "period": report.get("period"),
        "day_objects": latest,
        "period_objects": period_rows,
        "sales_dept": report.get("sales_dept"),
        "director_tasks": report.get("director_tasks"),
        "data_checks": report.get("checks"),
        "verified": report.get("verified"),
    }


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("Claude не вернул JSON")
    result = json.loads(text[start:end + 1])
    if not isinstance(result, dict):
        raise ValueError("Ответ Claude должен быть объектом JSON")
    return result


def analyze_with_claude(report: dict[str, Any]) -> dict[str, Any] | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        return None
    prompt = """Ты — аналитик директора сети отелей Jannat Hotels & Resorts.
Проанализируй только предоставленные цифры. Не выдумывай причины и факты.
Сопоставь день и период с планами, отметь качество данных и управленческие риски.
Денежные показатели указаны в сомах. Ответ дай на русском языке строго как JSON:
{
  "executive_summary": "4–6 предложений для руководителя",
  "highlights": ["до 5 подтверждённых сильных результатов"],
  "risks": [{"hotel":"объект или сеть", "issue":"факт", "impact":"почему важно"}],
  "actions": [{"priority":"высокий|средний|низкий", "action":"конкретное действие", "owner":"ответственный", "deadline":"срок"}],
  "hotel_insights": [{"hotel":"название", "status":"сильный|внимание|критично", "insight":"краткий вывод"}],
  "voice_summary": "связный текст для голосовой сводки длительностью до 2 минут"
}
Если данных недостаточно, прямо укажи это в соответствующем выводе.

ДАННЫЕ:
""" + json.dumps(build_analysis_payload(report), ensure_ascii=False, separators=(",", ":"))
    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps({
            "model": os.environ.get("CLAUDE_MODEL", "claude-sonnet-5"),
            "max_tokens": 2200,
            "temperature": 0.1,
            "messages": [{"role": "user", "content": prompt}],
        }).encode("utf-8"),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
            "user-agent": "jannat-report-automation/1.0",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"Claude API: HTTP {error.code}: {detail}") from error
    blocks = body.get("content") or []
    text = "\n".join(str(block.get("text") or "") for block in blocks if block.get("type") == "text")
    result = _extract_json(text)
    result["model"] = body.get("model")
    result["usage"] = body.get("usage") or {}
    return result
