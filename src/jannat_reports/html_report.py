from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Template


TEMPLATE = r'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Jannat — отчёт коммерческого директора</title><style>
:root{--gold:#B8952A;--dark:#1A1A2E;--charcoal:#2D2D44;--mist:#F7F6F3;--green:#2D7A4F;--red:#C0392B;--amber:#D4820A;--border:#E8E4DB}*{box-sizing:border-box}body{margin:0;background:var(--mist);font:14px Inter,Arial;color:#252538}header{background:var(--dark);color:#fff;padding:26px max(16px,calc((100% - 1180px)/2));border-bottom:4px solid var(--gold)}h1{margin:0 0 7px;font:28px Georgia}.wrap{max-width:1180px;margin:auto;padding:18px}.summary{display:grid;grid-template-columns:repeat(3,1fr);gap:10px}.card,.panel{background:#fff;border:1px solid var(--border);border-radius:12px;padding:16px;margin-bottom:14px}.value{font-size:25px;font-weight:800;margin-top:6px}.ok{color:var(--green)}.bad{color:var(--red)}.warn{color:var(--amber)}table{width:100%;border-collapse:collapse;min-width:760px}th{background:var(--charcoal);color:#fff}th,td{padding:10px;border:1px solid var(--border);text-align:left}.tbl{overflow:auto}.pill{display:inline-block;padding:4px 8px;border-radius:999px;background:#eee;font-weight:700}.pill.ok{background:#e8f5ee}.pill.bad{background:#fdeeed}h2{font:22px Georgia;margin:4px 0 14px}@media(max-width:600px){.wrap{padding:14px}.summary{gap:5px}.card{padding:9px}.value{font-size:14px}.card small{font-size:8px}h1{font-size:22px}}
</style></head><body><header><h1>JANNAT HOTELS & RESORTS</h1><div>Отчёт коммерческого директора · {{ d.meta.date }} · Директор по отелям Курманжан Тыналиева</div></header><main class="wrap">
<section class="summary"><div class="card"><small>Выручка дня</small><div class="value">{{ money(d.detail_totals.revenue) }}</div></div><div class="card"><small>План дня</small><div class="value">{{ money(d.kpi.revenue.plan_day) }}</div></div><div class="card"><small>Выполнение</small><div class="value {{ 'ok' if day_pct >= 100 else 'warn' }}">{{ day_pct }}%</div></div></section>
<section class="panel"><h2>Python-верификация</h2>{% for c in d.checks %}<p><span class="pill {{ 'ok' if c.ok else 'bad' }}">{{ 'OK' if c.ok else 'РАСХОЖДЕНИЕ' }}</span> {{ c.name }} · ожидалось {{ c.expected }} · в KPI/итоге {{ c.actual }}</p>{% endfor %}{% if not d.online_filled %}<p class="bad">Онлайн-лист не заполнен — требуется факт Booking / OTA.</p>{% endif %}</section>
<section class="panel"><h2>Менеджеры</h2><div class="tbl"><table><thead><tr><th>Менеджер</th><th>Звонки</th><th>Встречи</th><th>Компании</th><th>Контракты</th><th>Выручка</th><th>Фокус</th></tr></thead><tbody>{% for m in d.managers %}<tr><td>{{ m.name }}</td><td>{{ m.calls }}</td><td>{{ m.meetings }}</td><td>{{ m.companies }}</td><td>{{ m.contracts }}</td><td>{{ money(m.revenue) }}</td><td>{{ m.focus or '—' }}</td></tr>{% endfor %}</tbody></table></div></section>
<section class="panel"><h2>Месяц и пайплайн</h2><p>План месяца: <b>{{ money(d.kpi.revenue.plan_month) }}</b> · факт: <b>{{ money(d.kpi.revenue.fact_month) }}</b> · выполнение: <b>{{ month_pct }}%</b></p><p>Пайплайн: <b>{{ money(d.pipeline_total) }}</b></p><div class="tbl"><table><thead><tr><th>Клиент</th><th>Объект</th><th>Период</th><th>Сумма</th><th>Следующий шаг</th></tr></thead><tbody>{% for p in d.pipeline %}<tr><td>{{ p.client }}</td><td>{{ p.object }}</td><td>{{ p.period }}</td><td>{{ money(p.amount) }}</td><td>{{ p.next_step }}</td></tr>{% endfor %}</tbody></table></div></section>
<section class="panel"><h2>Текстовый отчёт</h2><p><b>Результат:</b> {{ d.texts.result or '—' }}</p><p><b>Проблема:</b> {{ d.texts.problem or '—' }}</p><p><b>Что предпринято:</b> {{ d.texts.action or '—' }}</p><p><b>Задачи на завтра:</b> {{ d.texts.tomorrow or '—' }}</p><p><b>Идея:</b> {{ d.texts.idea or '—' }}</p></section>
</main></body></html>'''


def render_report(data: dict, output: str | Path) -> None:
    money = lambda x: f"{round(float(x or 0)):,}".replace(",", " ") + " сом"
    revenue = data["detail_totals"]["revenue"]
    plan_day = data["kpi"]["revenue"]["plan_day"]
    plan_month = data["kpi"]["revenue"]["plan_month"]
    fact_month = data["kpi"]["revenue"]["fact_month"]
    html = Template(TEMPLATE).render(d=data, money=money, day_pct=round(revenue / plan_day * 100, 1) if plan_day else 0, month_pct=round(fact_month / plan_month * 100, 1) if plan_month else 0)
    Path(output).write_text(html, encoding="utf-8")

