
import importlib, pkgutil, pandas as pd, yaml
from pathlib import Path
from core.registry import REGISTRY
from io_ops.readers import read_docx_text, read_pdf_text, read_txt, read_docx_text_and_tables
from io_ops.writers import batches_to_excel
from rules.engine import evaluate_compliance
import extractors

# auto-import extractors
for _, modname, _ in pkgutil.iter_modules(extractors.__path__):
    if modname not in ("__init__", "base"):
        importlib.import_module(f"extractors.{modname}")

def run_once(input_path: str, output_excel: str):
    p = Path(input_path)
    doc_id = p.stem
    # read
    sfx = p.suffix.lower()
    if sfx == ".docx":
        text, tables = read_docx_text_and_tables(str(p))
    elif sfx == ".pdf":
        text = read_pdf_text(str(p))
    elif sfx == ".txt":
        text = read_txt(str(p))
    else:
        raise ValueError(f"Unsupported type: {sfx}")

    # extract
    batches = []
    enabled = set(yaml.safe_load(open('pipeline/config.yml','r',encoding='utf-8')).get('use_extractors', []))
    for ext_cls in REGISTRY["extractors"]:
        if ext_cls.__extractor_name__ in enabled:
            ext = ext_cls()
            batches.append(ext.extract(doc_id, text))

    # export spans
    df_spans = batches_to_excel(batches, output_excel)

    # compliance
    policies = yaml.safe_load(open("rules/policies.yml","r",encoding="utf-8"))
    comp = evaluate_compliance(df_spans, policies)
    with pd.ExcelWriter(output_excel, engine="openpyxl", mode="a", if_sheet_exists="replace") as xw:
        # Extra sheets: Indexation & ServiceCredits
        try:
            idx_df = df_spans[df_spans['subtype'].isin(['indexation_present','index_raise_percent_pa','index_cap_percent'])].copy()
            if idx_df is not None and not idx_df.empty:
                idx_df.to_excel(xw, index=False, sheet_name='Indexation')
        except Exception: pass
        try:
            sc_df = df_spans[df_spans['subtype'].isin(['service_credit_present','service_credit_trigger_uptime_lt','service_credit_percent'])].copy()
            if sc_df is not None and not sc_df.empty:
                sc_df.to_excel(xw, index=False, sheet_name='ServiceCredits')
        except Exception: pass
        # Compliance sheet
        if comp is not None:
            comp.to_excel(xw, index=False, sheet_name="Compliance")
        # Summaries (s_en/s_de written if computed above)
        try: s_en.to_excel(xw, index=False, sheet_name="ContractSummary")
        except Exception: pass
        try: s_de.to_excel(xw, index=False, sheet_name="ContractSummary_DE")
        except Exception: pass

    return output_excel


def _enrich_summary_with_lexicon(sum_de: pd.DataFrame, df_spans: pd.DataFrame) -> pd.DataFrame:
    if sum_de is None or sum_de.empty or df_spans is None or df_spans.empty:
        return sum_de
    row = sum_de.iloc[0].to_dict()

    def has_concept(key):
        try:
            d = df_spans[(df_spans["type"]=="concept") & (df_spans["subtype"]==key)]
            return not d.empty
        except Exception:
            return False

    def first_val(subtype):
        try:
            d = df_spans[df_spans["subtype"]==subtype]
            if not d.empty:
                v = str(d.iloc[0]["value_norm"]).strip()
                return v
        except Exception:
            pass
        return ""

    # Flags
    row["GWL_vorhanden"] = "Ja" if has_concept("gwl") else "Nein"
    row["Rufbereitschaft"] = "Ja" if has_concept("rufbereitschaft") else "Nein"

    # Uptime %
    up = first_val("uptime_percent")
    if up and not str(row.get("Verfuegbarkeit_Prozent","")).strip():
        row["Verfuegbarkeit_Prozent"] = up

    # Periodicities
    for k, col in [("wartung_period","Wartung_Periodizitaet"),
                   ("inspektion_period","Inspektion_Periodizitaet"),
                   ("kalibrierung_period","Kalibrierung_Periodizitaet")]:
        v = first_val(k)
        if v and not str(row.get(col,"")).strip():
            row[col] = v

    # Parts included?
    pi = first_val("parts_included").lower()
    if pi:
        row["Ersatzteile_Inklusive"] = "Ja" if "inkl" in pi else "Nein"

    return pd.DataFrame([row])


