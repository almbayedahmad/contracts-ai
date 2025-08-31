
## 2025-08-26 v13b
- Added persistent **error logging** to `logs/error.log` and guarded pipeline execution with try/except.
- Implemented robust file readers `_read_text` and `_read_text_and_tables` (TXT/DOCX/PDF) with safe `seek(0)` handling.
- Made sample display defensive (no crash when `data/input/sample_de.txt` is missing).
- Protected loading of `rules/policies.yml` (fallback to empty dict if file is absent).
- This change enforces policy: **always update CHANGELOG and maintain error logs** for any new features.

## 2025-08-26 v13c (hotfix)
- Fix: IndentationError around guarded `policies.yml` loader on Windows.

## 2025-08-26 v13d
- Reordered compliance block and fixed indentation for Windows. Now: Entities → PriceSchedule → Policies → Compliance.

## 2025-08-26 v13e
- Canonical rewrite of `run_local_pipeline` to fix indentation and block order (Windows-safe). Added explicit return order.

## 2025-08-26 v13f
- Global hardening: added `_safe_run_pipeline()` and replaced direct calls to avoid indentation-sensitive try/except blocks. Normalized line endings. Ensured policies are only loaded inside pipeline.

## 2025-08-26 v13g
- Canonicalized guarded policies block indentation and enforced `_safe_run_pipeline` usage.

## 2025-08-26 v13h
- Full rewrite of `app/ui_streamlit.py` with canonical 4-space indentation and LF endings. Added `_safe_run_pipeline` wrapper, hardened readers, and consistent Excel output.

## 2025-08-26 v13h-hotfix-legal
- Fix (extractors/legal): corrected jurisdiction regex grouping and span indices to avoid IndexError when text lacks optional groups. Ensured start/end use group(1).

## 2025-08-26 v13h-hotfix-lexicon
- Guarded YAML loading in `extractors/lexicon.py` with sanitizer for regex escapes in double-quoted scalars (e.g., "Response\\s*Time"). Falls back to doubled backslashes and retries parsing.

## 2025-08-26 v13h2
- UI: extractor init/run now resilient (logs error, continues pipeline).
- Lexicon: safe YAML loader with regex-escape sanitizer to avoid ScannerError on patterns like "Response\s*Time".

## 2025-08-26 v13h3
- Replaced `app/ui_streamlit.py` with fully validated version to resolve 'return outside function' SyntaxError.

## 2025-08-26 v13h4
- Fix: pass `full_text` to `build_entities_links` in `run_local_pipeline`.
- Tests: added `test_entities_signature.py` to ensure call includes full_text.

## 2025-08-26 v13h5
- Tests: updated stubs to accept `full_text` in `build_entities_links` signature.
- Fix: made lexicon sanitizer docstring a raw string to silence escape warnings.
