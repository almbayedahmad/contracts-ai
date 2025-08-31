
# Legal Extractor Hotfix

- Ensured jurisdiction regex captures the city in **group(1)**.
- Replaced `m.group(2)` with `m.group(1)`.
- Standardized span bounds to `m.start(1)` / `m.end(1)` to match the captured city.
- Preserved other extractor behavior.
