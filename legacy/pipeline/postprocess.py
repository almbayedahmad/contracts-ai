
import pandas as pd
import re

def _canon(s: str) -> str:
    s = (s or "").strip().strip('"“”„»«')
    s = re.sub(r'\s+', ' ', s)
    return s

def build_entities_links(df_spans, doc_id, full_text):
    # Entities from party spans
    parties = df_spans[df_spans["type"]=="party"].copy() if df_spans is not None and not df_spans.empty else pd.DataFrame()
    entities_rows = []
    links_rows = []

    if parties is None or parties.empty:
        return (pd.DataFrame(columns=["entity_id","entity_type","canonical_name","aliases","normalized_ids"]),
                pd.DataFrame(columns=["subject_id","predicate","object_id","evidence_span_id"]))

    # Deduplicate by canonical name (case-insensitive)
    seen = {}
    ent_index = 1
    for idx, row in parties.iterrows():
        name = _canon(row.get("value_norm") or row.get("text_raw") or "")
        if not name:
            continue
        key = name.lower()
        if key not in seen:
            ent_id = f"ent_{ent_index:03d}"
            seen[key] = {"entity_id": ent_id,
                         "entity_type": row.get("subtype") or "org",
                         "canonical_name": name,
                         "aliases": set([row.get("text_raw") or name]),
                         "normalized_ids": ""}
            ent_index += 1
        else:
            seen[key]["aliases"].add(row.get("text_raw") or name)

    # Build Entities DataFrame
    for k,v in seen.items():
        v["aliases"] = "; ".join(sorted(v["aliases"]))
        entities_rows.append(v)

    df_entities = pd.DataFrame(entities_rows, columns=["entity_id","entity_type","canonical_name","aliases","normalized_ids"])

    # Build Links: contract signed_by each party (evidence span_id if present)
    doc_node = f"doc:{doc_id}"
    for idx, row in parties.iterrows():
        ev = row.get("span_id") if "span_id" in parties.columns else ""
        name = _canon(row.get("value_norm") or row.get("text_raw") or "")
        key = name.lower()
        ent_id = seen.get(key, {}).get("entity_id", "")
        if ent_id:
            links_rows.append({
                "subject_id": doc_node,
                "predicate": "signed_by",
                "object_id": ent_id,
                "evidence_span_id": ev
            })

    df_links = pd.DataFrame(links_rows, columns=["subject_id","predicate","object_id","evidence_span_id"])
    return df_entities, df_links


ROLE_HINTS = [
    ("customer", ["kunde","krankenhaus","servicenehmer","auftraggeber"]),
    ("provider", ["abbott","abiomed","siemens","service-provider","dienstleister","auftragnehmer"]),
]

def detect_roles(df_parties: pd.DataFrame, full_text: str) -> dict:
    roles = {}
    if df_parties is None or df_parties.empty:
        return roles
    for _, r in df_parties.iterrows():
        name = _canon(r.get("value_norm") or r.get("text_raw") or "")
        if not name:
            continue
        key = name.lower()
        ctx = full_text.lower()
        # heuristic based on name presence + nearby role keywords
        # simple: if "nachfolgend 'Kunde' genannt" exists near name, or keyword co-occurs in doc
        if key in ctx:
            # check generic keywords
            for role, kws in ROLE_HINTS:
                for kw in kws:
                    if kw in ctx:
                        roles[key] = role
                        break
                if key in roles:
                    break
    return roles

