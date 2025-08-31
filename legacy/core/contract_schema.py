
from __future__ import annotations

# Canonical Contract Facts Schema
CONTRACT_SCHEMA = {
    "meta": {
        "contract_id": {"type": "id", "subtype": "contract_id", "description": "Interne ID oder Vertragsnummer"},
        "contract_title": {"type": "other", "subtype": "contract_title", "description": "Titel/Name des Vertrags"},
        "contract_type": {"type": "clause", "subtype": "contract_type", "description": "Dienstleistungsvertrag, Kaufvertrag, Mietvertrag …"},
    },

    "parties": {
        "party_a_name": {"type": "party", "subtype": "company", "description": "Name Partei A (juristische Person)"},
        "party_a_address": {"type": "other", "subtype": "party_a_address", "description": "Adresse Partei A"},
        "party_a_legal_form": {"type": "other", "subtype": "party_a_legal_form", "description": "Rechtsform Partei A (GmbH/AG/…)"},
        "party_b_name": {"type": "party", "subtype": "individual", "description": "Name Partei B (natürliche Person/Unternehmen)"},
        "party_b_address": {"type": "other", "subtype": "party_b_address", "description": "Adresse Partei B"},
        "party_b_legal_form": {"type": "other", "subtype": "party_b_legal_form", "description": "Rechtsform Partei B"},
        "signatories": {"type": "other", "subtype": "signatory", "description": "Unterzeichner + Funktion (z.B. Geschäftsführer)"},
    },

    "term": {
        "start_date": {"type": "date", "subtype": "start_date", "description": "Beginn des Vertrags"},
        "end_date": {"type": "date", "subtype": "end_date", "description": "Ende des Vertrags"},
        "duration_months": {"type": "other", "subtype": "duration_months", "description": "Gesamtdauer in Monaten"},
        "auto_renewal": {"type": "other", "subtype": "auto_renewal", "description": "Automatische Verlängerung (Ja/Nein + Bedingungen)"},
        "termination_notice": {"type": "other", "subtype": "termination_notice_weeks_to_month_end", "description": "Kündigungsfrist (z.B. X Wochen zum Monatsende)"},
    },

    "obligations": {
        "a_obligations": {"type": "clause", "subtype": "obligations_a", "description": "Leistungen von Partei A"},
        "b_obligations": {"type": "clause", "subtype": "obligations_b", "description": "Leistungen von Partei B"},
        "sla": {"type": "clause", "subtype": "sla", "description": "Service Levels, Qualität"},
        "deliverables": {"type": "clause", "subtype": "deliverables", "description": "Liefergegenstände + Termine"},
        "subject": {"type": "clause", "subtype": "subject", "description": "§1 Vertragsgegenstand (voller Text oder Auszug)"},
    },

    "financials": {
        "total_value": {"type": "money", "subtype": "total_fee", "description": "Vertragswert"},
        "currency": {"type": "other", "subtype": "currency", "description": "Währung (EUR, USD)"},
        "payment_terms": {"type": "other", "subtype": "payment_terms_days_after_invoice", "description": "Zahlungsbedingungen (z.B. innerhalb 14 Tagen netto)"},
        "payment_milestones": {"type": "clause", "subtype": "payment_milestones", "description": "Meilensteine"},
        "additional_costs": {"type": "money", "subtype": "additional_costs", "description": "Zusatzkosten (Auslagen, Reisekosten)"},
        "late_payment_interest": {"type": "other", "subtype": "late_payment_interest", "description": "Verzugszinsen"},
        "penalties": {"type": "other", "subtype": "penalties", "description": "Vertragsstrafen"},
        "vat_rate_percent": {"type": "other", "subtype": "vat_rate_percent", "description": "Umsatzsteuer in %"},
    },

    "ip_rights": {
        "ip_ownership": {"type": "clause", "subtype": "ip_ownership", "description": "Eigentum an Ergebnissen"},
        "usage_rights": {"type": "clause", "subtype": "usage_rights", "description": "Nutzungsrechte (exklusiv/nicht exklusiv)"},
        "sub_licensing": {"type": "clause", "subtype": "sub_licensing", "description": "Unterlizenzierung erlaubt?"},
    },

    "liability": {
        "warranty_period": {"type": "other", "subtype": "warranty_period", "description": "Garantiezeit"},
        "maintenance_procedure": {"type": "clause", "subtype": "maintenance_procedure", "description": "Korrektur-/Wartungsprozesse"},
        "liability_limit": {"type": "clause", "subtype": "liability_limit", "description": "Haftungsbegrenzung"},
        "liability_exclusions": {"type": "clause", "subtype": "liability_exclusions", "description": "Ausnahmen (Vorsatz, grobe Fahrlässigkeit, Personenschäden)"},
    },

    "confidentiality": {
        "confidentiality": {"type": "clause", "subtype": "confidentiality", "description": "Geheimhaltungsklausel"},
        "confidentiality_duration": {"type": "other", "subtype": "confidentiality_duration", "description": "Dauer der Geheimhaltung nach Vertragsende"},
        "data_protection": {"type": "clause", "subtype": "data_protection", "description": "DSGVO/GDPR"},
        "av_contract": {"type": "clause", "subtype": "av_contract", "description": "Auftragsverarbeitungsvertrag vorhanden?"},
    },

    "additional": {
        "governing_law": {"type": "other", "subtype": "governing_law", "description": "Anwendbares Recht (z.B. DE)"},
        "jurisdiction_city": {"type": "other", "subtype": "jurisdiction_city", "description": "Gerichtsstand (Stadt)"},
        "change_clause": {"type": "clause", "subtype": "change_clause", "description": "Änderungen nur schriftlich …"},
        "force_majeure": {"type": "clause", "subtype": "force_majeure", "description": "Höhere Gewalt"},
        "subcontractors": {"type": "clause", "subtype": "subcontractors", "description": "Subunternehmer zulässig?"},
        "non_compete": {"type": "clause", "subtype": "non_compete", "description": "Wettbewerbs-/Abwerbeverbote"},
        "audit_rights": {"type": "clause", "subtype": "audit_rights", "description": "Prüfungsrechte"},
        "penalties": {"type": "other", "subtype": "penalties", "description": "Vertragsstrafen (Zusammenfassung)"},
    },

    "management": {
        "reminder_dates": {"type": "other", "subtype": "reminder_dates", "description": "Erinnerungen: Verlängerung, Kündigung, Zahlungen"},
        "contract_owner": {"type": "other", "subtype": "contract_owner", "description": "Interner Verantwortlicher"},
        "risk_notes": {"type": "other", "subtype": "risk_notes", "description": "Risiken/Notizen"},
        "annexes": {"type": "other", "subtype": "annexes", "description": "Anhänge/Anlagen"},
    }
}

def schema_columns_flat() -> list[str]:
    cols = []
    for group, fields in CONTRACT_SCHEMA.items():
        for key in fields.keys():
            cols.append(key)
    return cols
