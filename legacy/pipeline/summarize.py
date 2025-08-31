from __future__ import annotations
def _get_first(df, cond, col):
    try:
        sub = df.loc[cond, col]
        return None if sub.empty else sub.iloc[0]
    except Exception:
        return None


from typing import Optional
import pandas as pd
import re
from datetime import datetime

def _parse_amount(s: str) -> Optional[float]:
    s = s or ""
    x = re.sub(r"[^0-9\.,]", "", s)
    if not x:
        return None
    if "." in x and "," in x:
        x = x.replace(".", "").replace(",", ".")
    elif "," in x and "." not in x:
        x = x.replace(",", ".")
    try:
        return float(x)
    except ValueError:
        return None

def _iso(d: str) -> Optional[str]:
    if re.match(r"^\d{4}-\d{2}-\d{2}$", d or ""):
        return d
    m = re.match(r"^(\d{1,2})/(\d{1,2})/(\d{2,4})$", d or "")
    if m:
        dd, mm, yy = m.groups()
        if len(yy)==2: yy = "20"+yy
        return f"{yy}-{int(mm):02d}-{int(dd):02d}"
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{2,4})$", d or "")
    if m:
        dd, mm, yy = m.groups()
        if len(yy)==2: yy = "20"+yy
        return f"{yy}-{int(mm):02d}-{int(dd):02d}"
    return None

def months_between(start_iso: str, end_iso: str) -> Optional[int]:
    try:
        s = datetime.strptime(start_iso, "%Y-%m-%d")
        e = datetime.strptime(end_iso, "%Y-%m-%d")
        return (e.year - s.year) * 12 + (e.month - s.month)
    except Exception:
        return None