def _enrich_summary_with_requested_fields(sum_de: pd.DataFrame, df_spans: pd.DataFrame, ents_df: pd.DataFrame) -> pd.DataFrame:
    if sum_de is None or sum_de.empty:
        return sum_de
    row = sum_de.iloc[0].to_dict()

    def get_first(subtype):
        try:
            d = df_spans[df_spans["subtype"]==subtype]
            if d is not None and not d.empty:
                return str(d.iloc[0]["value_norm"]).strip()
        except Exception:
            pass
        return ""

    # Aliases
    row["Vertragsnummer"] = row.get("Vertragsnummer") or get_first("contract_number") or row.get("ContractNo","")
    row["Vertragspartner"] = row.get("Parteien","")
    row["Vertragsgegenstand"] = row.get("Betreff","")
    row["Vertragsbeginn"] = row.get("Beginn","")
    row["Vertragsende"] = row.get("Ende","")

    # Kündigungsfrist (combine)
    km = row.get("Kündigungsfrist_Monate","") or ""
    kd = row.get("Kündigungsfrist_Tage","") or ""
    row["Kündigungsfrist"] = (f"{km} Monate" if str(km).strip() else (f"{kd} Tage" if str(kd).strip() else ""))

    # Verlängerung
    ar_m = row.get("Automatische_Verlängerung_Monate","") or row.get("Automatische_Verlaengerung","")
    if str(ar_m).strip():
        row["Verlängerung"] = f"Ja ({ar_m} Monate)"
    else:
        # check yes/no spans
        try:
            auto = df_spans[df_spans["subtype"]=="auto_renewal"]
            if not auto.empty:
                v = str(auto.iloc[0]["value_norm"]).lower()
                row["Verlängerung"] = "Ja" if "yes" in v or "ja" in v else "Nein"
        except Exception:
            pass

    # Vertragslaufzeit
    lt = row.get("Laufzeit_Monate","") or row.get("Mindestlaufzeit_Monate","") or ""
    row["Vertragslaufzeit"] = f"{lt} Monate" if str(lt).strip() else ""

    # Kosten p.a. / p.M.
    row["Kosten [€ p.a.]"] = row.get("Kosten_pro_Jahr_EUR","")
    row["Kosten {€ p.M.]"] = row.get("Kosten_pro_Monat_EUR","") or row.get("Kosten/Monatlich","")
    row["Kosten/Monatlich"] = row.get("Kosten_pro_Monat_EUR","")

    # Zusatzkosten
    row["Zusatzkosten"] = row.get("Zusätzliche_Kosten_EUR","")

    # Zahlungsweise
    parts = []
    iv = get_first("payment_interval");  parts.append(iv) if iv else None
    adv = get_first("payment_advance");   parts.append("im Voraus") if adv else None
    pm = get_first("payment_method");    parts.append(pm) if pm else None
    row["Zahlungsweise"] = ", ".join([p for p in parts if p])

    # Leistungsumfang (jährlich): aggregate 'service_scope_yearly' OR compose from periodicities
    sc = ""
    try:
        d = df_spans[df_spans["subtype"]=="service_scope_yearly"]
        if d is not None and not d.empty:
            vals = d["value_norm"].astype(str).tolist()
            sc = "; ".join(vals[:5])
    except Exception:
        pass
    if not sc:
        w = get_first("wartung_period")
        i = get_first("inspektion_period")
        k = get_first("kalibrierung_period")
        chunks = []
        if w: chunks.append(f"Wartung: {w}")
        if i: chunks.append(f"Inspektion: {i}")
        if k: chunks.append(f"Kalibrierung: {k}")
        sc = "; ".join(chunks)
    row["Leistungsumfang (jährlich)"] = sc

    # Pflichten des Kunden / Haftung (presence or short excerpt)
    def _excerpt(sub):
        try:
            d = df_spans[df_spans["subtype"]==sub]
            if d is not None and not d.empty:
                txt = str(d.iloc[0]["text_raw"])
                return (txt[:220] + "…") if len(txt) > 220 else txt
        except Exception:
            pass
        return ""

    row["Pflichten des Kunden"] = "Ja" if get_first("customer_obligations") else ""
    if not row["Pflichten des Kunden"]:
        row["Pflichten des Kunden"] = _excerpt("customer_obligations")

    row["Haftung"] = "Ja" if get_first("liability") else ""
    if not row["Haftung"]:
        row["Haftung"] = _excerpt("liability")

    # Kontakt (email/phone)
    def _first_contact(st):
        try:
            d = df_spans[(df_spans["type"]=="contact") & (df_spans["subtype"]==st)]
            if d is not None and not d.empty:
                return str(d.iloc[0]["value_norm"]).strip()
        except Exception:
            pass
        return ""

    email = _first_contact("email")
    phone = _first_contact("phone")
    contact = "; ".join([x for x in [email, phone] if x])
    row["Kontakt"] = contact

    return pd.DataFrame([row])


