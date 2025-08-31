
import pandas as pd
from core.schemas import ExtractBatch

def batches_to_excel(batches: list[ExtractBatch], out_path: str):
    rows = []
    for b in batches:
        for it in b.items:
            rows.append({
                "doc_id": b.doc_id,
                "type": it.item_type,
                "subtype": it.subtype,
                "text_raw": it.text_raw,
                "value_norm": it.value_norm,
                "currency": it.currency,
                "unit": it.unit,
                "page": it.page, "para": it.para,
                "start": it.start, "end": it.end,
                "confidence": it.confidence,
                "extractor": it.extractor,
                "version": it.version
            })
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=["doc_id","type","subtype","text_raw","value_norm","currency","unit","page","para","start","end","confidence","extractor","version","span_id"])
    else:
        # assign a simple span_id per row: sp_000001, sp_000002, ...
        df = df.reset_index(drop=True)
        df["span_id"] = ["sp_" + str(i+1).zfill(6) for i in range(len(df))]
    df.to_excel(out_path, index=False, sheet_name="Spans")
    return df
