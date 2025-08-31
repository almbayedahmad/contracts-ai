import re as _re
import yaml as _yaml
import logging as _logging

def _sanitize_yaml_regex_escapes(raw_text: str) -> str:
    r"""
    Double-escape common regex escapes inside double-quoted YAML scalars (e.g., "Response\s*Time").
    """
    pattern = _re.compile(r'(?<!\\)\\([sdwbnrtDWBS.])')
    return pattern.sub(r'\\\\\1', raw_text)

def _safe_load_yaml_with_regex(path):
    raw = path.read_text(encoding='utf-8')
    try:
        return _yaml.safe_load(raw)
    except _yaml.YAMLError as e:
        _logging.getLogger('contracts-ai.lexicon').warning('YAML parse failed; applying sanitizer: %s', e)
        fixed = _sanitize_yaml_regex_escapes(raw)
        return _yaml.safe_load(fixed)


import re, yaml
from pathlib import Path
from core.schemas import ExtractItem, ExtractBatch
from core.registry import register_extractor
from extractors.base import BaseExtractor

@register_extractor(name="lexicon", version="0.1.0")
class LexiconExtractor(BaseExtractor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        path = Path(__file__).resolve().parents[1] / "lexicon" / "medtech_de.yml"
        spec = _safe_load_yaml_with_regex(path)
        self.concepts = []
        for c in spec.get("concepts", []):
            patt = [re.compile(p, re.IGNORECASE) for p in c.get("patterns", [])]
            self.concepts.append({
                "id": c["id"],
                "label": c["label"],
                "category": c.get("category",""),
                "description": c.get("description",""),
                "patterns": patt
            })

    def extract(self, doc_id, text):
        items = []
        for c in self.concepts:
            for rx in c["patterns"]:
                for m in rx.finditer(text):
                    raw = m.group(0)
                    items.append(ExtractItem(
                        item_type="other",  # was "concept"; constrained by ItemType Literal
                        
                        subtype=c["id"],
                        text_raw=raw,
                        value_norm=c["label"],
                        start=m.start(),
                        end=m.end(),
                        extractor=self.__class__.__name__,
                        version=self.__version__
                    ))
        return ExtractBatch(doc_id=doc_id, items=items)