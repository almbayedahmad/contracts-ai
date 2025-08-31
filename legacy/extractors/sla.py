
import re
from core.schemas import ExtractItem, ExtractBatch
from core.registry import register_extractor
from extractors.base import BaseExtractor

@register_extractor(name="sla", version="0.1.0")
class SLAExtractor(BaseExtractor):
    rx_react = re.compile(r'\breaktionszeit\b.*?\b(\d{1,3})\s*(?:stunden|h)\b', re.IGNORECASE | re.DOTALL)
    rx_hours = re.compile(r'(montag\s*bis\s*freitag|mo\.\s*-\s*fr\.)[^\n\r]*?\b(\d{1,2})[:\.](\d{2})\s*uhr?\s*(?:bis|-)\s*(\d{1,2})[:\.](\d{2})\s*uhr?', re.IGNORECASE)
    rx_surcharge = re.compile(r'(\d{1,3})\s*-%-?\s*zuschlag', re.IGNORECASE)
    rx_loaner = re.compile(r'\b(leihgerät|ersatzgerät)\b', re.IGNORECASE)

    def extract(self, doc_id, text):
        items = []
        m = self.rx_react.search(text)
        if m:
            items.append(ExtractItem(item_type="other", subtype="reaction_time_hours",
                                     text_raw=m.group(0).strip(), value_norm=m.group(1),
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        m = self.rx_hours.search(text)
        if m:
            hh1, mm1, hh2, mm2 = m.group(2), m.group(3), m.group(4), m.group(5)
            val = f"Mo-Fr {int(hh1):02d}:{mm1}-{int(hh2):02d}:{mm2}"
            items.append(ExtractItem(item_type="other", subtype="business_hours",
                                     text_raw=m.group(0).strip(), value_norm=val,
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        m = self.rx_surcharge.search(text)
        if m:
            items.append(ExtractItem(item_type="other", subtype="weekend_surcharge_percent",
                                     text_raw=m.group(0).strip(), value_norm=m.group(1),
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        if self.rx_loaner.search(text):
            items.append(ExtractItem(item_type="other", subtype="loaner_device",
                                     text_raw="loaner_device", value_norm="yes",
                                     start=None, end=None, extractor=self.__class__.__name__, version=self.__version__))

        return ExtractBatch(doc_id=doc_id, items=items)
