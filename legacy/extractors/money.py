
import re
from core.schemas import ExtractItem, ExtractBatch
from core.registry import register_extractor
from extractors.base import BaseExtractor
from core.utils import normalize_digits

@register_extractor(name="money", version="1.2.0")
class MoneyExtractor(BaseExtractor):
    # Money pattern allowing German format 1.234,56 with optional symbol/name
    rx_money = re.compile(
        r'\b(?:[$€]|EUR|USD|SAR|SYP)?\s?\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?\s?(?:[$€]|EUR|USD|SAR|SYP|Euro|euro|دولار|ريال|يورو|ل\.س)?\b'
    )

    # Percent (supports % and ٪)
    rx_percent = re.compile(r'\b\d{1,3}(?:[.,]\d+)?\s?[%%٪]\b')

    # Durations (DE/AR/EN)
    rx_days = re.compile(r'\b(\d{1,4})\s*(?:يوم|يوماً|أيام|day|days|tag|tage|tagen)\b', re.IGNORECASE)
    rx_months = re.compile(r'\b(\d{1,4})\s*(?:شهر|أشهر|month|months|monat|monate|monaten)\b', re.IGNORECASE)

    # IBAN generic
    rx_iban = re.compile(r'\b[A-Z]{2}\d{2}[A-Z0-9]{1,30}\b')

    window = 80

    def _ctx(self, text, start, end):
        return (text[max(0, start-self.window):min(len(text), end+self.window)]).lower()

    def _currency_from_text(self, s: str):
        s = s.lower()
        if "eur" in s or "€" in s or "euro" in s or "يورو" in s:
            return "EUR"
        if "usd" in s or "$" in s or "dollar" in s or "دولار" in s:
            return "USD"
        if "sar" in s or "ريال" in s:
            return "SAR"
        if "syp" in s or "ل.س" in s or "ليرة" in s:
            return "SYP"
        return None

    def extract(self, doc_id, text):
        t = normalize_digits(text)
        items = []

        # Money
        for m in self.rx_money.finditer(t):
            raw = m.group(0).strip()
            ctx = self._ctx(t, m.start(), m.end())
            subtype = None
            unit = None

            # per month/year
            if any(k in ctx for k in ["شهري", "شهريًا", "per month", "p.m", "/month", "بالشهر", "monatlich", "pro monat", "/monat"]):
                subtype, unit = "cost_per_month", "month"
            elif any(k in ctx for k in ["سنوي", "سنوياً", "per year", "p.a", "/year", "بالسنة", "jährlich", "pro jahr", "/jahr"]):
                subtype, unit = "cost_per_year", "year"
            elif any(k in ctx for k in ["رسوم إضافية", "تكاليف إضافية", "extra cost", "surcharge", "fee", "zusätzliche gebühren", "zusatzkosten", "aufschlag"]):
                subtype = "extra_cost"

            currency = self._currency_from_text(raw) or self._currency_from_text(ctx)

            items.append(ExtractItem(
                item_type="money",
                subtype=subtype,
                text_raw=raw,
                value_norm=raw,
                currency=currency,
                unit=unit,
                start=m.start(), end=m.end(),
                extractor=self.__class__.__name__,
                version=self.__version__
            ))

        # Percent (VAT)
        for m in self.rx_percent.finditer(t):
            raw = m.group(0)
            ctx = self._ctx(t, m.start(), m.end())
            subtype = "percent"
            if any(k in ctx for k in ["vat", "ضريبة القيمة المضافة", "القيمة المضافة", "ضريبة", "tax", "mwst", "ust", "umsatzsteuer", "mehrwertsteuer"]):
                subtype = "vat_percent"
            items.append(ExtractItem(
                item_type="money",
                subtype=subtype,
                text_raw=raw,
                value_norm=raw.replace("٪", "%"),
                start=m.start(), end=m.end(),
                extractor=self.__class__.__name__,
                version=self.__version__
            ))

        # Durations
        for m in self.rx_days.finditer(t):
            n = m.group(1)
            ctx = self._ctx(t, m.start(), m.end())
            subtype = "duration_days"
            if any(k in ctx for k in ["إشعار", "اخطار", "إخطار", "notice", "بلاغ", "إبلاغ", "kündigungsfrist", "kuendigungsfrist", "frist"]):
                subtype = "notice_days"
            items.append(ExtractItem(
                item_type="money",
                subtype=subtype,
                text_raw=m.group(0),
                value_norm=str(int(n)),
                unit="days",
                start=m.start(), end=m.end(),
                extractor=self.__class__.__name__,
                version=self.__version__
            ))

        for m in self.rx_months.finditer(t):
            n = m.group(1)
            ctx = self._ctx(t, m.start(), m.end())
            subtype = "duration_months"
            if any(k in ctx for k in ["تجدد", "تلقائي", "auto renew", "renewal", "verlängert", "verlanger", "verlängerung", "automatische verlängerung"]):
                subtype = "auto_renew_months"
            items.append(ExtractItem(
                item_type="money",
                subtype=subtype,
                text_raw=m.group(0),
                value_norm=str(int(n)),
                unit="months",
                start=m.start(), end=m.end(),
                extractor=self.__class__.__name__,
                version=self.__version__
            ))

        # IBAN
        for m in self.rx_iban.finditer(t):
            items.append(ExtractItem(
                item_type="money",
                subtype="iban",
                text_raw=m.group(0),
                value_norm=m.group(0).replace(" ", ""),
                start=m.start(), end=m.end(),
                extractor=self.__class__.__name__,
                version=self.__version__
            ))

        return ExtractBatch(doc_id=doc_id, items=items)


