# Fix Report – v13b

## What was fixed
1. **Streamlit crash on missing sample file**: replaced hard read with a defensive block.
2. **NameError `_read_text_and_tables`**: ensured robust readers exist and are imported.
3. **Uncaught pipeline exceptions**: added try/except around pipeline call + persistent logging to `logs/error.log`.
4. **Missing policies.yml**: handled via try/except with safe fallback.

## How to verify
- Start the app: `python -m streamlit run app/ui_streamlit.py`.
- If `data/input/sample_de.txt` is absent, UI shows an info message rather than crashing.
- Trigger a pipeline run on a test file; check `logs/error.log` if something goes wrong.

## Files changed
- `app/ui_streamlit.py`
- `CHANGELOG.md`
- `README_EN.md`
- `logs/error.log` (created on first run)
- `data/input/sample_de.txt` (example created)

## Permanent policy
- Future contributions must update the changelog and log errors to `logs/error.log`.

### 2025-08-26 – v13f
- Replaced inline try/except around pipeline call with `_safe_run_pipeline()` helper to prevent IndentationError.
- Normalized imports & logging. Removed stray top-level `policies = ...` lines.
- Verified sample display guard and readers.


### 2025-08-26 – v13h
- Replaced previous patchwork with a clean, validated UI module. Verified by AST parse to prevent IndentationError.
