
# Development Notes (English)

This repository targets **German contracts**. The **UI and final outputs are in German**. All **development documentation** is in English.

## Extractors overview
- `dates.py`: German date formats (DD.MM.YYYY, textual months), start/end/durations.
- `money.py`: EUR parsing with German number formats, VAT (%), cost per month/year.
- `pricing.py`: Monthly/Yearly schedules from text (24–36 Monat(e), bis, ab dem) and inline amounts.
- `totals.py`: Gesamtsumme/Vertragssumme detection.
- `terms.py`: (Mindest)laufzeit, Kündigungsfrist (days/months), payment start event, auto-renewal.
- `sla.py`: Reaction time (hours), business hours (Mo–Fr HH:MM–HH:MM), weekend surcharges.
- `legal.py`: Governing law (DE), jurisdiction (city), CISG exclusion.
- `ids.py`, `contacts.py`, `parties.py`: Contract/customer numbers, emails/phones, parties (org/person) in DE/EN.
- All extractors are registered via `@register_extractor` and enabled in `pipeline/config.yml`.

## PriceSchedule (tables + text)
- DOCX **tables** are parsed **header-aware** (column synonyms: von/bis/Monat/Jahr/Betrag/Preis/Kosten).
- Text patterns: `24.–36. Monat`, `24 bis 36 Monate`, `ab dem 24. Monat`, `im 1. Jahr`.
- Unified sheet `PriceSchedule` with columns: `type, subtype, amount_eur, unit, start_month, end_month, year_index, raw`.
- Summary enrichment fills `Kosten_pro_Monat_EUR`, `Kosten_pro_Jahr_EUR`, and derives `Freimonate=12` if year 1 is 0 EUR.

## Compliance engine
Rules (German descriptions in `rules/policies.yml`) include:
- Presence (date/money), Laufzeit ≥ 24 months (min/term), Kündigungsfrist ≥ 30 days or ≥ 2 months,
- SLA reaction time ≤ 48h, Start ≤ End, Governing law ⇒ Jurisdiction present,
- VAT present if EUR prices appear, PriceSchedule required if costs per month/year are present,
- Year 1 = 0 EUR ⇒ Freimonate = 12 (info), Entities must include both customer & provider roles.

## UI (German-only)
- Streamlit app shows tabs: **Überblick, Spans, Entitäten, Beziehungen, Preise, Compliance**.
- Overview card includes: Laufzeit, Kündigungsfrist, MwSt, Kosten/Monat, Kosten/Jahr, Gerichtsstand, Rechtswahl, CISG, Freimonate, Reaktionszeit, Arbeitszeiten, Fixed per call, Zahlungsbeginn, Vertrags-/Kundennummer.
- Download full Excel result from the UI.

## Coding guidelines
- Prefer robust regex with `re.DOTALL` and support DE number formatting.
- Keep internal identifiers in English when useful, but **UI labels/policies in German**.
- No Arabic tokens in code, regex, or policies to avoid confusion.
- Add new extractors in `extractors/` and list them in `pipeline/config.yml`.

## Testing checklist
- Run `python -m pipeline.runner_api <file.docx> data/output/out.xlsx` and review: `Spans`, `Entities`, `Links`, `PriceSchedule`, `ContractSummary_DE`, `Compliance`.
- Validate PriceSchedule ranges and amounts against the DOCX tables.
- Confirm Compliance rules fire correctly and display in the UI.
