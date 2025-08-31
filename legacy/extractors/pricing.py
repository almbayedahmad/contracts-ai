
import re
from core.schemas import ExtractItem, ExtractBatch
from core.registry import register_extractor
from extractors.base import BaseExtractor

@register_extractor(name="pricing", version="0.2.0")
class PricingExtractor(BaseExtractor):
    # Monatsbereiche: "24.–36. Monat", "24.-36. Monat", "24 bis 36 Monate"
    rx_month_range1 = re.compile(r'(\d{1,3})\s*[\.\-–—]\s*(\d{1,3})\s*\.\s*Monat', re.IGNORECASE)
    rx_month_range2 = re.compile(r'(\d{1,3})\s*bis\s*(\d{1,3})\s*Monat(?:e)?', re.IGNORECASE)
    rx_month_from  = re.compile(r'ab\s*dem\s*(\d{1,3})\.\s*Monat', re.IGNORECASE)

    # Betrag باليورو في نفس السطر أو قريب
    rx_amount_eur  = re.compile(r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)\s*(?:€|EUR)', re.IGNORECASE)

    # Jahreskosten عبر أسطر: "Kosten/Jahr ... € 15.450,00"
    rx_cost_per_year = re.compile(r'Kosten\s*/\s*Jahr.*?(?:€|EUR)\s*([0-9\.\,]+)', re.IGNORECASE | re.DOTALL)

    # Fixed per call / pro Einsatz
    rx_per_call = re.compile(r'(?:fixed\s+per\s+call|pro\s+einsatz)\s*[:\-]?\s*([0-9\.\,]+)\s*(?:€|EUR)', re.IGNORECASE)

    def extract(self, doc_id, text):
        items = []

        # Monatsbereiche 24.-36. Monat
        for m in self.rx_month_range1.finditer(text):
            a, b = m.group(1), m.group(2)
            # حاول التقاط مبلغ بجوار النطاق
            ctx = text[max(0, m.start()-120):m.end()+120]
            am = self.rx_amount_eur.search(ctx)
            val = f"{am.group(1)} EUR per month [{a}-{b}]" if am else f"[{a}-{b}]"
            items.append(ExtractItem(item_type="money", subtype="price_schedule_monthly",
                                     text_raw=ctx.strip(), value_norm=val, unit="month",
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        # 24 bis 36 Monate
        for m in self.rx_month_range2.finditer(text):
            a, b = m.group(1), m.group(2)
            ctx = text[max(0, m.start()-120):m.end()+120]
            am = self.rx_amount_eur.search(ctx)
            val = f"{am.group(1)} EUR per month [{a}-{b}]" if am else f"[{a}-{b}]"
            items.append(ExtractItem(item_type="money", subtype="price_schedule_monthly",
                                     text_raw=ctx.strip(), value_norm=val, unit="month",
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        # ab dem 24. Monat
        for m in self.rx_month_from.finditer(text):
            a = m.group(1)
            ctx = text[max(0, m.start()-120):m.end()+120]
            am = self.rx_amount_eur.search(ctx)
            val = f"{am.group(1)} EUR per month [from {a}]" if am else f"[from {a}]"
            items.append(ExtractItem(item_type="money", subtype="price_schedule_monthly_from",
                                     text_raw=ctx.strip(), value_norm=val, unit="month",
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        # Jahreskosten
        for m in self.rx_cost_per_year.finditer(text):
            amt = m.group(1)
            payload = f"{amt} EUR per year"
            items.append(ExtractItem(item_type="money", subtype="price_per_year",
                                     text_raw=m.group(0), value_norm=payload, unit="year",
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        # Per call / pro Einsatz
        for m in self.rx_per_call.finditer(text):
            amt = m.group(1)
            items.append(ExtractItem(item_type="money", subtype="fixed_per_call",
                                     text_raw=m.group(0), value_norm=amt, unit=None,
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        return ExtractBatch(doc_id=doc_id, items=items)
