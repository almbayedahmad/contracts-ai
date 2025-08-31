
import re
from core.schemas import ExtractItem, ExtractBatch
from core.registry import register_extractor
from extractors.base import BaseExtractor

ORG_HINTS = r'(?:GmbH|AG|UG|UG\s*\(haftungsbeschränkt\)|OHG|KG|GmbH\s*&\s*Co\.\s*KG|KGaA|e\.K\.|eG|SE|GbR|PartG|PartGmbB|Ltd|LLC|Inc\.?|S\.A\.|SARL|PLC|Unternehmen|Gesellschaft|Firma)'

@register_extractor(name="parties", version="0.2.1")
class PartiesExtractor(BaseExtractor):
    # Quoted names
    rx_quoted = re.compile(r'["“”„»«]\s*([^"“”„»«]{2,120}?)\s*["“”„»«]')
    # Organizations by legal form
    rx_org = re.compile(rf'\b{ORG_HINTS}\b[^\n,().:;]{{0,120}}', re.IGNORECASE)
    # Persons with titles
    rx_person = re.compile(r'\b(Herr|Frau|Dr\.|Mr\.?|Ms\.?|Mrs\.?)\s+([^\n,().]{2,80})', re.IGNORECASE)

    def _clean(self, name: str) -> str:
        name = (name or "").strip().strip(' "“”„»«')
        name = re.sub(r'\s{2,}', ' ', name)
        return name

    def extract(self, doc_id, text):
        items = []
        t = text

        # Organizations by legal form
        for m in self.rx_org.finditer(t):
            # Expand capture to include preceding name if present
            left = t[max(0, m.start()-80):m.start()]
            right = t[m.end():m.end()+80]
            # Try to capture a company name ending at the legal form
            cand = re.search(r'([A-ZÄÖÜ][^,\n().:;]{2,180}?\s*' + ORG_HINTS + r')', left + t[m.start():m.end()] + right, re.IGNORECASE)
            raw = cand.group(1) if cand else t[m.start():m.end()]
            val = self._clean(raw)
            items.append(ExtractItem(item_type="party", subtype="org", text_raw=raw, value_norm=val,
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        # Quoted names → often company names
        for m in self.rx_quoted.finditer(t):
            val = self._clean(m.group(1))
            if len(val) >= 3:
                items.append(ExtractItem(item_type="party", subtype="quoted", text_raw=m.group(0), value_norm=val,
                                         start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        # Persons
        for m in self.rx_person.finditer(t):
            val = self._clean(m.group(2))
            items.append(ExtractItem(item_type="party", subtype="person", text_raw=m.group(0), value_norm=val,
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        return ExtractBatch(doc_id=doc_id, items=items)
