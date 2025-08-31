from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOGS_DIR = Path(__file__).resolve().parents[1] / "logs"
_LOGS_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FILE = _LOGS_DIR / "error.log"

_configured = False

def get_logger(name: str = "contracts-ai"):
    global _configured
    logger = logging.getLogger(name)
    if not _configured:
        logger.setLevel(logging.INFO)
        # Rotating file handler: 2 MB x 5 backups
        fh = RotatingFileHandler(_LOG_FILE, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
        # Stream to console (Streamlit/pytest)
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        logger.addHandler(sh)
        _configured = True
    return logger


import json as _json
import traceback as _tb
import datetime as _dt
import logging as _logging

def make_run_logger(path):
    lg = _logging.getLogger(f"run.{path}")
    if getattr(lg, "_configured", False):
        return lg
    fh = _logging.FileHandler(path, encoding="utf-8")
    fh.setLevel(_logging.INFO)
    fh.setFormatter(_logging.Formatter("%(message)s"))
    lg.addHandler(fh)
    lg.setLevel(_logging.INFO)
    lg.propagate = False
    lg._configured = True
    return lg

def log_event(lg, event, **data):
    rec = {"ts": _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z", "event": event}
    rec.update({k: v for k, v in data.items() if v is not None})
    try:
        lg.info(_json.dumps(rec, ensure_ascii=False))
    except Exception:
        lg.info(str(rec))

def log_exception(lg, err, **data):
    data = dict(data)
    data.update({"error": str(err), "exc_type": type(err).__name__, "traceback": _tb.format_exc()})
    log_event(lg, "exception", **data)