def summarize(df: pd.DataFrame) -> pd.DataFrame:
    row = {
        "Parties": "",
        "Subject": "",
        "StartDate": "",
        "EndDate": "",
        "TermMonths": "",
        "NoticeDays": "",
        "AutoRenewMonths": "",
        "TotalAmount": "",
        "Currency": "",
        "VAT_Percent": "",
        "Cost_pM_EUR": "",
        "Cost_pA_EUR": "",
        "ExtraCosts_EUR": "",
        "IBAN": "",
        "Deadline": "",
        # New (DE-focused)
        "ReactionTime_Hours": "",
        "BusinessHours": "",
        "MinTermMonths": "",
        "NoticeMonths": "",
        "FreeMonths": "",
        "WeekendSurcharge_Percent": "",
        "Jurisdiction": "",
        "GoverningLaw": "",
        "CISG_Excluded": "",
        "PaymentStartEvent": "",
        "AutoRenewal": "",
        "ContractNumber": "",
        "CustomerNumber": "",
    }

    if df is None or df.empty:
        return pd.DataFrame([row])

    # Dates
    dates = df[df["type"]=="date"].copy()
    if not dates.empty:
        start = dates[dates["subtype"]=="start_date"]["value_norm"].dropna().tolist()
        end = dates[dates["subtype"]=="end_date"]["value_norm"].dropna().tolist()
        deadline = dates[dates["subtype"]=="deadline"]["value_norm"].dropna().tolist()
        if start: row["StartDate"] = _iso(start[0]) or start[0]
        if end: row["EndDate"] = _iso(end[0]) or end[0]
        if deadline: row["Deadline"] = _iso(deadline[0]) or deadline[0]

    # TermMonths explicit or computed
    dur_months = (df[(df["type"]=="money") & (df["subtype"]=="duration_months")]["value_norm"].tolist()
            if "value_norm" in df.columns else [])
    if dur_months:
        row["TermMonths"] = dur_months[0]
    if not row["TermMonths"] and row["StartDate"] and row["EndDate"]:
        m = months_between(row["StartDate"], row["EndDate"])
        if m is not None:
            row["TermMonths"] = str(m)

    # NoticeDays
    notice = df[(df["type"]=="money") & (df["subtype"]=="notice_days")]["value_norm"].tolist()
    if notice:
        row["NoticeDays"] = notice[0]

    # AutoRenewMonths
    ar = df[(df["type"]=="money") & (df["subtype"]=="auto_renew_months")]["value_norm"].tolist()
    if ar:
        row["AutoRenewMonths"] = ar[0]

    # Money aggregates
    monies = df[df["type"]=="money"].copy()
    if not monies.empty:
        monies["amount_num"] = monies["text_raw"].apply(_parse_amount)
        cand = monies[~monies["subtype"].isin(["percent","vat_percent","notice_days","duration_days","duration_months","auto_renew_months","iban","fixed_per_call","price_schedule_monthly","price_schedule_yearly","price_per_year"])].copy()
        if not cand.empty and cand["amount_num"].notna().any():
            mx = cand.loc[cand["amount_num"].idxmax()]
            amt = mx["amount_num"]
            row["TotalAmount"] = str(int(amt)) if isinstance(amt, float) and amt.is_integer() else (f"{amt:.2f}").rstrip('0').rstrip('.')
            # currency heuristic
            cur = mx.get("currency")
            tx = str(mx.get("text_raw","")).lower()
            if not cur or pd.isna(cur) or cur=="":
                cur = "EUR" if ("€" in tx or "eur" in tx or "euro" in tx) else ""
            row["Currency"] = cur

    # VAT
    vat = df[(df["type"]=="money") & (df["subtype"]=="vat_percent")]["text_raw"].tolist()
    if vat:
        row["VAT_Percent"] = vat[0].replace("٪","%")

    # Costs
    pm = df[(df["type"]=="money") & (df["subtype"]=="cost_per_month")]
    if not pm.empty:
        v = pm.iloc[0]
        amt = _parse_amount(v.get("text_raw",""))
        if amt is not None:
            row["Cost_pM_EUR"] = str(amt)
    pa = df[(df["type"]=="money") & (df["subtype"]=="cost_per_year")]
    if not pa.empty:
        v = pa.iloc[0]
        amt = _parse_amount(v.get("text_raw",""))
        if amt is not None:
            row["Cost_pA_EUR"] = str(amt)
    ex = df[(df["type"]=="money") & (df["subtype"]=="extra_cost")]
    if not ex.empty:
        v = ex.iloc[0]
        amt = _parse_amount(v.get("text_raw",""))
        if amt is not None:
            row["ExtraCosts_EUR"] = str(amt)

    # IDs
    cid = df[(df["type"]=="id") & (df["subtype"]=="contract_number")]["value_norm"].tolist()
    if cid: row["ContractNumber"] = cid[0]
    cust = df[(df["type"]=="id") & (df["subtype"]=="customer_number")]["value_norm"].tolist()
    if cust: row["CustomerNumber"] = cust[0]

    # Other (DE-focused)
    rt = df[(df["subtype"]=="reaction_time_hours")]["value_norm"].tolist()
    if rt: row["ReactionTime_Hours"] = rt[0]
    bh = df[(df["subtype"]=="business_hours")]["value_norm"].tolist()
    if bh: row["BusinessHours"] = bh[0]
    mt = df[(df["subtype"]=="min_term_months")]["value_norm"].tolist()
    if mt: row["MinTermMonths"] = mt[0]
    nm = df[(df["subtype"]=="notice_months")]["value_norm"].tolist()
    if nm: row["NoticeMonths"] = nm[0]
    fm = df[(df["subtype"]=="free_months")]["value_norm"].tolist()
    if fm: row["FreeMonths"] = fm[0]
    we = df[(df["subtype"]=="weekend_surcharge_percent")]["value_norm"].tolist()
    if we: row["WeekendSurcharge_Percent"] = we[0]
    juri = df[(df["subtype"]=="jurisdiction")]["value_norm"].tolist()
    if juri: row["Jurisdiction"] = juri[0]
    law = df[(df["subtype"]=="governing_law")]["value_norm"].tolist()
    if law: row["GoverningLaw"] = law[0]
    cisg = df[(df["subtype"]=="cisg_excluded")]["value_norm"].tolist()
    if cisg: row["CISG_Excluded"] = cisg[0]
    payevt = df[(df["subtype"]=="payment_start_event")]["value_norm"].tolist()
    if payevt: row["PaymentStartEvent"] = payevt[0]
    auto = df[(df["subtype"]=="auto_renewal")]["value_norm"].tolist()
    if auto: row["AutoRenewal"] = auto[0]

    # Parties
    try:
        parties = df[(df["type"]=="party")]
        if not parties.empty:
            names = []
            for _, r in parties.iterrows():
                nm = (r.get("value_norm") or r.get("text_raw") or "").strip().strip('"“”„»«')
                if nm and nm not in names:
                    names.append(nm)
            row["Parties"] = " | ".join(names)
    except Exception:
        pass

    # Subject
    try:
        subj = df[(df["type"]=="clause") & (df["subtype"]=="subject")]["value_norm"].dropna().tolist()
        if subj:
            row["Subject"] = subj[0]
    except Exception:
        pass

    return pd.DataFrame([row])

