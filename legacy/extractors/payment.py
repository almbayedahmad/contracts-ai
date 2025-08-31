
import re
from core.schemas import ExtractItem, ExtractBatch
from core.registry import register_extractor
from extractors.base import BaseExtractor

@register_extractor(name="payment", version="0.1.0")
class PaymentExtractor(BaseExtractor):
    rx_interval = re.compile(r'\b(j[aä]hrlich|monatlich|viertelj[aä]hrlich|quartalsweise|halbj[aä]hrlich)\b', re.IGNORECASE)
    rx_advance  = re.compile(r'\b(im\s+Voraus|vorauszahl)\w*\b', re.IGNORECASE)
    rx_method   = re.compile(r'\b(SEPA[-\s]?Lastschrift|Lastschrift|Rechnung|[ÜU]berweisung|Bank[ -]?[Tt]ransfer)\b', re.IGNORECASE)

    def extract(self, doc_id, text):
        items = []

        for m in self.rx_interval.finditer(text):
            items.append(ExtractItem(item_type="other", subtype="payment_interval",
                                     text_raw=m.group(0), value_norm=m.group(0).lower(), start=m.start(), end=m.end(),
                                     extractor=self.__class__.__name__, version=self.__version__))

        for m in self.rx_advance.finditer(text):
            items.append(ExtractItem(item_type="other", subtype="payment_advance",
                                     text_raw=m.group(0), value_norm="im Voraus", start=m.start(), end=m.end(),
                                     extractor=self.__class__.__name__, version=self.__version__))

        for m in self.rx_method.finditer(text):
            val = m.group(0)
            items.append(ExtractItem(item_type="other", subtype="payment_method",
                                     text_raw=val, value_norm=val, start=m.start(), end=m.end(),
                                     extractor=self.__class__.__name__, version=self.__version__))

        return ExtractBatch(doc_id=doc_id, items=items)
