#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, datetime
from pathlib import Path

try:
    import yaml
except Exception:
    yaml = None

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip() if (ROOT / "VERSION").exists() else "0.0.0"
CHANGELOG = ROOT / "CHANGELOG.md"
ARCH_LOG = DOCS / "ARCHITECTURE_CHANGELOG.md"
STATE = DOCS / "PROJECT_STATE.yaml"

def append(p: Path, line: str):
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as f:
        if not line.endswith("\n"):
            line += "\n"
        f.write(line)

def main():
    ctype = os.getenv("CHANGE_TYPE","feat")
    summary = os.getenv("CHANGE_SUMMARY","Routine maintenance")
    details = os.getenv("CHANGE_DETAILS","")
    area = os.getenv("CHANGE_AREA","Architecture")
    affected = os.getenv("CHANGE_AFFECTED","")
    today = datetime.date.today().isoformat()

    append(ARCH_LOG, f"## {today} - v{VERSION}")
    append(ARCH_LOG, f"- ({ctype}) {summary}")

    append(CHANGELOG, f"### {area}")
    append(CHANGELOG, f"- ({ctype}) {summary}")
    if details: append(CHANGELOG, f"  - {details}")
    if affected: append(CHANGELOG, f"  - Affected: {affected}")

    if yaml is not None:
        state = {
            "app":{"name":"contracts-ai","version":VERSION,"env":os.getenv("APP_ENV","dev")},
            "commands":{"setup":"make setup","run_api":"make run-api","run_ui":"make run-ui","lint":"make lint","test":"make test","e2e":"make e2e","release":"make release"},
            "architecture":{"style":"Modular Monolith","paths":{"backend":"backend/app","frontend":"frontend","tests":"backend/tests","docs":"docs","data":"data","legacy":"legacy"},
                            "components":{"api_v1":"backend/app/api/v1","application":"backend/app/application","domain":"backend/app/domain","infrastructure":"backend/app/infrastructure","schemas":"backend/app/schemas","core":"backend/app/core"}},
            "policies":{"logging_schema":["ts","level","message","logger","component","version","request_id","correlation_id","user_id","span_id"],"versioning":"SemVer"}
        }
        STATE.write_text(yaml.safe_dump(state, sort_keys=False, allow_unicode=True), encoding="utf-8")

if __name__ == "__main__":
    main()
