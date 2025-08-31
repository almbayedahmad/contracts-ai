
import re
from core.schemas import ExtractItem, ExtractBatch
from core.registry import register_extractor
from extractors.base import BaseExtractor

@register_extractor(name="legal", version="0.1.0")
class LegalExtractor(BaseExtractor):
    rx_law = re.compile(r'\b(deutsches\s+recht|german\s+law)\b', re.IGNORECASE)
    rx_cisg_excl = re.compile(r'\bCISG\b.*?(?:nicht|ausgeschlossen|keine Anwendung)', re.IGNORECASE)
    rx_juris = re.compile(r'\bGerichtsstand\b[^\.:\n\r]*?(?:ist|in|am|:)?\s*([A-ZÄÖÜ][A-Za-zÄÖÜäöüß\-]+)', re.IGNORECASE)

    def extract(self, doc_id, text):
        items = []
        if self.rx_law.search(text):
            items.append(ExtractItem(item_type="clause", subtype="governing_law",
                                     text_raw="deutsches Recht", value_norm="DE",
                                     start=None, end=None, extractor=self.__class__.__name__, version=self.__version__))
        if self.rx_cisg_excl.search(text):
            items.append(ExtractItem(item_type="clause", subtype="cisg_excluded",
                                     text_raw="CISG excluded", value_norm="yes",
                                     start=None, end=None, extractor=self.__class__.__name__, version=self.__version__))
        m = self.rx_juris.search(text)
        if m:
            city = m.group(1)
            items.append(ExtractItem(item_type="clause", subtype="jurisdiction",
                                     text_raw=m.group(0).strip(), value_norm=city,
                                     start = m.start(1), end = m.end(1), extractor=self.__class__.__name__, version=self.__version__))
        return ExtractBatch(doc_id=doc_id, items=items)
