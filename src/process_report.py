from __future__ import annotations

import argparse
import json
from pathlib import Path

from jannat_reports.commercial import parse_commercial_report
from jannat_reports.html_report import render_report


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--input", required=True)
    p.add_argument("--html", default="public/index.html")
    p.add_argument("--json", default="public/latest.json")
    args = p.parse_args()
    data = parse_commercial_report(args.input)
    Path(args.html).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).parent.mkdir(parents=True, exist_ok=True)
    Path(args.json).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    render_report(data, args.html)
    print(f"Готово: {args.html}; verified={data['verified']}")


if __name__ == "__main__":
    main()

