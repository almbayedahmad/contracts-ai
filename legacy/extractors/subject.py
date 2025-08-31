
import re
from core.schemas import ExtractItem, ExtractBatch
from core.registry import register_extractor
from extractors.base import BaseExtractor

@register_extractor(name="subject", version="0.1.0")
class SubjectExtractor(BaseExtractor):
    # Arabic: "عقد ..." / "اتفاق ..." / "اتفاقية ..."
    rx_ar = re.compile(r'\b(عقد|اتفاق|اتفاقية)\s+[^\n.]{1,120}')
    # English: "Contract for ..." / "Service Agreement ..." / "Master Agreement ..."
    rx_en = re.compile(r'\b(Contract|Agreement)\s+[^\n.]{1,160}', re.IGNORECASE)

    def extract(self, doc_id, text):
        items = []
        m = self.rx_ar.search(text) or self.rx_en.search(text)
        if m:
            subj = m.group(0).strip()
            items.append(ExtractItem(
                item_type="clause", subtype="subject",
                text_raw=subj, value_norm=subj,
                start=m.start(), end=m.end(),
                extractor=self.__class__.__name__, version=self.__version__
            ))
        return ExtractBatch(doc_id=doc_id, items=items)
