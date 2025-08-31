
import re
from core.schemas import ExtractItem, ExtractBatch
from core.registry import register_extractor
from extractors.base import BaseExtractor

@register_extractor(name="totals", version="0.1.0")
class TotalsExtractor(BaseExtractor):
    rx_total_line = re.compile(
        r'(Gesamtsumme|Gesamtbetrag|Vertragssumme|Gesamtpreis|Preis\s*gesamt)[^0-9]{0,40}([0-9]{1,3}(?:\.[0-9]{3})*(?:,[0-9]{2})?)\s*(€|EUR)',
        re.IGNORECASE
    )

    def extract(self, doc_id, text):
        items = []
        for m in self.rx_total_line.finditer(text):
            amt = m.group(2)
            items.append(ExtractItem(
                item_type="money", subtype="total_amount", text_raw=m.group(0),
                value_norm=f"{amt} EUR", currency="EUR",
                start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__
            ))
        return ExtractBatch(doc_id=doc_id, items=items)