import re as _re
from core.schemas import ExtractItem, ExtractBatch

try:
    MoneyExtractor
except NameError:
    from core.registry import register_extractor
    from extractors.base import BaseExtractor
    @register_extractor(name='money_plus', version='0.1.0')
    class MoneyExtractor(BaseExtractor):
        def extract(self, doc_id, text):
            return ExtractBatch(doc_id=doc_id, items=[])

# German money patterns
_rx_num_eur = r'(\d{1,3}(?:[.\s]\d{3})*(?:,\d{1,2})?)\s*(?:EUR|€)'
_rx_netto  = _re.compile(r'(Netto(?:betrag)?)\s*[:\-]?\s*' + _rx_num_eur, _re.IGNORECASE)
_rx_brutto = _re.compile(r'(Brutto(?:betrag)?)\s*[:\-]?\s*' + _rx_num_eur, _re.IGNORECASE)
_rx_mwst_amt = _re.compile(r'(?:MwSt|USt|Umsatzsteuer)[^0-9\n]{0,20}' + _rx_num_eur, _re.IGNORECASE)
_rx_mwst_pct = _re.compile(r'(?:MwSt|USt|Umsatzsteuer)[^%\n]{0,20}(\d{1,2}(?:[.,]\d{1,2})?)\s*%', _re.IGNORECASE)

_old_extract = getattr(MoneyExtractor, 'extract', None)

def _money_plus_extract(self, doc_id, text):
    items = []
    t = text

    for m in _rx_netto.finditer(t):
        items.append(ExtractItem(item_type="money", subtype="net_amount_eur",
                                 text_raw=m.group(0), value_norm=m.group(2),
                                 start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))
    for m in _rx_brutto.finditer(t):
        items.append(ExtractItem(item_type="money", subtype="gross_amount_eur",
                                 text_raw=m.group(0), value_norm=m.group(2),
                                 start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))
    for m in _rx_mwst_amt.finditer(t):
        items.append(ExtractItem(item_type="money", subtype="vat_amount_eur",
                                 text_raw=m.group(0), value_norm=m.group(1),
                                 start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))
    for m in _rx_mwst_pct.finditer(t):
        items.append(ExtractItem(item_type="money", subtype="vat_percent",
                                 text_raw=m.group(0), value_norm=m.group(1),
                                 start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

    if callable(_old_extract):
        try:
            prev = _old_extract(self, doc_id, text)
            items.extend(prev.items or [])
        except Exception:
            pass

    return ExtractBatch(doc_id=doc_id, items=items)

MoneyExtractor.extract = _money_plus_extract