def summarize_de(df: pd.DataFrame) -> pd.DataFrame:
    base = summarize(df)
    if base is None or base.empty:
        cols = ["Parteien","Betreff","Beginn","Ende","Laufzeit_Monate","Kündigungsfrist_Tage","Automatische_Verlängerung_Monate",
                "Gesamtbetrag","Währung","MwSt_Prozent","Kosten_pro_Monat_EUR","Kosten_pro_Jahr_EUR","Zusätzliche_Kosten_EUR","IBAN","Frist",
                "Reaktionszeit_Stunden","Arbeitszeiten","Mindestlaufzeit_Monate","Kündigungsfrist_Monate","Freimonate","Wochenend-Zuschlag_%","Gerichtsstand","Rechtswahl","CISG_Ausgeschlossen","Zahlungsbeginn_Ereignis","Automatische_Verlaengerung","Vertragsnummer","Kundennummer"]
        return pd.DataFrame([{c:"" for c in cols}])
    row = base.iloc[0].to_dict()
    de = {
        "Parteien": row.get("Parties",""),
        "Betreff": row.get("Subject",""),
        "Beginn": row.get("StartDate",""),
        "Ende": row.get("EndDate",""),
        "Laufzeit_Monate": row.get("TermMonths",""),
        "Kündigungsfrist_Tage": row.get("NoticeDays",""),
        "Automatische_Verlängerung_Monate": row.get("AutoRenewMonths",""),
        "Gesamtbetrag": row.get("TotalAmount",""),
        "Währung": row.get("Currency",""),
        "MwSt_Prozent": row.get("VAT_Percent",""),
        "Kosten_pro_Monat_EUR": row.get("Cost_pM_EUR",""),
        "Kosten_pro_Jahr_EUR": row.get("Cost_pA_EUR",""),
        "Zusätzliche_Kosten_EUR": row.get("ExtraCosts_EUR",""),
        "IBAN": row.get("IBAN",""),
        "Frist": row.get("Deadline",""),
        "Reaktionszeit_Stunden": row.get("ReactionTime_Hours",""),
        "Arbeitszeiten": row.get("BusinessHours",""),
        "Mindestlaufzeit_Monate": row.get("MinTermMonths",""),
        "Kündigungsfrist_Monate": row.get("NoticeMonths",""),
        "Freimonate": row.get("FreeMonths",""),
        "Wochenend-Zuschlag_%": row.get("WeekendSurcharge_Percent",""),
        "Gerichtsstand": row.get("Jurisdiction",""),
        "Rechtswahl": row.get("GoverningLaw",""),
        "CISG_Ausgeschlossen": row.get("CISG_Excluded",""),
        "Zahlungsbeginn_Ereignis": row.get("PaymentStartEvent",""),
        "Automatische_Verlaengerung": row.get("AutoRenewal",""),
        "Vertragsnummer": row.get("ContractNumber",""),
        "Kundennummer": row.get("CustomerNumber",""),
    }
    return pd.DataFrame([de])

