
from core.schemas import ExtractBatch

class BaseExtractor:
    name = "base"
    version = "0.0.1"
    def extract(self, doc_id: str, text: str) -> ExtractBatch:
        raise NotImplementedError
