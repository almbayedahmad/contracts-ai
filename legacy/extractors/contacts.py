
import re
from core.schemas import ExtractItem, ExtractBatch
from core.registry import register_extractor
from extractors.base import BaseExtractor

@register_extractor(name="contacts", version="0.1.0")
class ContactsExtractor(BaseExtractor):
    rx_email = re.compile(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}')
    rx_phone = re.compile(r'(\+?\d[\d \-()/]{6,}\d)')

    def extract(self, doc_id, text):
        items = []
        for m in self.rx_email.finditer(text):
            items.append(ExtractItem(item_type="contact", subtype="email",
                                     text_raw=m.group(0), value_norm=m.group(0).lower(),
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))
        for m in self.rx_phone.finditer(text):
            ph = m.group(1).strip()
            items.append(ExtractItem(item_type="contact", subtype="phone",
                                     text_raw=ph, value_norm=ph.replace(" ", ""),
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))
        return ExtractBatch(doc_id=doc_id, items=items)
