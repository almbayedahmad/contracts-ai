
import re
from core.schemas import ExtractItem, ExtractBatch
from core.registry import register_extractor
from extractors.base import BaseExtractor
from core.utils import normalize_digits

@register_extractor(name="terms", version="0.1.0")
class TermsExtractor(BaseExtractor):
    win = 80

    # Kündigung: "mit einer Frist von drei Monaten ..." -> notice_months
    rx_notice_months = re.compile(r'\b(?:frist|kündigungsfrist|kuendigungsfrist)\b.*?\b(\d{1,3})\s*monate?n\b', re.IGNORECASE | re.DOTALL)
    # Mindestlaufzeit: "Mindestlaufzeit: 96 Monate"
    rx_min_term = re.compile(r'\bmindestlaufzeit\b.*?\b(\d{1,4})\s*monate?n\b', re.IGNORECASE)
    # Free months: "entgeltfrei während der ersten 24 Monate"
    rx_free_months = re.compile(r'\b(entgeltfrei|kostenfrei|kostenlos)\b.*?\b(\d{1,3})\s*monate?n\b', re.IGNORECASE)
    # Payment start event: "Zahlungsbeginn: Nach Ablauf der GWL"
    rx_pay_start_event = re.compile(r'\bzahlungsbeginn\b\s*:\s*([^\n\r]+)', re.IGNORECASE)
    # Auto-renewal: detect negation or presence
    rx_auto_yes = re.compile(r'\b(verlängert\s+sich\s+automatisch|automatische\s+verlängerung)\b', re.IGNORECASE)
    rx_auto_no = re.compile(r'\bwird\s+nicht\s+automatisch\s+verlängert\b', re.IGNORECASE)

    def extract(self, doc_id, text):
        t = normalize_digits(text)
        items = []

        m = self.rx_notice_months.search(t)
        if m:
            items.append(ExtractItem(item_type="other", subtype="notice_months",
                                     text_raw=m.group(0).strip(), value_norm=m.group(1),
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        m = self.rx_min_term.search(t)
        if m:
            items.append(ExtractItem(item_type="other", subtype="min_term_months",
                                     text_raw=m.group(0).strip(), value_norm=m.group(1),
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        m = self.rx_free_months.search(t)
        if m:
            items.append(ExtractItem(item_type="other", subtype="free_months",
                                     text_raw=m.group(0).strip(), value_norm=m.group(2),
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        m = self.rx_pay_start_event.search(t)
        if m:
            items.append(ExtractItem(item_type="other", subtype="payment_start_event",
                                     text_raw=m.group(0).strip(), value_norm=m.group(1).strip(),
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        if self.rx_auto_yes.search(t):
            items.append(ExtractItem(item_type="other", subtype="auto_renewal", text_raw="auto_renewal_yes", value_norm="yes",
                                     start=None, end=None, extractor=self.__class__.__name__, version=self.__version__))
        if self.rx_auto_no.search(t):
            items.append(ExtractItem(item_type="other", subtype="auto_renewal", text_raw="auto_renewal_no", value_norm="no",
                                     start=None, end=None, extractor=self.__class__.__name__, version=self.__version__))

        return ExtractBatch(doc_id=doc_id, items=items)