def build_price_schedule(df_spans: pd.DataFrame) -> pd.DataFrame:
    if df_spans is None or df_spans.empty:
        return pd.DataFrame(columns=["type","subtype","amount_eur","unit","start_month","end_month","year_index","raw"])

    out = []
    # monthly ranges
    pm = df_spans[(df_spans["type"]=="money") & (df_spans["subtype"]=="price_schedule_monthly")]
    for _, r in pm.iterrows():
        raw = r["text_raw"]
        m = re.search(r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)', raw)
        amt = m.group(1) if m else ""
        rng = re.search(r'vom\s+(\d+)\.\s*-\s*(\d+)\.\s*Monat', raw)
        a, b = (rng.group(1), rng.group(2)) if rng else ("","")
        out.append({"type":"monthly","subtype":"price_schedule_monthly","amount_eur":amt,"unit":"month","start_month":a,"end_month":b,"year_index":"","raw":raw})

    # yearly stages
    py = df_spans[(df_spans["type"]=="money") & (df_spans["subtype"]=="price_schedule_yearly")]
    for _, r in py.iterrows():
        raw = r["text_raw"]
        m = re.search(r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)', raw)
        amt = m.group(1) if m else ""
        yr = re.search(r'im\s*(\d)\.\s*Jahr', raw, re.IGNORECASE)
        y = yr.group(1) if yr else ""
        out.append({"type":"yearly","subtype":"price_schedule_yearly","amount_eur":amt,"unit":"year","start_month":"","end_month":"","year_index":y,"raw":raw})

    # flat per year
    fy = df_spans[(df_spans["type"]=="money") & (df_spans["subtype"]=="price_per_year")]
    for _, r in fy.iterrows():
        raw = r["text_raw"]
        m = re.search(r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)', raw)
        amt = m.group(1) if m else ""
        out.append({"type":"flat","subtype":"price_per_year","amount_eur":amt,"unit":"year","start_month":"","end_month":"","year_index":"","raw":raw})

    return pd.DataFrame(out, columns=["type","subtype","amount_eur","unit","start_month","end_month","year_index","raw"])


