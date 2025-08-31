
import importlib, yaml, pandas as pd
from pathlib import Path
from core.registry import REGISTRY
from io_ops.readers import read_docx_text, read_pdf_text, read_txt
from io_ops.writers import batches_to_excel
from rules.engine import evaluate_compliance
import pkgutil, extractors

# auto-import all extractors to register them via decorators
for _, modname, _ in pkgutil.iter_modules(extractors.__path__):
    if modname not in ("__init__", "base"):
        importlib.import_module(f"extractors.{modname}")

cfg = yaml.safe_load(open("pipeline/config.yml", "r", encoding="utf-8"))
in_path = Path(cfg["input_path"])
doc_id = in_path.stem

# read text
suffix = in_path.suffix.lower()
if suffix == ".docx":
    text = read_docx_text(str(in_path))
elif suffix == ".pdf":
    text = read_pdf_text(str(in_path))
elif suffix == ".txt":
    text = read_txt(str(in_path))
else:
    raise ValueError(f"Unsupported file type: {suffix}")

# run enabled extractors
enabled = set(cfg.get("use_extractors", []))
batches = []
for ext_cls in REGISTRY["extractors"]:
    if ext_cls.__extractor_name__ in enabled:
        ext = ext_cls()
        batches.append(ext.extract(doc_id, text))

# export spans
out_excel = cfg["output_excel"]
df_spans = batches_to_excel(batches, out_excel)

# compliance
policies = yaml.safe_load(open("rules/policies.yml", "r", encoding="utf-8"))
comp = evaluate_compliance(df_spans, policies)
if not comp.empty:
    with pd.ExcelWriter(out_excel, engine="openpyxl", mode="a", if_sheet_exists="replace") as xw:
        comp.to_excel(xw, index=False, sheet_name="Compliance")

# entities/links
from pipeline.summarize import summarize
summary_df = summarize(df_spans)
with pd.ExcelWriter(out_excel, engine="openpyxl", mode="a", if_sheet_exists="replace") as xw:
    summary_df.to_excel(xw, index=False, sheet_name="ContractSummary")

print(f"✅ Done → {out_excel}")


# --- Entities & Links sheets ---
from pipeline.postprocess import build_entities_links, build_price_schedule
ents_df, links_df = build_entities_links(df_spans, doc_id, text)
with pd.ExcelWriter(out_excel, engine="openpyxl", mode="a", if_sheet_exists="replace") as xw:
    if not ents_df.empty:
        ents_df.to_excel(xw, index=False, sheet_name="Entities")
    else:
        pd.DataFrame(columns=["entity_id","entity_type","canonical_name","aliases","normalized_ids"]).to_excel(xw, index=False, sheet_name="Entities")
    if not links_df.empty:
        links_df.to_excel(xw, index=False, sheet_name="Links")
    else:
        pd.DataFrame(columns=["subject_id","predicate","object_id","evidence_span_id"]).to_excel(xw, index=False, sheet_name="Links")

# --- ContractSummary sheet ---
from pipeline.summarize import summarize
summary_df = summarize(df_spans)
with pd.ExcelWriter(out_excel, engine="openpyxl", mode="a", if_sheet_exists="replace") as xw:
    summary_df.to_excel(xw, index=False, sheet_name="ContractSummary")


# --- PriceSchedule sheet ---
ps_df = build_price_schedule(df_spans)
with pd.ExcelWriter(out_excel, engine="openpyxl", mode="a", if_sheet_exists="replace") as xw:
    if ps_df is not None:
        ps_df.to_excel(xw, index=False, sheet_name="PriceSchedule")
