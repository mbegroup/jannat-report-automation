from __future__ import annotations

from pathlib import Path

from jinja2 import Template


TEMPLATE = r'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Jannat — отчёт GM</title><style>
:root{--gold:#b8952a;--navy:#172033;--ink:#24283a;--bg:#f5f6f8;--line:#e2e5eb;--green:#287a4b;--red:#be3d35;--amber:#bd7900}*{box-sizing:border-box}body{margin:0;background:var(--bg);font:14px Arial;color:var(--ink)}header{background:var(--navy);color:#fff;border-bottom:4px solid var(--gold);padding:24px max(16px,calc((100% - 1180px)/2))}h1{margin:0 0 6px;font:27px Georgia}.wrap{max-width:1180px;margin:auto;padding:18px}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px}.card,.panel{background:#fff;border:1px solid var(--line);border-radius:12px;padding:15px;margin-bottom:14px}.value{font-size:23px;font-weight:800;margin-top:7px}.ok{color:var(--green)}.bad{color:var(--red)}.warn{color:var(--amber)}h2{font:21px Georgia;margin:2px 0 13px}.tbl{overflow:auto}table{border-collapse:collapse;width:100%;min-width:720px}th{background:#30394f;color:#fff}th,td{padding:9px;border:1px solid var(--line);text-align:left}.pill{display:inline-block;padding:4px 8px;border-radius:999px;font-weight:700}.pill.ok{background:#e6f4ec}.pill.bad{background:#fbe9e7}@media(max-width:700px){.grid{grid-template-columns:repeat(2,1fr)}.value{font-size:18px}}
</style></head><body><header><h1>{{ d.meta.hotel }}</h1><div>Ежедневный отчёт GM · {{ d.meta.date }} · заполнено {{ d.meta.filled_days }} из {{ d.meta.day_sheets }} дней</div></header><main class="wrap">
<section class="grid"><div class="card"><small>Доход накопительно</small><div class="value">{{ money(m.income.fact_accum) }}</div></div><div class="card"><small>EBITDA накопительно</small><div class="value {{ 'ok' if m.ebitda.fact_accum >= 0 else 'bad' }}">{{ money(m.ebitda.fact_accum) }}</div></div><div class="card"><small>Выполнение плана доходов</small><div class="value {{ 'ok' if income_pct >= pace_pct else 'warn' }}">{{ income_pct }}%</div></div><div class="card"><small>Продано номеров</small><div class="value">{{ number(m.rooms_sold.fact_accum) }}</div></div></section>
<section class="panel"><h2>Контроль данных</h2>{% for c in d.checks %}<p><span class="pill {{ 'ok' if c.ok else 'bad' }}">{{ 'OK' if c.ok else 'РАСХОЖДЕНИЕ' }}</span> {{ c.name }} · ожидалось {{ number(c.expected) }} · отчёт {{ number(c.actual) }}</p>{% endfor %}{% if d.meta.missing_before_latest %}<p class="bad">Пропущены дни до последней даты: {{ d.meta.missing_before_latest|join(', ') }}</p>{% endif %}</section>
<section class="panel"><h2>KPI и финансовый результат</h2><div class="tbl"><table><thead><tr><th>Показатель</th><th>План месяца</th><th>Факт дня</th><th>Накопительно</th><th>Выполнение</th></tr></thead><tbody>{% for key in ['rooms_sold','occupancy','adr','revpar','trevpar','income','operating_expenses','ebitda','net_profit','profitability'] %}{% set x=m[key] %}<tr><td>{{ x.label }}</td><td>{{ percent(x.plan_month) if x.unit == '%' else number(x.plan_month) }}</td><td>{{ percent(x.fact_day) if x.unit == '%' else number(x.fact_day) }}</td><td>{{ percent(x.fact_accum) if x.unit == '%' else number(x.fact_accum) }}</td><td>{{ percent(x.accum_pct) }}</td></tr>{% endfor %}</tbody></table></div></section>
<section class="panel"><h2>Номерной фонд по каналам</h2><div class="tbl"><table><thead><tr><th>Канал</th><th>План месяца</th><th>Факт дня</th><th>Накопительно</th><th>% плана</th></tr></thead><tbody>{% for key in ['b2c','b2b','online','rooms_revenue'] %}{% set x=m[key] %}<tr><td>{{ x.label }}</td><td>{{ money(x.plan_month) }}</td><td>{{ money(x.fact_day) }}</td><td>{{ money(x.fact_accum) }}</td><td>{{ percent(x.accum_pct) }}</td></tr>{% endfor %}</tbody></table></div></section>
<section class="panel"><h2>Оперативный блок GM</h2><p><b>Инцидент:</b> {{ d.operational.incident or '—' }}</p><p><b>Что предпринято:</b> {{ d.operational.action or '—' }}</p><p><b>Эскалация директору сети:</b> {{ d.operational.escalation or '—' }}</p><p><b>TOP-3 на завтра:</b> {{ d.operational.tomorrow or '—' }}</p><p><b>Идея:</b> {{ d.operational.idea or '—' }}</p></section>
</main></body></html>'''


def render_gm_report(data: dict, output: str | Path) -> None:
    number = lambda x: f"{round(float(x or 0)):,}".replace(",", " ")
    money = lambda x: number(x) + " сом"
    percent = lambda x: f"{float(x or 0) * 100:.1f}%"
    metrics = data["metrics"]
    income_plan = metrics["income"]["plan_month"]
    income_pct = round(metrics["income"]["fact_accum"] / income_plan * 100, 1) if income_plan else 0
    pace_pct = round(data["meta"]["filled_days"] / data["meta"]["day_sheets"] * 100, 1)
    html = Template(TEMPLATE).render(
        d=data,
        m=metrics,
        number=number,
        money=money,
        percent=percent,
        income_pct=income_pct,
        pace_pct=pace_pct,
    )
    Path(output).write_text(html, encoding="utf-8")
