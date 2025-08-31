from __future__ import annotations
import re
from typing import List
from core.schemas import ExtractBatch, ExtractItem

SEC_RE = re.compile(r"(?P<h>(?:§\s*|)^)(?P<num>1)\s*[.)]?\s+Vertragsgegenstand\b", re.I)
NEXT_HEADER = re.compile(r"(?:\n|\r)(?:\s*§\s*\d+\s+\w+|\s*\d+[.)]\s+\w+)", re.I)

def _extract_section(text: str, header_rx: re.Pattern, next_header_rx: re.Pattern):
    m = header_rx.search(text)
    if not m:
        alt = re.compile(r"(^|\n)\s*1[.)]?\s+Vertragsgegenstand\b", re.I)
        m = alt.search(text)
        if not m:
            return None
    start = m.start()
    n = next_header_rx.search(text, m.end())
    end = n.start() if n else len(text)
    return text[start:end].strip()

class SectionExtractor:
    __name__ = "SectionExtractor"
    __version__ = "1.0.0"

    def extract(self, doc_id: str, text: str) -> ExtractBatch:
        items: List[ExtractItem] = []
        sec1 = _extract_section(text, SEC_RE, NEXT_HEADER)
        if sec1:
            items.append(ExtractItem(
                item_type="clause",
                subtype="subject",
                text_raw=sec1,
                value_norm=None,
                page=None, para=None,
                start=text.find(sec1), end=text.find(sec1)+len(sec1),
                extractor=self.__class__.__name__,
                version=self.__version__,
                confidence=0.92,
            ))
        return ExtractBatch(doc_id=doc_id, items=items)