def _first_val(df, expr):
    try:
        s = df.query(expr)
        if not s.empty:
            return s.iloc[0]
    except Exception:
        pass
    return None

def summarize_keyfacts(text: str, sections: dict, spans_df):
    # sections: {"1": "...", "2":"...", "3":"...", "4":"..."}
    kf = {}
    # Parties (best-effort): look for type=='party'
    p = spans_df[spans_df["type"]=="party"] if "type" in spans_df.columns else None
    if p is not None and not p.empty:
        kf["party_1"] = p[p["subtype"]=="A"]["text_raw"].iloc[0] if "subtype" in p.columns and (p["subtype"]=="A").any() else p.iloc[0]["text_raw"]
        if len(p) > 1:
            kf["party_2"] = p.iloc[1]["text_raw"]
    else:
        kf["party_1"] = None
        kf["party_2"] = None
    # Contract type
    ct = _first_val(spans_df, 'type=="clause" and subtype=="contract_type"') if hasattr(spans_df,"query") else None
    kf["contract_type"] = (ct["value_norm"] if isinstance(ct, pd.Series) and "value_norm" in ct else None)
    # Subject snippet from §1
    s1 = sections.get("1") or ""
    kf["subject_snippet"] = (s1[:200] + "...") if s1 else None
    # Fee / currency from money:total_fee within §3
    fee = _first_val(spans_df, 'type=="money" and subtype=="total_fee"') if hasattr(spans_df,"query") else None
    kf["total_fee"] = (float(fee["value_norm"]) if isinstance(fee, pd.Series) and "value_norm" in fee else None)
    kf["currency"] = (fee["currency"] if isinstance(fee, pd.Series) and "currency" in fee else None)
    # VAT percent
    vat = _first_val(spans_df, 'subtype=="vat_rate_percent"') if hasattr(spans_df,"query") else None
    kf["vat_rate_percent"] = (int(vat["value_norm"]) if isinstance(vat, pd.Series) and "value_norm" in vat else None)
    # Payment terms
    pay = _first_val(spans_df, 'subtype=="payment_terms_days_after_invoice"') if hasattr(spans_df,"query") else None
    kf["payment_terms_days"] = (int(pay["value_norm"]) if isinstance(pay, pd.Series) and "value_norm" in pay else None)
    # Dates
    sd = _first_val(spans_df, 'type=="date" and subtype=="start_date"') if hasattr(spans_df,"query") else None
    ed = _first_val(spans_df, 'type=="date" and subtype=="end_date"') if hasattr(spans_df,"query") else None
    kf["start_date"] = (sd["value_norm"] if isinstance(sd, pd.Series) and "value_norm" in sd else None)
    kf["end_date"] = (ed["value_norm"] if isinstance(ed, pd.Series) and "value_norm" in ed else None)
    # Termination
    tn = _first_val(spans_df, 'subtype=="termination_notice_weeks_to_month_end"') if hasattr(spans_df,"query") else None
    kf["termination_notice_weeks_to_month_end"] = (int(tn["value_norm"]) if isinstance(tn, pd.Series) and "value_norm" in tn else None)
    # Law/Jurisdiction (best-effort)
    law = _first_val(spans_df, 'subtype=="governing_law"') if hasattr(spans_df,"query") else None
    jur = _first_val(spans_df, 'subtype=="jurisdiction_city"') if hasattr(spans_df,"query") else None
    kf["governing_law"] = (law["value_norm"] if isinstance(law, pd.Series) and "value_norm" in law else None)
    kf["jurisdiction_city"] = (jur["value_norm"] if isinstance(jur, pd.Series) and "value_norm" in jur else None)
    return kf
