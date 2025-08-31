
from __future__ import annotations
import re
import pandas as pd

# -------- Regexes --------
RE_MONEY_ANY = re.compile(r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*(EUR|€)?', re.I)
RE_VERG = re.compile(r"\bVergütung\b", re.I)
RE_TOTAL_FEE_SENT = re.compile(r"Vergütung\s+beträgt", re.I)
RE_EUR = re.compile(r"\bEUR\b", re.I)
RE_VAT = re.compile(r"(?:Umsatzsteuer|MwSt)[^%]{0,200}?\(?(?:derzeit\s*)?(\d{1,2})%\)?", re.I)
RE_PAY_DAYS = re.compile(r"(\d{1,3})\s*Tage\s+nach\s+Rechnungserhalt", re.I)
RE_START = re.compile(r"tritt\s+am\s+(\d{1,2}\.\d{1,2}\.\d{2,4})\s+in\s+Kraft", re.I)
RE_END = re.compile(r"endet\s+am\s+(\d{1,2}\.\d{1,2}\.\d{2,4})", re.I)
RE_JUR = re.compile(r"Gerichtsstand[^\n]*?(?:ist|in|am|bei|:)??\s*([A-ZÄÖÜ][a-zäöüß]+)(?=[\s\.,;]|$)", re.I)
RE_LAW = re.compile(r"Es gilt das Recht der Bundesrepublik Deutschland", re.I)
RE_CONTRACT_TYPE = re.compile(r"\b(Dienstleistungsvertrag|Werkvertrag|Kaufvertrag|Mietvertrag|Lizenzvertrag|Servicevertrag)\b", re.I)
RE_TERM_WEEKS = re.compile(r"Frist\s+von\s+(\d{1,2})\s*Wochen\s+zum\s+Monatsende", re.I)

# -------- Helpers --------
_COMPANY_HINT = re.compile(r"\b(GmbH|AG|UG|KG|OHG|GbR|SE|e\.V\.)\b")
_PERSON_NAME = re.compile(r"^[A-ZÄÖÜ][a-zäöüß]+(?:\s+[A-ZÄÖÜ][a-zäöüß\-]+){1,2}$")
_STOPWORDS = {"und", "recht", "gerichtsstand", "ist", "in", "am", "bei"}

def _is_company(name: str) -> bool:
    return bool(name and _COMPANY_HINT.search(name))

def _is_person_name(name: str) -> bool:
    return bool(name and _PERSON_NAME.match(name))

def _looks_like_title(s: str) -> bool:
    bad = ["Dienstleistungsvertrag", "Vertragsgegenstand", "Gerichtsstand", "Schlussbestimmungen", "§"]
    s = s or ""
    return any(tok in s for tok in bad)

def _fmt_date(s: str | None) -> str | None:
    if not s:
        return None
    if re.match(r"^\d{4}-\d{2}-\d{2}$", s):
        return s
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{2,4})$", s)
    if m:
        d, mth, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100:
            y += 2000
        return f"{y:04d}-{mth:02d}-{d:02d}"
    return s

def _section(text: str, num: int) -> str | None:
    rx = re.compile(rf"(§\s*{num}\s+\w+.*?)(?=\n\s*§\s*\d+\s+\w+|$)", re.S|re.I)
    m = rx.search(text or "")
    return m.group(1) if m else None

def _first(dfq: pd.DataFrame, col: str):
    return None if dfq.empty else dfq.iloc[0].get(col)

