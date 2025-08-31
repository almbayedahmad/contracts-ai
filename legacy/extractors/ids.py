
import re
from core.schemas import ExtractItem, ExtractBatch
from core.registry import register_extractor
from extractors.base import BaseExtractor

@register_extractor(name="ids", version="0.1.0")
class IdsExtractor(BaseExtractor):
    rx_contract = re.compile(r'\b(?:Vertr\.-?Nr\.|Vertragsnummer|Servicevertrag\s*Nr\.)\s*[:#]?\s*([A-Z0-9\-\.\/]+)', re.IGNORECASE)
    rx_customer = re.compile(r'\b(Kunden-?Nr\.|Kundennummer)\s*[:#]?\s*([A-Z0-9\-\.\/]+)', re.IGNORECASE)

    def extract(self, doc_id, text):
        items = []
        for m in self.rx_contract.finditer(text):
            items.append(ExtractItem(item_type="id", subtype="contract_number",
                                     text_raw=m.group(0).strip(), value_norm=m.group(1).strip(),
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))
        for m in self.rx_customer.finditer(text):
            items.append(ExtractItem(item_type="id", subtype="customer_number",
                                     text_raw=m.group(0).strip(), value_norm=m.group(2).strip(),
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))
        return ExtractBatch(doc_id=doc_id, items=items)
