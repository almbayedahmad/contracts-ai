# extractors/dummy.py — minimal extractor to keep UI working
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
import re

from pipeline.summarize import summarize_keyfacts
from pipeline.normalize import normalize_spans

AVAILABLE_EXTRACTORS = ["dummy"]
DEFAULT_EXTRACTOR = "dummy"

# التعرّف البسيط على كيانات (heuristics)
_WORD_RE = re.compile(r"\b([A-Z][a-z]{3,}|[A-Za-z]{4,}|[ء-ي]{3,})\b")
_NUM_RE  = re.compile(r"\d+(?:[.,]\d+)?")
_CUR_RE  = re.compile(r"(USD|EUR|SAR|AED|QAR|KWD|OMR|EGP|\$|€|£|ريال|درهم|دينار|جنيه)", re.I)
_DATE_RE = re.compile(r"(\d{4}-\d{1,2}-\d{1,2}|\d{1,2}/\d{1,2}/\d{2,4})")

def get(name: Optional[str] = None) -> str:
    return name or DEFAULT_EXTRACTOR

def list_available() -> List[str]:
    return AVAILABLE_EXTRACTORS[:]

def extract_entities(text: str) -> List[Dict[str, Any]]:
    ents: List[Dict[str, Any]] = []
    for m in _WORD_RE.finditer(text or ""):
        span = m.span()
        t = m.group(0)
        ents.append({"id": f"ent_{span[0]}_{span[1]}", "text": t, "type": "TERM", "start": span[0], "end": span[1]})
    return ents[:50]  # لا نبالغ

def extract_spans(text: str) -> List[Dict[str, Any]]:
    spans: List[Dict[str, Any]] = []
    for pat, label in ((_NUM_RE, "NUMBER"), (_CUR_RE, "CURRENCY"), (_DATE_RE, "DATE")):
        for m in pat.finditer(text or ""):
            s, e = m.span()
            spans.append({"start": s, "end": e, "text": m.group(0), "label": label, "confidence": 0.5})
    return spans

def extract_tables(tables: Any = None) -> Dict[str, Any]:
    # ارجع كما هو بشكل موحّد
    if isinstance(tables, dict):
        return {"rows": tables.get("rows") or []}
    if isinstance(tables, list):
        return {"rows": tables}
    return {"rows": []}

def extract_all(text: str = "", tables: Any = None, **kwargs) -> Dict[str, Any]:
    ents = extract_entities(text or "")
    spans = extract_spans(text or "")
    tbls = extract_tables(tables)
    keyfacts = summarize_keyfacts(text or "", max_items=5)
    # طَبِّع الـ spans
    spans_n = normalize_spans(spans)
    return {
        "entities": ents,
        "spans": spans_n,
        "tables": tbls,
        "keyfacts": keyfacts,
        "meta": {"extractor": "dummy"}
    }
