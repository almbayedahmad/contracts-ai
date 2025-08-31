
import pandas as pd
from typing import Dict, Any

def _to_float_de(s: str):
    import re as _re
    s = _re.sub(r'[^0-9\.,]', '', str(s) or '')
    if '.' in s and ',' in s: s = s.replace('.', '').replace(',', '.')
    elif ',' in s and '.' not in s: s = s.replace(',', '.')
    try: return float(s)
    except: return None

def _parse_date_any(s: str):
    import re as _re
    from datetime import datetime
    s = str(s or "").strip()
    try:
        if _re.match(r'^\d{4}-\d{2}-\d{2}$', s):
            return datetime.strptime(s, "%Y-%m-%d")
    except: pass
    m = _re.match(r'^(\d{1,2})\.(\d{1,2})\.(\d{2,4})$', s)
    if m:
        dd, mm, yy = m.groups()
        if len(yy)==2: yy = "20"+yy
        try:
            return datetime(int(yy), int(mm), int(dd))
        except: pass
    return None

def _span_ids(df: pd.DataFrame):
    if df is None or len(df)==0: return []
    col = "span_id" if "span_id" in df.columns else None
    if col:
        return [str(x) for x in df[col].head(5).tolist()]
    return [str(i) for i in df.index.astype(str).tolist()[:5]]

def _exists(df: pd.DataFrame, t: str = None, st: str = None) -> bool:
    if df is None or df.empty: return False
    ok = df
    if t is not None: ok = ok[ok["type"] == t]
    if st is not None: ok = ok[ok["subtype"] == st]
    return not ok.empty

def _nums_from(spans: pd.DataFrame, subtype: str):
    if spans is None or spans.empty: return []
    df = spans[spans["subtype"]==subtype]
    if df is None or df.empty: return []
    vals = df["value_norm"].dropna().astype(str).tolist()
    nums = [_to_float_de(v) for v in vals]
    return [x for x in nums if x is not None]

def _any_present(spans: pd.DataFrame, options):
    if spans is None or spans.empty: return False
    for opt in options or []:
        df = spans
        if "type" in opt: df = df[df["type"]==opt["type"]]
        if "subtype" in opt: df = df[df["subtype"]==opt["subtype"]]
        if df is not None and not df.empty: return True
    return False

def _all_present(spans: pd.DataFrame, reqs):
    if spans is None or spans.empty: return False
    for opt in reqs or []:
        df = spans
        if "type" in opt: df = df[df["type"]==opt["type"]]
        if "subtype" in opt: df = df[df["subtype"]==opt["subtype"]]
        if df is None or df.empty: return False
    return True

# Helpers for price coverage
def _covered_months(price: pd.DataFrame):
    months = set()
    if price is None or price.empty:
        return months
    df = price.copy()
    if "unit" in df.columns:
        pm = df[df["unit"]=="month"]
        py = df[df["unit"]=="year"]
    else:
        pm = pd.DataFrame(); py = pd.DataFrame()
    if not pm.empty:
        for _, r in pm.iterrows():
            try:
                s = int(float(r.get("start_month") or 0)); e = int(float(r.get("end_month") or 0))
                if s and e and e>=s:
                    for m in range(s, e+1): months.add(m)
            except Exception: pass
    if not py.empty:
        for _, r in py.iterrows():
            try:
                y = int(float(r.get("year_index") or 0))
                if y>0:
                    s = (y-1)*12 + 1; e = y*12
                    for m in range(s, e+1): months.add(m)
            except Exception: pass
    return months

def _term_months(spans: pd.DataFrame):
    if spans is None or spans.empty: return None
    for st in ["min_term_months", "term_months", "Laufzeit_Monate"]:
        df = spans[spans["subtype"]==st]
        if df is not None and not df.empty:
            try:
                val = df["value_norm"].astype(str).iloc[0]
                val = val.replace(',', '.')
                return int(float(val))
            except Exception: pass
    return None

def price_covers_term(spans: pd.DataFrame, price: pd.DataFrame, tolerance: int = 0):
    tm = _term_months(spans)
    if not tm or tm<=0:
        return True, "", []  # not applicable
    covered = _covered_months(price)
    missing = [m for m in range(1, tm+1) if m not in covered]
    if len(missing) <= tolerance:
        return True, "", ["PriceSchedule"]
    msg = f"Fehlende Monate im Preisplan: {missing[:20]}{'...' if len(missing)>20 else ''}"
    return False, msg, ["PriceSchedule"]

