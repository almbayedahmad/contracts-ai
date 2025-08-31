
from __future__ import annotations
import re
from typing import List, Optional
from core.schemas import ExtractBatch, ExtractItem

# --- Intro block (parties) ---
PARTY_BLOCK = re.compile(r'Zwischen(.*?)wird folgender Vertrag', re.S | re.I)
FOLGEN = re.compile(r'im\s+Folgenden', re.I)

# --- Section headers (tolerant) ---
SEC1 = re.compile(r'(§\s*1\s+Vertragsgegenstand|^\s*1[.)]?\s+Vertragsgegenstand)', re.I | re.M)
SEC2 = re.compile(r'(§\s*2\s+(Pflichten|Leistungsumfang)|^\s*2[.)]?\s+(Pflichten|Leistungsumfang))', re.I | re.M)
SEC3 = re.compile(r'(§\s*3\s+(Vergütung|Verguetung|Zahlung)|^\s*3[.)]?\s+(Vergütung|Verguetung|Zahlung))', re.I | re.M)
SEC4 = re.compile(r'(§\s*4\s+(Vertragsdauer|Laufzeit|Kündigung|Kuendigung)|^\s*4[.)]?\s+(Vertragsdauer|Laufzeit|Kündigung|Kuendigung))', re.I | re.M)

def _find_section(text: str, rx_start, next_rxs) -> Optional[re.Match]:
    m = rx_start.search(text)
    if not m:
        return None
    start = m.start()
    end = len(text)
    for rx in next_rxs:
        n = rx.search(text, m.end())
        if n:
            end = min(end, n.start())
    return (start, end)

def _slice(text: str, span) -> str:
    s, e = span
    return text[s:e].strip()

def _split_parties(block: str):
    b = block.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.strip() for ln in b.split("\n")]
    lines = [ln for ln in lines if ln and not FOLGEN.search(ln)]
    und_idx = next((i for i, ln in enumerate(lines) if ln.lower()=="und"), None)
    if und_idx is None:
        mid = len(lines)//2
        return [lines[:mid], lines[mid:]]
    before = [ln for ln in lines[:und_idx] if ln.lower()!="zwischen"]
    after  = [ln for ln in lines[und_idx+1:]]
    return [before, after]

def _pack_party(chunk: list[str]):
    chunk = [c for c in chunk if c.lower() not in ("zwischen","und")]
    if not chunk:
        return {"name":"", "addr":""}
    name = chunk[0]
    addr = "\n".join(chunk[1:4])
    return {"name": name, "addr": addr}