# -------- Core --------
def normalize_spans(df: pd.DataFrame, full_text: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fill missing subtype/currency/unit and derive a KeyFacts dataframe.
    Returns: (df_enriched, keyfacts_df)
    """
    if df is None or df.empty:
        return df, pd.DataFrame()

    df = df.copy()

    # Required columns
    for col in ["subtype","currency","unit","value_norm","text_raw","type","span_id","doc_id","page","para","start","end","confidence","extractor","version"]:
        if col not in df.columns:
            df[col] = None

    # PARTY FILTER: drop titles masquerading as parties
    if "type" in df.columns:
        mask = df["type"].eq("party")
        drop_idx = []
        for i in df[mask].index:
            nm = str(df.at[i, "value_norm"] or df.at[i, "text_raw"] or "")
            if _looks_like_title(nm):
                drop_idx.append(i)
        if drop_idx:
            df = df.drop(index=drop_idx).reset_index(drop=True)

    # SUBJECT (clause: subject)
    mask_subject = df["type"].eq("clause") & df["text_raw"].fillna("").str.contains(r"§\s*1\s+Vertragsgegenstand", case=False, regex=True)
    df.loc[mask_subject & df["subtype"].isna(), "subtype"] = "subject"

    ## CURRENCY FILL: if money has EUR symbol in text, set currency
    if 'type' in df.columns:
        for i in df.index[df['type'].eq('money')]:
            txt = str(df.at[i, 'text_raw'] or '')
            if (df.at[i, 'currency'] is None or df.at[i, 'currency']=="") and ('EUR' in txt or '€' in txt):
                df.at[i, 'currency'] = 'EUR'

    # MONEY: mark total_fee + currency
    for i in df.index[df["type"].eq("money")]:
        txt = str(df.at[i, "text_raw"] or "")
        if pd.isna(df.at[i, "currency"]) and RE_EUR.search(txt):
            df.at[i, "currency"] = "EUR"
        if pd.isna(df.at[i, "subtype"]) and (RE_TOTAL_FEE_SENT.search(txt) or RE_VERG.search(txt)):
            df.at[i, "subtype"] = "total_fee"

    
    # Contract type
    if not ((df["type"]=="clause") & (df["subtype"]=="contract_type")).any():
        mt = RE_CONTRACT_TYPE.search(full_text or "")
        if mt:
            ctype = mt.group(1).strip()
            new_row = {
                "doc_id": df["doc_id"].iloc[0] if "doc_id" in df.columns else "",
                "type": "clause",
                "subtype": "contract_type",
                "text_raw": mt.group(0),
                "value_norm": ctype,
                "unit": None, "currency": None,
                "page": None, "para": None, "start": None, "end": None,
                "confidence": 0.9, "extractor": "Normalizer", "version": "1.0",
                "span_id": f"sp_{str(len(df)+1).zfill(6)}"
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
# VAT from §3
    sec3 = _section(full_text, 3) or (full_text or "")
    if not ((df["type"]=="other") & (df["subtype"]=="vat_rate_percent")).any():
        m = RE_VAT.search(sec3)
        if not m:
            m = RE_VAT.search(full_text or '')
        if m:
            try:
                pct = float(m.group(1))
            except Exception:
                pct = None
            new_row = {
                "doc_id": df["doc_id"].iloc[0] if "doc_id" in df.columns else "",
                "type": "other",
                "subtype": "vat_rate_percent",
                "text_raw": m.group(0),
                "value_norm": pct,
                "unit": "percent",
                "currency": None,
                "page": None, "para": None, "start": None, "end": None,
                "confidence": 0.86, "extractor": "Normalizer", "version": "1.0",
                "span_id": f"sp_{str(len(df)+1).zfill(6)}"
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # Payment terms
    if not ((df["type"]=="other") & (df["subtype"]=="payment_terms_days_after_invoice")).any():
        pm = RE_PAY_DAYS.search(full_text or "")
        if pm:
            days = int(pm.group(1))
            new_row = {
                "doc_id": df["doc_id"].iloc[0] if "doc_id" in df.columns else "",
                "type": "other",
                "subtype": "payment_terms_days_after_invoice",
                "text_raw": pm.group(0),
                "value_norm": days,
                "unit": "days",
                "currency": None,
                "page": None, "para": None, "start": None, "end": None,
                "confidence": 0.85, "extractor": "Normalizer", "version": "1.0",
                "span_id": f"sp_{str(len(df)+1).zfill(6)}"
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # Dates in §4
    sec4 = _section(full_text, 4) or (full_text or "")
    if not ((df["type"]=="date") & (df["subtype"]=="start_date")).any():
        ms = RE_START.search(sec4)
        if ms:
            iso = _fmt_date(ms.group(1))
            new_row = {
                "doc_id": df["doc_id"].iloc[0] if "doc_id" in df.columns else "",
                "type": "date",
                "subtype": "start_date",
                "text_raw": ms.group(0),
                "value_norm": iso,
                "unit": None, "currency": None,
                "page": None, "para": None, "start": None, "end": None,
                "confidence": 0.85, "extractor": "Normalizer", "version": "1.0",
                "span_id": f"sp_{str(len(df)+1).zfill(6)}"
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    if not ((df["type"]=="date") & (df["subtype"]=="end_date")).any():
        me = RE_END.search(sec4)
        if me:
            iso = _fmt_date(me.group(1))
            new_row = {
                "doc_id": df["doc_id"].iloc[0] if "doc_id" in df.columns else "",
                "type": "date",
                "subtype": "end_date",
                "text_raw": me.group(0),
                "value_norm": iso,
                "unit": None, "currency": None,
                "page": None, "para": None, "start": None, "end": None,
                "confidence": 0.85, "extractor": "Normalizer", "version": "1.0",
                "span_id": f"sp_{str(len(df)+1).zfill(6)}"
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # Jurisdiction & Law
    sec6 = _section(full_text, 6) or (full_text or "")
    if not ((df["type"]=="clause") & (df["subtype"]=="jurisdiction")).any():
        mj = RE_JUR.search(sec6)
        if mj:
            city = mj.group(1)
            if city and city.lower() not in _STOPWORDS:
                new_row = {
                    "doc_id": df["doc_id"].iloc[0] if "doc_id" in df.columns else "",
                    "type": "clause",
                    "subtype": "jurisdiction",
                    "text_raw": mj.group(0),
                    "value_norm": city,
                    "unit": None, "currency": None,
                    "page": None, "para": None, "start": None, "end": None,
                    "confidence": 0.85, "extractor": "Normalizer", "version": "1.0",
                    "span_id": f"sp_{str(len(df)+1).zfill(6)}"
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    if not ((df["type"]=="clause") & (df["subtype"]=="governing_law_germany")).any():
        if RE_LAW.search(full_text or ""):
            m = RE_LAW.search(full_text or "")
            new_row = {
                "doc_id": df["doc_id"].iloc[0] if "doc_id" in df.columns else "",
                "type": "clause",
                "subtype": "governing_law_germany",
                "text_raw": m.group(0),
                "value_norm": "DE",
                "unit": None, "currency": None,
                "page": None, "para": None, "start": None, "end": None,
                "confidence": 0.85, "extractor": "Normalizer", "version": "1.0",
                "span_id": f"sp_{str(len(df)+1).zfill(6)}"
            }
            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)

    # DEFAULTS
    df["subtype"] = df["subtype"].fillna("unspecified")

    # KeyFacts
    key = {}
    parties = df[df["type"]=="party"].copy()
    key["party_count"] = int(parties.shape[0])
    if not parties.empty:
        companies = parties[parties["value_norm"].fillna("").apply(_is_company)]
        persons   = parties[parties["value_norm"].fillna("").apply(_is_person_name)]
        selected = []
        if not companies.empty: selected.append(companies.iloc[0])
        if not persons.empty:   selected.append(persons.iloc[0])
        if not selected:
            selected = [parties.iloc[0]]
            if parties.shape[0] > 1:
                selected.append(parties.iloc[1])
        selected = [r.to_dict() if hasattr(r, "to_dict") else r for r in selected]
        if selected:
            key["party_1"] = selected[0].get("value_norm") or selected[0].get("text_raw")
        if len(selected) > 1:
            key["party_2"] = selected[1].get("value_norm") or selected[1].get("text_raw")

    ctype_df = df[(df["type"]=="clause") & (df["subtype"]=="contract_type")]
    key["contract_type"] = _first(ctype_df, "value_norm")

    subj = df[(df["type"]=="clause") & (df["subtype"]=="subject")]
    key["subject_present"] = not subj.empty
    key["subject_snippet"] = None if subj.empty else str(subj.iloc[0]["text_raw"]).splitlines()[0][:180]

    fee = df[(df["type"]=="money") & (df["subtype"]=="total_fee")]
    key["total_fee"] = _first(fee, "value_norm")
    key["currency"] = _first(fee, "currency")

    vat = df[(df["type"]=="other") & (df["subtype"]=="vat_rate_percent")]
    key["vat_rate_percent"] = _first(vat, "value_norm")

    pay = df[(df["type"]=="other") & (df["subtype"]=="payment_terms_days_after_invoice")]
    key["payment_terms_days"] = _first(pay, "value_norm")

    termn = df[(df['type']=='other') & (df['subtype']=='termination_notice_weeks_to_month_end')]
    key['termination_notice_weeks_to_month_end'] = _first(termn, 'value_norm')

    s = df[(df["type"]=="date") & (df["subtype"]=="start_date")]
    e = df[(df["type"]=="date") & (df["subtype"]=="end_date")]
    key["start_date"] = _first(s, "value_norm")
    key["end_date"] = _first(e, "value_norm")

    law = df[(df["type"]=="clause") & (df["subtype"]=="governing_law_germany")]
    jur = df[(df["type"]=="clause") & (df["subtype"]=="jurisdiction")]
    key["governing_law"] = _first(law, "value_norm")
    key["jurisdiction_city"] = _first(jur, "value_norm")

    keyfacts_df = pd.DataFrame([key])
    return df, keyfacts_df

SUM_RE_MONEY = re.compile(r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*(EUR|€)', re.I)
SUM_RE_VAT = re.compile(r'(?:Umsatzsteuer|MwSt)[^%]{0,120}?(?:derzeit\s*)?(\d{1,2})%', re.I)
SUM_RE_PAY = re.compile(r'(\d{1,3})\s*Tage\s+nach\s+Rechnungserhalt', re.I)

def summarize_de(df_spans: pd.DataFrame, df_keyfacts: pd.DataFrame | None = None) -> str:
    lines = []
    try:
        if df_keyfacts is None or df_keyfacts.empty:
            _, df_keyfacts = normalize_spans(df_spans, "")
        if df_keyfacts.empty:
            return ""

        row = df_keyfacts.iloc[0]

        # Load section texts for fallbacks
        all_text = ''
        if 'text_raw' in df_spans.columns:
            try:
                all_text = '\n'.join(df_spans['text_raw'].dropna().astype(str).tolist())
            except Exception:
                all_text = ''
        # Try to locate §3 and §4 from combined text
        sec3_txt = ''
        sec4_txt = ''
        try:
            m3 = re.search(r'(§\s*3\s+[^\n]+)(.*?)(?=\n\s*§\s*4\s+|$)', all_text, re.S|re.I)
            if m3: sec3_txt = m3.group(0)
        except Exception:
            pass
        try:
            m4 = re.search(r'(§\s*4\s+[^\n]+)(.*?)(?=\n\s*§\s*\d+\s+|$)', all_text, re.S|re.I)
            if m4: sec4_txt = m4.group(0)
        except Exception:
            pass

        parties = []
        if row.get("party_1"): parties.append(str(row.get("party_1")))
        if row.get("party_2"): parties.append(str(row.get("party_2")))
        if parties:
            lab = []
            if len(parties) >= 1: lab.append(f"A: {parties[0]}")
            if len(parties) >= 2: lab.append(f"B: {parties[1]}")
            lines.append("**Parteien:** " + " – ".join(lab))

        ctype = row.get("contract_type")
        if ctype:
            lines.append("**Vertragsart:** " + str(ctype))

        subj = row.get("subject_snippet")
        if subj:
            lines.append("**Vertragsgegenstand:** " + str(subj))

        fee = row.get("total_fee")
        ## FEE FALLBACK: pick largest amount in §3 when missing
        if (fee is None or fee=='') and sec3_txt:
            vals = [m.group(1) for m in SUM_RE_MONEY.finditer(sec3_txt)]
            def _to_f(x):
                x = x.replace('.', '').replace(',', '.')
                try: return float(x)
                except: return None
            nums = [ _to_f(v) for v in vals ]
            nums = [n for n in nums if n is not None]
            if nums:
                fee = max(nums)
        cur = row.get("currency") or ("EUR" if fee else None)
        if fee is not None:
            lines.append(f"**Vergütung:** {fee} {cur or ''}".strip())

        vat = row.get("vat_rate_percent")
        ## VAT FALLBACK: read from §3 text
        if (vat is None or vat=='') and sec3_txt:
            mv = SUM_RE_VAT.search(sec3_txt)
            if mv:
                try: vat = float(mv.group(1))
                except: pass
        if vat is not None:
            lines.append(f"**USt.:** {float(vat):.0f}%")

        pay = row.get("payment_terms_days")
        ## PAY FALLBACK: read from §3 text
        if (not pay) and sec3_txt:
            mp = SUM_RE_PAY.search(sec3_txt)
            if mp:
                try: pay = int(mp.group(1))
                except: pass
        if pay:
            lines.append(f"**Zahlungsziel:** {int(pay)} Tage nach Rechnungserhalt")

        s = _fmt_date(row.get("start_date"))
        e = _fmt_date(row.get("end_date"))
        ## DATES FALLBACK via §4
        if (not s or s=='') and sec4_txt:
            ms = re.search(r'tritt\s+am\s+(\d{1,2}\.\d{1,2}\.\d{2,4})\s+in\s+Kraft', sec4_txt, re.I)
            if ms: s = _fmt_date(ms.group(1))
        if (not e or e=='') and sec4_txt:
            me = re.search(r'endet\s+am\s+(\d{1,2}\.\d{1,2}\.\d{2,4})', sec4_txt, re.I)
            if me: e = _fmt_date(me.group(1))
        if s or e:
            lines.append(f"**Laufzeit:** {s or '—'} bis {e or '—'}")

        jur = row.get("jurisdiction_city")
        law = row.get("governing_law")
        if jur or law:
            lj = []
            if law: lj.append("Deutsches Recht")
            if jur: lj.append(f"Gerichtsstand {jur}")
            lines.append("**Recht/Gerichtsstand:** " + " – ".join(lj))

    except Exception:
        pass

    return "\n\n".join(lines) if lines else ""