# Roles_Aggregation
def _enrich_summary_with_roles(sum_de: pd.DataFrame, ents_df: pd.DataFrame) -> pd.DataFrame:
    if sum_de is None or sum_de.empty or ents_df is None or ents_df.empty:
        return sum_de
    row = sum_de.iloc[0].to_dict()
    def names(role_key):
        try:
            d = ents_df[ents_df["role"].str.lower()==role_key]
            if d is None or d.empty: return ""
            vals = d["canonical_name"].fillna(d["entity_name"] if "entity_name" in d.columns else "").astype(str).tolist()
            vals = [v for v in vals if v]
            return "; ".join(vals[:3])
        except Exception:
            return ""
    row["Auftraggeber"] = names("customer") or names("auftraggeber")
    row["Auftragnehmer"] = names("provider") or names("auftragnehmer")
    row["Kunde"] = names("kunde") or names("customer")
    row["Lieferant"] = names("lieferant") or names("provider")
    return pd.DataFrame([row])


def _enrich_summary_with_legal_pricing(sum_de: pd.DataFrame, df_spans: pd.DataFrame) -> pd.DataFrame:
    if sum_de is None or sum_de.empty:
        return sum_de
    row = sum_de.iloc[0].to_dict()

    def first_val(st):
        try:
            d = df_spans[df_spans["subtype"]==st]
            if d is not None and not d.empty:
                return str(d.iloc[0]["value_norm"]).strip()
        except Exception:
            pass
        return ""

    # Zahlungsziel/Skonto/Verzug
    row["Zahlungsziel_Tage"] = first_val("payment_due_days")
    row["Skonto_%"] = first_val("skonto_percent")
    row["Verzugszinsen_%"] = first_val("default_interest_percent") or first_val("default_interest_over_basis")

    # Haftungsobergrenze
    row["Haftungsobergrenze_EUR"] = first_val("liability_cap_amount")
    row["Haftungsobergrenze_%"] = first_val("liability_cap_percent")

    # DSGVO / AVV / TOMs
    row["DSGVO"] = "Ja" if first_val("dsgvo") else "Nein"
    row["AVV"] = "Ja" if first_val("avv") else "Nein"
    row["TOMs"] = "Ja" if first_val("toms") else "Nein"

    # Wettbewerbs-/Abwerbeverbot
    row["Wettbewerbsverbot"] = "Ja" if first_val("non_compete") else "Nein"
    row["Abwerbeverbot"] = "Ja" if first_val("non_solicit") else "Nein"

    # Indexation & Service Credits presence
    row["Indexierung"] = "Ja" if first_val("indexation_present") or first_val("index_raise_percent_pa") else "Nein"
    row["Index_Cap_%"] = first_val("index_cap_percent")
    row["Service_Credits"] = "Ja" if first_val("service_credit_present") else "Nein"
    row["SC_Trigger_LT_%"] = first_val("service_credit_trigger_uptime_lt")
    row["SC_%"] = first_val("service_credit_percent")

    return pd.DataFrame([row])

def _enrich_summary_with_finance_sla_travel(sum_de: pd.DataFrame, df_spans: pd.DataFrame) -> pd.DataFrame:
    if sum_de is None or sum_de.empty:
        return sum_de
    row = sum_de.iloc[0].to_dict()

    def first(st):
        try:
            d = df_spans[df_spans["subtype"]==st]
            if d is not None and not d.empty:
                return str(d.iloc[0]["value_norm"]).strip()
        except Exception:
            pass
        return ""

    # Netto/MwSt/Brutto
    row["Netto_EUR"] = first("net_amount_eur")
    row["MwSt_EUR"] = first("vat_amount_eur")
    row["Brutto_EUR"] = first("gross_amount_eur")

    # Zuschläge vorhanden?
    has_pct = df_spans is not None and not df_spans.empty and not df_spans[df_spans["subtype"]=="oncall_surcharge_percent"].empty
    has_eurh = df_spans is not None and not df_spans.empty and not df_spans[df_spans["subtype"]=="oncall_surcharge_eur_per_hour"].empty
    row["Zuschläge_vorhanden"] = "Ja" if (has_pct or has_eurh) else "Nein"

    # Anfahrt
    row["Anfahrt_pro_km_EUR"] = first("travel_per_km_eur")
    row["Anfahrt_Pauschale_EUR"] = first("travel_flat_eur")

    # Teile-Deckel (jährlich)
    row["Ersatzteile_Deckel_Jahr_EUR"] = first("parts_cap_per_year_eur")

    return pd.DataFrame([row])
