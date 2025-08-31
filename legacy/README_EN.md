
# Contracts AI — German-first Contract Analysis

**General overview (English)**

This project provides a **local, rule-based** pipeline for analyzing **German** contracts:
- Extracts dates, amounts, parties, IDs, governing law, jurisdiction, SLAs, payment schedules.
- Reads **DOCX/PDF/TXT**, including **DOCX tables** (header-aware) to build a unified **PriceSchedule**.
- Produces an Excel with sheets: `Spans`, `Entities`, `Links`, `PriceSchedule`, `Compliance`, `ContractSummary`, `ContractSummary_DE`.
- A **Streamlit UI (German)** provides filtering, summaries, and downloads.

## Quickstart
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app/ui_streamlit.py
# Or process a single file to Excel:
python -m pipeline.runner_api "C:\path\to\contract.docx" "data\output\out.xlsx"
```

## Architecture (short)
- `extractors/` — modular regex/heuristics per domain (dates, money, terms, legal, parties, pricing, totals, ids, contacts, sla).
- `pipeline/` — orchestration: reading, post-processing (entities/links, price schedule), summaries, runners.
- `rules/` — compliance engine + policies (German). Engine checks presence, min values, date order, SLA thresholds, etc.
- `app/ui_streamlit.py` — German UI: Überblick, Spans, Entitäten, Beziehungen, Preise, Compliance.

## Extensibility
- Add a new extractor: `extractors/<name>.py` and register via `@register_extractor`.
- Add a compliance rule in `rules/policies.yml` (German descriptions).
- UI automatically shows new fields if added to summaries or sheets.


See **DEV_NOTES_EN.md** for detailed development notes.


### Error Logs
- Runtime errors are persisted in `logs/error.log` (rotated by deployment tooling if needed).
- The Streamlit UI wraps pipeline execution and reports exceptions without crashing the whole app.

### Development Policy (Maintained)
- Any new feature must:
  1) Add an entry to `CHANGELOG.md`.
  2) Write errors to `logs/error.log` or a dedicated module logger.
  3) Avoid hard crashes on missing optional sample files and configs.