def _find_amt_eur(s: str):
    m = re.search(r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*(?:€|EUR)', s, re.IGNORECASE)
    return m.group(1) if m else ""


def build_price_schedule_from_tables(tables) -> pd.DataFrame:
    cols = ["type","subtype","amount_eur","unit","start_month","end_month","year_index","raw"]
    out = []
    if not tables:
        return pd.DataFrame(columns=cols)

    def norm(s):
        s = (s or "").strip().lower()
        s = re.sub(r"\s+", " ", s)
        return s

    # Header synonyms
    H_VON   = {"von", "start", "beginn", "monat von", "von monat", "beginn monat", "ab monat", "ab dem monat", "ab"}
    H_BIS   = {"bis", "ende", "monat bis", "bis monat", "ende monat"}
    H_MONAT = {"monat", "monate", "monat(e)", "duration", "zeitr", "zeitraum"}
    H_JAHR  = {"jahr", "jahr(e)", "jahrgang", "year"}
    H_PREIS = {"preis", "betrag", "summe", "kosten", "preis/monat", "monatsrate", "rate", "eur", "€"}
    H_NOTE  = {"bemerkung", "anmerkung", "hinweis", "beschreibung"}

    rx_amt  = re.compile(r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*(?:€|eur)', re.IGNORECASE)
    rx_rng1 = re.compile(r'(\d{1,3})\s*[.\-–—]\s*(\d{1,3})\s*\.?\s*monat', re.IGNORECASE)
    rx_rng2 = re.compile(r'(\d{1,3})\s*bis\s*(\d{1,3})\s*monat(?:e)?', re.IGNORECASE)
    rx_from = re.compile(r'ab\s*dem\s*(\d{1,3})\.?\s*monat', re.IGNORECASE)
    rx_year = re.compile(r'(?:im|im\s*gesamten)?\s*(\d)\.?\s*jahr', re.IGNORECASE)

    def header_map(row):
        m = {}
        for i, cell in enumerate(row):
            c = norm(cell)
            if not c: continue
            k = None
            if any(w in c for w in H_PREIS): k = "preis"
            elif any(w in c for w in H_VON): k = "von"
            elif any(w in c for w in H_BIS): k = "bis"
            elif any(w in c for w in H_JAHR): k = "jahr"
            elif any(w in c for w in H_MONAT): k = "monat"
            elif any(w in c for w in H_NOTE): k = "note"
            if k and k not in m:
                m[k] = i
        return m

    for t in tables:
        if not t or not any(any((c or "").strip() for c in r) for r in t):
            continue

        # Try to detect header on first non-empty row
        hdr_idx = None; hdr_map = {}
        for idx, r in enumerate(t):
            if any((c or "").strip() for c in r):
                tmp = header_map(r)
                if tmp:
                    hdr_idx = idx; hdr_map = tmp; break

        # Iterate data rows
        for ridx, r in enumerate(t):
            if hdr_idx is not None and ridx <= hdr_idx:
                continue
            line = " | ".join([c for c in r if c is not None]).strip()
            if not line: continue

            def get(colkey):
                i = hdr_map.get(colkey, None)
                return (r[i] if i is not None and i < len(r) else "").strip()

            # Header-driven parse
            if hdr_map:
                val_amt = get("preis")
                if not rx_amt.search(val_amt):
                    # maybe amount is elsewhere in row
                    for c in r:
                        if rx_amt.search(c or ""):
                            val_amt = c; break
                amt = rx_amt.search(val_amt)
                amt_s = amt.group(1) if amt else ""

                # months
                von, bis, monat = get("von"), get("bis"), get("monat")
                yr = get("jahr")

                a=b=""
                if von and bis:
                    a = re.sub(r"\D", "", von)
                    b = re.sub(r"\D", "", bis)
                elif monat:
                    # try ranges in monat cell
                    m1 = rx_rng1.search(monat) or rx_rng2.search(monat)
                    if m1:
                        a, b = m1.group(1), m1.group(2)
                    else:
                        m2 = rx_from.search(monat)
                        if m2:
                            a = m2.group(1)

                # Decide row type
                if amt_s and (a or b):
                    out.append({"type":"monthly","subtype":"price_schedule_monthly","amount_eur":amt_s,"unit":"month","start_month":a,"end_month":b,"year_index":"","raw":line})
                    continue
                if amt_s and yr:
                    y = re.sub(r"\D", "", yr) or ""
                    out.append({"type":"yearly","subtype":"price_schedule_yearly","amount_eur":amt_s,"unit":"year","start_month":"","end_month":"","year_index":y,"raw":line})
                    continue
                # fallback: monat string with amount
                if amt_s and ("monat" in norm(monat) or "monat" in line.lower() or (von or bis)):
                    out.append({"type":"monthly","subtype":"price_schedule_monthly","amount_eur":amt_s,"unit":"month","start_month":a,"end_month":b,"year_index":"","raw":line})
                    continue
                # yearly fallback
                if amt_s and ("jahr" in (yr or "").lower() or "jahr" in line.lower()):
                    y = re.sub(r"\D", "", yr or "") or ""
                    out.append({"type":"yearly","subtype":"price_schedule_yearly","amount_eur":amt_s,"unit":"year","start_month":"","end_month":"","year_index":y,"raw":line})
                    continue

            # No header map → pattern-based, as before
            m1 = rx_rng1.search(line) or rx_rng2.search(line)
            if m1:
                a, b = m1.group(1), m1.group(2)
                amt = rx_amt.search(line)
                out.append({"type":"monthly","subtype":"price_schedule_monthly","amount_eur":(amt.group(1) if amt else ""), "unit":"month","start_month":a,"end_month":b,"year_index":"","raw":line})
                continue
            m2 = rx_from.search(line)
            if m2:
                a = m2.group(1)
                amt = rx_amt.search(line)
                out.append({"type":"monthly","subtype":"price_schedule_monthly_from","amount_eur":(amt.group(1) if amt else ""),"unit":"month","start_month":a,"end_month":"","year_index":"","raw":line})
                continue
            my = rx_year.search(line)
            if my:
                y = my.group(1)
                amt = rx_amt.search(line)
                if amt:
                    out.append({"type":"yearly","subtype":"price_schedule_yearly","amount_eur":amt.group(1),"unit":"year","start_month":"","end_month":"","year_index":y,"raw":line})
                continue
            if "monat" in line.lower():
                amt = rx_amt.search(line)
                if amt:
                    out.append({"type":"monthly","subtype":"price_schedule_monthly","amount_eur":amt.group(1),"unit":"month","start_month":"","end_month":"","year_index":"","raw":line})

    df = pd.DataFrame(out, columns=cols)
    # drop empty rows
    df = df[df["amount_eur"].astype(str).str.strip() != ""]
    return df
