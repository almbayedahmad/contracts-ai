
import re
from core.schemas import ExtractItem, ExtractBatch
from core.registry import register_extractor
from extractors.base import BaseExtractor

@register_extractor(name="obl_liability", version="0.1.0")
class ObligationsLiabilityExtractor(BaseExtractor):
    rx_obl = re.compile(r'(Pflichten des Kunden|Mitwirkungspflichten|Obliegenheiten des Kunden)', re.IGNORECASE)
    rx_liab = re.compile(r'(Haftung|Haftungsbeschr[aä]nkung|Haftungsausschluss)', re.IGNORECASE)

    def _grab(self, text, m, window=350):
        s = max(0, m.start())
        e = min(len(text), m.end() + window)
        return text[s:e].strip()

    def extract(self, doc_id, text):
        items = []
        for m in self.rx_obl.finditer(text):
            raw = self._grab(text, m)
            items.append(ExtractItem(item_type="clause", subtype="customer_obligations",
                                     text_raw=raw, value_norm="present", start=m.start(), end=m.end(),
                                     extractor=self.__class__.__name__, version=self.__version__))
        for m in self.rx_liab.finditer(text):
            raw = self._grab(text, m)
            items.append(ExtractItem(item_type="clause", subtype="liability",
                                     text_raw=raw, value_norm="present", start=m.start(), end=m.end(),
                                     extractor=self.__class__.__name__, version=self.__version__))
        return ExtractBatch(doc_id=doc_id, items=items)
