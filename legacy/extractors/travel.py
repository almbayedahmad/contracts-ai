
import re
from core.schemas import ExtractItem, ExtractBatch
from core.registry import register_extractor
from extractors.base import BaseExtractor

@register_extractor(name="travel", version="0.1.0")
class TravelExtractor(BaseExtractor):
    rx_trig = re.compile(r'\b(Anfahrt|Anfahrtskosten|Fahrtkosten)\b', re.IGNORECASE)
    rx_per_km = re.compile(r'(Anfahrtskosten|Fahrtkosten)[^0-9\n]{0,40}?(\d{1,2}(?:[.,]\d{1,2})?)\s*€\s*/\s*km', re.IGNORECASE)
    rx_flat = re.compile(r'(Anfahrtskosten|Fahrtkosten|Anfahrt)[^0-9\n]{0,60}?(\d{1,4}(?:[.\s]\d{3})*(?:,\d{1,2})?)\s*(?:EUR|€)\b[^a-zA-Z\n]{0,10}(?:Pauschale|pauschal)?', re.IGNORECASE)

    def extract(self, doc_id, text):
        items = []
        for m in self.rx_trig.finditer(text):
            items.append(ExtractItem(item_type="travel", subtype="travel_trigger",
                                     text_raw=m.group(0), value_norm="present",
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))
        for m in self.rx_per_km.finditer(text):
            items.append(ExtractItem(item_type="travel", subtype="travel_per_km_eur",
                                     text_raw=m.group(0), value_norm=m.group(2),
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))
        for m in self.rx_flat.finditer(text):
            items.append(ExtractItem(item_type="travel", subtype="travel_flat_eur",
                                     text_raw=m.group(0), value_norm=m.group(2),
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))
        return ExtractBatch(doc_id=doc_id, items=items)
