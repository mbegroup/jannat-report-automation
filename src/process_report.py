from __future__ import annotations

import argparse
import json
from pathlib import Path

from jannat_reports.commercial import parse_commercial_report
from jannat_reports.gm_august import parse_gm_august_report
from jannat_reports.gm_html import render_gm_report
from jannat_reports.html_report import render_report
from jannat_reports.network import parse_network_report
from jannat_reports.network_html import render_network_report


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", action="append", required=True)
    p.add_argument("--html", default="public/index.html")
    p.add_argument("--json", default="public/latest.json")
    p.add_argument("--notes-json")
    args = p.parse_args()
    inputs = [Path(value) for value in args.input]
    gm_inputs = [value for value in inputs if value.name.lower().startswith("gm_")]
    commercial_inputs = [value for value in inputs if value not in gm_inputs]
    director_notes = None
    if args.notes_json:
        notes = json.loads(Path(args.notes_json).read_text(encoding="utf-8"))
        if isinstance(notes, list):
            director_notes = {f"Заметка {index + 1}": text for index, text in enumerate(notes)}
        elif isinstance(notes, dict):
            director_notes = notes
    if len(gm_inputs) > 1:
        data = parse_network_report(
            gm_inputs,
            commercial_inputs[0] if commercial_inputs else None,
            director_notes=director_notes,
        )
        renderer = render_network_report
    elif gm_inputs:
        data = parse_gm_august_report(gm_inputs[0])
        renderer = render_gm_report
    else:
        data = parse_commercial_report(commercial_inputs[0])
        renderer = render_report
    Path(args.html).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    renderer(data, args.html)
    print(f"Готово: {args.html}; verified={data['verified']}")


if __name__ == "__main__":
    main()
