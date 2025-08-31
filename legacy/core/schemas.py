
from typing import Literal, List, Optional
from pydantic import BaseModel

ItemType = Literal["date","money","party","clause","contact","id","other"]

class ExtractItem(BaseModel):
    item_type: ItemType
    subtype: Optional[str] = None
    text_raw: str
    value_norm: Optional[str] = None
    currency: Optional[str] = None
    unit: Optional[str] = None
    page: Optional[int] = None
    para: Optional[int] = None
    start: Optional[int] = None
    end: Optional[int] = None
    confidence: float = 1.0
    extractor: str
    version: str

class ExtractBatch(BaseModel):
    doc_id: str
    items: List[ExtractItem]
