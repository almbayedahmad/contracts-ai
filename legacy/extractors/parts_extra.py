
import re
from core.schemas import ExtractItem, ExtractBatch
from core.registry import register_extractor
from extractors.base import BaseExtractor

@register_extractor(name="parts_extra", version="0.1.0")
class PartsExtraExtractor(BaseExtractor):
    # Annual cap for spare/wear parts
    rx_cap_year = re.compile(r'(Ersatzteile|Verschlei[ßs]teile)[^.\n\r]{0,80}?(?:Max\.?|maximal|Deckel|Obergrenze|bis zu)[^0-9\n\r]{0,20}(\d{1,4}(?:[.\s]\d{3})*(?:,\d{1,2})?)\s*(?:EUR|€)\s*(?:pro\s*Jahr|p\.a\.|j[aä]hrlich)', re.IGNORECASE)

    def extract(self, doc_id, text):
        items = []
        for m in self.rx_cap_year.finditer(text):
            items.append(ExtractItem(item_type="parts", subtype="parts_cap_per_year_eur",
                                     text_raw=m.group(0), value_norm=m.group(2),
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))
        return ExtractBatch(doc_id=doc_id, items=items)
