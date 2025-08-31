#!/usr/bin/env python3
import sys, pathlib
root = pathlib.Path(__file__).resolve().parents[1]
c = root / "CHANGELOG.md"
exit(0) if c.exists() and c.stat().st_size > 0 else (print("ERROR: CHANGELOG missing/empty"), sys.exit(1))