# --- §3 patterns ---
RE_MONEY = re.compile(r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*(EUR|€)', re.I)
RE_VAT = re.compile(r'(?:Umsatzsteuer|MwSt)[^%]{0,80}?(?:derzeit\s*)?(\d{1,2})%', re.I)
RE_PAY_DAYS = re.compile(r'(\d{1,3})\s*Tage\s+nach\s+Rechnungserhalt', re.I)

# --- §4 patterns ---
RE_START = re.compile(r'tritt\s+am\s+(\d{1,2}\.\d{1,2}\.\d{2,4})\s+in\s+Kraft', re.I)
RE_END = re.compile(r'endet\s+am\s+(\d{1,2}\.\d{1,2}\.\d{2,4})', re.I)
RE_TERM_WEEKS = re.compile(r'Frist\s+von\s+(\d{1,2})\s*Wochen\s+zum\s+Monatsende', re.I)

def _norm_money_de(s: str) -> float:
    s = s.replace(".", "").replace(",", ".")
    try:
        return float(s)
    except Exception:
        return None

def _norm_date_de(s: str) -> str:
    m = re.match(r'(\d{1,2})\.(\d{1,2})\.(\d{2,4})', s)
    if not m:
        return s
    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if y < 100:
        y += 2000
    return f"{y:04d}-{mo:02d}-{d:02d}"

# --- Contract Type ---
CONTRACT_TYPE = re.compile(r'\b(Dienstleistungsvertrag|Werkvertrag|Kaufvertrag|Mietvertrag|Lizenzvertrag|Servicevertrag)\b', re.I)

class ServiceContractExtractor:
    __name__ = "ServiceContractExtractor"
    __version__ = "1.4.0"

    def extract(self, doc_id: str, text: str) -> ExtractBatch:
        items: List[ExtractItem] = []

        # Contract type (title-level)
        mt = CONTRACT_TYPE.search(text)
        if mt:
            items.append(ExtractItem(
                item_type="clause", subtype="contract_type",
                text_raw=mt.group(0), value_norm=mt.group(1),
                page=None, para=None, start=None, end=None,
                extractor=self.__class__.__name__, version=self.__version__, confidence=0.95,
            ))

        # Parties (intro)
        pb = PARTY_BLOCK.search(text)
        if pb:
            parts = _split_parties(pb.group(1))
            for ch in parts[:2]:
                p = _pack_party(ch)
                name = p["name"]
                if not name or name.lower() in ("und", "zwischen"):
                    continue
                subtype = "company" if ("GmbH" in name or "AG" in name or "UG" in name or "SE" in name or "KG" in name or "OHG" in name or "GbR" in name or "e.V." in name) else "individual"
                items.append(ExtractItem(
                    item_type="party", subtype=subtype,
                    text_raw=(name + ("\n"+p["addr"] if p["addr"] else "")).strip(),
                    value_norm=name,
                    page=None, para=None, start=pb.start(), end=pb.end(),
                    extractor=self.__class__.__name__,
                    version=self.__version__, confidence=0.97,
                ))

        # Sections spans
        s1 = _find_section(text, SEC1, [SEC2, SEC3, SEC4])
        s2 = _find_section(text, SEC2, [SEC3, SEC4])
        s3 = _find_section(text, SEC3, [SEC4])
        s4 = _find_section(text, SEC4, [])

        # §1 subject (full text)
        if s1:
            sec = _slice(text, s1)
            items.append(ExtractItem(
                item_type="clause", subtype="subject",
                text_raw=sec, value_norm=None,
                page=None, para=None, start=s1[0], end=s1[1],
                extractor=self.__class__.__name__, version=self.__version__, confidence=0.94,
            ))

        # §2 obligations (full text)
        if s2:
            sec = _slice(text, s2)
            items.append(ExtractItem(
                item_type="clause", subtype="obligations",
                text_raw=sec, value_norm=None,
                page=None, para=None, start=s2[0], end=s2[1],
                extractor=self.__class__.__name__, version=self.__version__, confidence=0.9,
            ))

        # §3 financials
        if s3:
            sec3 = _slice(text, s3)
            # total fee
            mfee = RE_MONEY.search(sec3)
            if mfee:
                val = _norm_money_de(mfee.group(1))
                cur = "EUR"
                items.append(ExtractItem(
                    item_type="money", subtype="total_fee",
                    text_raw=mfee.group(0), value_norm=val, 
                    page=None, para=None, start=s3[0], end=s3[1],
                    unit=None, extractor=self.__class__.__name__,
                    version=self.__version__, currency=cur, confidence=0.9,
                ))
            # VAT
            mvat = RE_VAT.search(sec3)
            if mvat:
                items.append(ExtractItem(
                    item_type="other", subtype="vat_rate_percent",
                    text_raw=mvat.group(0), value_norm=float(mvat.group(1)),
                    page=None, para=None, start=s3[0], end=s3[1],
                    unit="percent", extractor=self.__class__.__name__,
                    version=self.__version__, currency=None, confidence=0.88,
                ))
            # Payment terms
            mpay = RE_PAY_DAYS.search(sec3)
            if mpay:
                items.append(ExtractItem(
                    item_type="other", subtype="payment_terms_days_after_invoice",
                    text_raw=mpay.group(0), value_norm=int(mpay.group(1)),
                    page=None, para=None, start=s3[0], end=s3[1],
                    unit="days", extractor=self.__class__.__name__,
                    version=self.__version__, currency=None, confidence=0.9,
                ))

        # §4 dates & termination
        if s4:
            sec4 = _slice(text, s4)
            ms = RE_START.search(sec4)
            if ms:
                items.append(ExtractItem(
                    item_type="date", subtype="start_date",
                    text_raw=ms.group(0), value_norm=_norm_date_de(ms.group(1)),
                    page=None, para=None, start=s4[0], end=s4[1],
                    extractor=self.__class__.__name__, version=self.__version__, confidence=0.9,
                ))
            me = RE_END.search(sec4)
            if me:
                items.append(ExtractItem(
                    item_type="date", subtype="end_date",
                    text_raw=me.group(0), value_norm=_norm_date_de(me.group(1)),
                    page=None, para=None, start=s4[0], end=s4[1],
                    extractor=self.__class__.__name__, version=self.__version__, confidence=0.9,
                ))
            mt = RE_TERM_WEEKS.search(sec4)
            if mt:
                items.append(ExtractItem(
                    item_type="other", subtype="termination_notice_weeks_to_month_end",
                    text_raw=mt.group(0), value_norm=int(mt.group(1)),
                    page=None, para=None, start=s4[0], end=s4[1],
                    unit="weeks", extractor=self.__class__.__name__, version=self.__version__, confidence=0.88,
                ))

        return ExtractBatch(doc_id=doc_id, items=items)
