from __future__ import annotations
import pandas as pd
from core.contract_schema import CONTRACT_SCHEMA, schema_columns_flat

def align_keyfacts_to_schema(df_keyfacts: pd.DataFrame) -> pd.DataFrame:
    cols = ['party_1', 'party_2', 'contract_type', 'subject_snippet', 'total_fee', 'currency', 'vat_rate_percent', 'payment_terms_days', 'start_date', 'end_date', 'termination_notice_weeks_to_month_end', 'governing_law', 'jurisdiction_city']
    if df_keyfacts is None or df_keyfacts.empty:
        return pd.DataFrame(columns=cols)
    df = df_keyfacts.copy()
    row = {}
    map_simple = {
        'party_1':'party_1', 'party_2':'party_2', 'contract_type':'contract_type',
        'subject_snippet':'subject_snippet', 'total_fee':'total_fee', 'currency':'currency',
        'vat_rate_percent':'vat_rate_percent', 'payment_terms_days':'payment_terms_days',
        'start_date':'start_date', 'end_date':'end_date',
        'termination_notice_weeks_to_month_end':'termination_notice_weeks_to_month_end',
        'governing_law':'governing_law', 'jurisdiction_city':'jurisdiction_city'
    }
    for s, d in map_simple.items():
        if s in df.columns:
            row[d] = df.iloc[0].get(s)
    for c in cols:
        row.setdefault(c, None)
    out = pd.DataFrame([row])
    return out[cols]
import io, json
from typing import Dict, Any, Tuple
import pandas as pd

def export_results(spans_df: "pd.DataFrame", keyfacts: Dict[str, Any], diagnostics: Dict[str, Any], out_xlsx: str, out_json: str) -> bytes:
    # Ensure columns exist
    spans = spans_df.copy()
    for col in ["section_id","clause_title","provenance_text","confidence","extractor","pattern_id","context"]:
        if col not in spans.columns:
            spans[col] = None
    # Write Excel with three sheets
    with pd.ExcelWriter(out_xlsx, engine="openpyxl") as xw:
        # KeyFacts as one-row frame
        kf_df = pd.DataFrame([keyfacts])
        kf_df.to_excel(xw, sheet_name="KeyFacts", index=False)
        spans.to_excel(xw, sheet_name="Spans", index=False)
        # Diagnostics flattened
        diag_items = []
        for k,v in diagnostics.items():
            if isinstance(v, list):
                for it in v:
                    diag_items.append({"key": k, "value": it})
            else:
                diag_items.append({"key": k, "value": v})
        pd.DataFrame(diag_items).to_excel(xw, sheet_name="Diagnostics", index=False)

    # JSON
    payload = {"keyfacts": keyfacts, "diagnostics": diagnostics, "spans": spans.to_dict(orient="records")}
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    # Return Excel bytes for UI download if needed
    with open(out_xlsx, "rb") as f:
        return f.read()
