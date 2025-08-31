
import re
from core.schemas import ExtractItem, ExtractBatch
from core.registry import register_extractor
from extractors.base import BaseExtractor

@register_extractor(name="legal_deep", version="0.1.0")
class LegalDeepExtractor(BaseExtractor):
    # Zahlungsziel: "zahlbar innerhalb 30 Tagen", "Zahlungsziel 14 Tage", "Netto 30"
    rx_pay_days = re.compile(r'(zahlbar\s+innerhalb\s+|Zahlungsziel\s+|Netto\s*)(\d{1,3})\s*Tage', re.IGNORECASE)

    # Skonto: "Skonto 2%", "2 % Skonto bei Zahlung innerhalb 10 Tagen"
    rx_skonto = re.compile(r'(Skonto)[^%\n\r]{0,30}?(\d{1,2}(?:[.,]\d{1,2})?)\s*%', re.IGNORECASE)

    # Verzugszinsen: "Verzugszins[e] X% p.a.", "5 % über dem Basiszinssatz"
    rx_verzug_pct = re.compile(r'(Verzugszins\w*|Zinsen)[^%\n\r]{0,50}?(\d{1,2}(?:[.,]\d{1,2})?)\s*%\s*(?:p\.a\.|pro\s*Jahr)?', re.IGNORECASE)
    rx_basiszins = re.compile(r'(\d{1,2}(?:[.,]\d{1,2})?)\s*%\s*(?:über|ueber)\s*dem\s*Basiszinssatz', re.IGNORECASE)

    # Haftungsobergrenze: Betrag (EUR) أو نسبة من Preis
    rx_liab_cap_amt = re.compile(r'(Haftungsobergrenze|Haftung\b[^.\n]{0,40}?\bbegrenzt)\b[^0-9\n]{0,40}?(\d{1,3}(?:[.\s]\d{3})*(?:[.,]\d{1,2})?)\s*(?:EUR|€)', re.IGNORECASE)
    rx_liab_cap_pct = re.compile(r'(Haftungsobergrenze|Haftung\b[^.\n]{0,40}?\bbegrenzt)\b[^%\n]{0,40}?(\d{1,2}(?:[.,]\d{1,2})?)\s*%', re.IGNORECASE)

    # DSGVO/AVV/TOMs
    rx_dsgvo = re.compile(r'\b(DSGVO|GDPR|Datenschutz-Grundverordnung)\b', re.IGNORECASE)
    rx_avv = re.compile(r'\b(Auftragsverarbeitung|AVV|Auftragsverarbeitungsvertrag)\b', re.IGNORECASE)
    rx_toms = re.compile(r'\b(technische\s+und\s+organisatorische\s+Ma[ßs]nahmen|TOMs?)\b', re.IGNORECASE)

    # Wettbewerbsverbot / Abwerbeverbot
    rx_compete = re.compile(r'\b(Wettbewerbsverbot|Konkurrenzverbot)\b', re.IGNORECASE)
    rx_poach = re.compile(r'\b(Abwerbeverbot|Abwerbung)\b', re.IGNORECASE)

    # Sitz (registered office) + einfache Stadt/Ort Erkennung
    rx_sitz = re.compile(r'\bSitz\b[^.\n]{0,40}?\b([A-ZÄÖÜ][a-zäöüß]+(?:[-\s][A-ZÄÖÜa-zäöüß]+)?)', re.IGNORECASE)

    def extract(self, doc_id, text):
        items = []
        t = text

        for m in self.rx_pay_days.finditer(t):
            items.append(ExtractItem(item_type="money", subtype="payment_due_days",
                                     text_raw=m.group(0), value_norm=m.group(2),
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        for m in self.rx_skonto.finditer(t):
            items.append(ExtractItem(item_type="money", subtype="skonto_percent",
                                     text_raw=m.group(0), value_norm=m.group(2), unit="percent",
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        for m in self.rx_verzug_pct.finditer(t):
            items.append(ExtractItem(item_type="money", subtype="default_interest_percent",
                                     text_raw=m.group(0), value_norm=m.group(2), unit="percent",
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))
        for m in self.rx_basiszins.finditer(t):
            items.append(ExtractItem(item_type="money", subtype="default_interest_over_basis",
                                     text_raw=m.group(0), value_norm=m.group(1), unit="percent_over_basis",
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        for m in self.rx_liab_cap_amt.finditer(t):
            items.append(ExtractItem(item_type="clause", subtype="liability_cap_amount",
                                     text_raw=m.group(0), value_norm=m.group(2),
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))
        for m in self.rx_liab_cap_pct.finditer(t):
            items.append(ExtractItem(item_type="clause", subtype="liability_cap_percent",
                                     text_raw=m.group(0), value_norm=m.group(2), unit="percent",
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        for rx, sub in [(self.rx_dsgvo,"dsgvo"), (self.rx_avv,"avv"), (self.rx_toms,"toms"),
                        (self.rx_compete,"non_compete"), (self.rx_poach,"non_solicit")]:
            for m in rx.finditer(t):
                items.append(ExtractItem(item_type="clause", subtype=sub,
                                         text_raw=m.group(0), value_norm="present",
                                         start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        for m in self.rx_sitz.finditer(t):
            # normalize to city string
            city = m.group(1).strip()
            items.append(ExtractItem(item_type="party", subtype="seat_city",
                                     text_raw=m.group(0), value_norm=city,
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        return ExtractBatch(doc_id=doc_id, items=items)