def evaluate_net_vat_brutto(spans: pd.DataFrame, tol_eur: float = 1.0):
    net = _nums_from(spans, "net_amount_eur")
    vat_amt = _nums_from(spans, "vat_amount_eur")
    gross = _nums_from(spans, "gross_amount_eur")
    vat_pct = _nums_from(spans, "vat_percent")

    if net and gross:
        # Try with VAT amount
        if vat_amt:
            for n in net:
                for v in vat_amt:
                    for g in gross:
                        if n is None or v is None or g is None: continue
                        if abs((n+v) - g) <= tol_eur:
                            return True
        # Try with VAT percent
        if vat_pct:
            for n in net:
                for p in vat_pct:
                    for g in gross:
                        if n is None or p is None or g is None: continue
                        exp = n*(1.0 + p/100.0)
                        if abs(exp - g) <= tol_eur:
                            return True
        return False
    return True  # not applicable

def evaluate_compliance(frames_or_spans, policies: Dict[str, Any]) -> pd.DataFrame:
    # Backward compatibility: allow df_spans directly
    if isinstance(frames_or_spans, pd.DataFrame):
        spans = frames_or_spans
        entities = None
        price = None
    else:
        frames = frames_or_spans or {}
        spans = frames.get("spans")
        entities = frames.get("entities")
        price = frames.get("price")

    out = []
    for rule in policies.get("rules", []):
        rid = rule.get("id")
        rtype = rule.get("type")
        sev = rule.get("severity","low")
        msg = rule.get("description","")
        passed = False
        ev_ids = []

        try:
            if rtype == "presence":
                t = rule.get("target"); st = rule.get("subtype")
                df = spans
                if df is not None and not df.empty:
                    if t is not None: df = df[df["type"]==t]
                    if st is not None: df = df[df["subtype"]==st]
                passed = (df is not None and not df.empty)
                if passed: ev_ids = _span_ids(df)

            elif rtype == "min_value":
                where = rule.get("where", {})
                field = rule.get("field","value_norm")
                thr = float(rule.get("threshold", 0))
                df = spans
                if df is not None and not df.empty:
                    if "type" in where: df = df[df["type"] == where["type"]]
                    if "subtype" in where: df = df[df["subtype"] == where["subtype"]]
                if df is None or df.empty:
                    passed = False
                else:
                    vals = df[field].dropna().astype(str).tolist()
                    nums = [ _to_float_de(v) for v in vals ]
                    nums = [x for x in nums if x is not None]
                    if nums:
                        mx = max(nums)
                        passed = (mx >= thr)
                        ev = df[df[field].astype(str)==str(mx).replace('.', ',')]
                        if ev is None or ev.empty: ev = df.head(1)
                        ev_ids = _span_ids(ev)

            elif rtype == "reaction_time_max_hours":
                thr = float(rule.get("threshold", 48))
                df = spans
                if df is not None and not df.empty:
                    df = df[(df["subtype"]=="reaction_time_hours")]
                vals = df["value_norm"].dropna().astype(str).tolist() if df is not None and not df.empty else []
                nums = [ _to_float_de(v) for v in vals ]
                nums = [x for x in nums if x is not None]
                passed = (nums and min(nums) <= thr)
                if nums and df is not None and not df.empty:
                    mi = min(nums)
                    ev = df[df["value_norm"].astype(str).str.contains(str(int(mi)) if isinstance(mi,float) and mi.is_integer() else str(mi), na=False, regex=False)]
                    if ev is None or ev.empty: ev = df.head(1)
                    ev_ids = _span_ids(ev)

            elif rtype == "start_before_end":
                s = spans[spans["subtype"]=="start_date"] if spans is not None and not spans.empty else None
                e = spans[spans["subtype"]=="end_date"] if spans is not None and not spans.empty else None
                if s is not None and not s.empty and e is not None and not e.empty:
                    ds = _parse_date_any(s["value_norm"].dropna().astype(str).iloc[0])
                    de = _parse_date_any(e["value_norm"].dropna().astype(str).iloc[0])
                    if ds and de:
                        passed = (ds <= de)
                    ev_ids = _span_ids(s.head(1)) + _span_ids(e.head(1))
                else:
                    passed = True  # not applicable

            elif rtype == "govlaw_requires_jurisdiction":
                gl = spans[spans["subtype"]=="governing_law"] if spans is not None and not spans.empty else None
                if gl is not None and not gl.empty:
                    j = spans[(spans["type"]=="clause") & (spans["subtype"]=="jurisdiction")]
                    passed = (j is not None and not j.empty)
                    ev_ids = _span_ids(gl.head(1)) + (_span_ids(j.head(1)) if j is not None else [])
                else:
                    passed = True

            elif rtype == "cisg_excluded_if_de_govlaw":
                gl = spans[spans["subtype"]=="governing_law"] if spans is not None and not spans.empty else None
                if gl is not None and not gl.empty:
                    txt = " ".join(gl["text_raw"].dropna().astype(str).tolist()).lower()
                    is_de = any(w in txt for w in ["deutsch", "bundesrepublik", "deutsches recht", "german law"])
                    if is_de:
                        cisg = spans[(spans["type"]=="clause") & (spans["subtype"]=="cisg_excluded")]
                        passed = (cisg is not None and not cisg.empty)
                        ev_ids = _span_ids(gl.head(1)) + (_span_ids(cisg.head(1)) if cisg is not None else [])
                    else:
                        passed = True
                else:
                    passed = True

            elif rtype == "vat_present_if_eur":
                has_eur = False; df = spans
                if df is not None and not df.empty:
                    mny = df[df["type"]=="money"]
                    if mny is not None and not mny.empty:
                        txt = " ".join(mny["text_raw"].dropna().astype(str).tolist()).lower()
                        has_eur = ("€" in txt) or ("eur" in txt) or ("euro" in txt)
                        if has_eur: ev_ids = _span_ids(mny.head(2))
                if has_eur:
                    vat = spans[(spans["type"]=="money") & (spans["subtype"]=="vat_percent")] if spans is not None else None
                    passed = (vat is not None and not vat.empty)
                    if vat is not None and not vat.empty:
                        ev_ids += _span_ids(vat.head(1))
                else:
                    passed = True

            elif rtype == "price_schedule_exists_if_costs":
                has_cost = _exists(spans, "money", "cost_per_month") or _exists(spans, "money", "cost_per_year")
                if has_cost:
                    passed = (price is not None and not price.empty)
                    if passed: ev_ids = ["PriceSchedule"]
                else:
                    passed = True

            elif rtype == "year1_free_impl_freimonate":
                if price is not None and not price.empty and "unit" in price.columns:
                    py = price[price["unit"]=="year"].copy()
                    if not py.empty:
                        import numpy as _np
                        py["y"] = pd.to_numeric(py.get("year_index"), errors="coerce").fillna(_np.nan)
                        py = py.dropna(subset=["y"])
                        py["y"] = py["y"].astype(int)
                        py["amt"] = py.get("amount_eur").apply(_to_float_de)
                        y1 = py[py["y"]==1]
                        if not y1.empty and y1["amt"].fillna(0).min() == 0:
                            passed = True; ev_ids = ["PriceSchedule:Y1=0"]
                        else:
                            passed = False
                    else:
                        passed = True
                else:
                    passed = True

            elif rtype == "entities_roles_both_present":
                if entities is None or entities.empty or "role" not in entities.columns:
                    passed = False
                else:
                    roles = entities["role"].str.lower().fillna("")
                    passed = ("customer" in roles.values) and ("provider" in roles.values)
                    if passed: ev_ids = ["entities:roles"]

            elif rtype == "presence_any":
                options = rule.get("options", [])
                ev_ids = []; ok = False
                for opt in options:
                    df = spans
                    if df is not None and not df.empty:
                        if "type" in opt: df = df[df["type"]==opt["type"]]
                        if "subtype" in opt: df = df[df["subtype"]==opt["subtype"]]
                    if df is not None and not df.empty:
                        ok = True; ev_ids += _span_ids(df.head(1))
                passed = ok

            elif rtype == "presence_implies":
                cond = rule.get("if", []); need = rule.get("then", [])
                cond_hit = False; cids = []
                for opt in cond:
                    df = spans
                    if df is not None and not df.empty:
                        if "type" in opt: df = df[df["type"]==opt["type"]]
                        if "subtype" in opt: df = df[df["subtype"]==opt["subtype"]]
                    if df is not None and not df.empty:
                        cond_hit = True; cids += _span_ids(df.head(1))
                if cond_hit:
                    all_ok = True; nids = []
                    for opt in need:
                        df2 = spans
                        if df2 is not None and not df2.empty:
                            if "type" in opt: df2 = df2[df2["type"]==opt["type"]]
                            if "subtype" in opt: df2 = df2[df2["subtype"]==opt["subtype"]]
                        if df2 is None or df2.empty:
                            all_ok = False
                        else:
                            nids += _span_ids(df2.head(1))
                    passed = all_ok; ev_ids = cids + nids
                else:
                    passed = True

            elif rtype == "presence_implies_any":
                cond = rule.get("if", []); opts = rule.get("any", [])
                cond_hit = False; cids = []
                for opt in cond:
                    df = spans
                    if df is not None and not df.empty:
                        if "type" in opt: df = df[df["type"]==opt["type"]]
                        if "subtype" in opt: df = df[df["subtype"]==opt["subtype"]]
                    if df is not None and not df.empty:
                        cond_hit = True; cids += _span_ids(df.head(1))
                if cond_hit:
                    any_ok = False; nids = []
                    for opt in opts:
                        df2 = spans
                        if df2 is not None and not df2.empty:
                            if "type" in opt: df2 = df2[df2["type"]==opt["type"]]
                            if "subtype" in opt: df2 = df2[df2["subtype"]==opt["subtype"]]
                        if df2 is not None and not df2.empty:
                            any_ok = True; nids += _span_ids(df2.head(1))
                    passed = any_ok; ev_ids = cids + nids
                else:
                    passed = True

            elif rtype == "monthly_yearly_consistency":
                tol = float(rule.get("tolerance_pct", 5.0)) / 100.0
                m = spans[spans["subtype"]=="cost_per_month"] if spans is not None and not spans.empty else None
                y = spans[spans["subtype"]=="cost_per_year"] if spans is not None and not spans.empty else None
                if m is not None and not m.empty and y is not None and not y.empty:
                    mv = [ _to_float_de(v) for v in m["value_norm"].astype(str).tolist() ]
                    yv = [ _to_float_de(v) for v in y["value_norm"].astype(str).tolist() ]
                    ok = False
                    for i, mm in enumerate(mv):
                        for j, yy in enumerate(yv):
                            if mm and yy:
                                exp = mm*12.0
                                diff = abs(yy-exp)/exp if exp else 1.0
                                if diff <= tol:
                                    ok = True; ev_ids = _span_ids(m.iloc[i:i+1]) + _span_ids(y.iloc[j:j+1]); break
                        if ok: break
                    passed = ok
                else:
                    passed = True

            elif rtype == "payment_annual_requires_advance":
                df_int = spans[spans["subtype"]=="payment_interval"] if spans is not None and not spans.empty else None
                has_y = df_int is not None and not df_int.empty and any("jähr" in str(x).lower() for x in df_int["value_norm"].astype(str).tolist())
                has_cost_y = _exists(spans, "money", "cost_per_year")
                if has_y and has_cost_y:
                    adv = spans[(spans["subtype"]=="payment_advance")]
                    passed = (adv is not None and not adv.empty)
                    ev_ids = (_span_ids(df_int.head(1)) if df_int is not None else []) + (_span_ids(adv.head(1)) if adv is not None else [])
                else:
                    passed = True

            elif rtype == "price_covers_term":
                ok, msg2, ev = price_covers_term(spans, price, tolerance=int(rule.get("tolerance", 0)))
                passed = ok
                if msg2: msg = msg + " | " + msg2 if msg else msg2
                ev_ids = ev

            elif rtype == "net_vat_brutto_consistency":
                tol = float(rule.get("tolerance_eur", 1.0))
                passed = evaluate_net_vat_brutto(spans, tol_eur=tol)

            else:
                passed = False

        except Exception:
            passed = False

        out.append({
            "rule_id": rid,
            "passed": bool(passed),
            "severity": sev,
            "message": msg,
            "evidence_span_ids": ", ".join(ev_ids) if ev_ids else ""
        })

    return pd.DataFrame(out)
