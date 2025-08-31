
import re
from core.schemas import ExtractItem, ExtractBatch
from core.registry import register_extractor
from extractors.base import BaseExtractor

@register_extractor(name="indexation_credits", version="0.1.0")
class IndexationCreditsExtractor(BaseExtractor):
    # Indexation: VPI/CPI/Indexierung/Erhöhung um X% jährlich (cap optional)
    rx_index_vpi = re.compile(r'(Verbraucherpreisindex|VPI|CPI|Indexierung|Preisgleitklausel)', re.IGNORECASE)
    rx_raise_pct_year = re.compile(r'(Erh[öo]hung|Anpassung)[^%\n]{0,40}?(\d{1,2}(?:[.,]\d{1,2})?)\s*%\s*(?:p\.a\.|pro\s*Jahr|jährlich)', re.IGNORECASE)
    rx_cap_pct = re.compile(r'(?:Max\.?|maximal|Deckelung|Kappung)[^%\n]{0,40}?(\d{1,2}(?:[.,]\d{1,2})?)\s*%', re.IGNORECASE)

    # Service Credits: Gutschrift/Credit bei Verfügbarkeit < X%
    rx_credit = re.compile(r'(Gutschrift|Servicegutschrift|Credit)\b', re.IGNORECASE)
    rx_uptime_trigger = re.compile(r'Verfügbarkeit[^%\n]{0,40}?<\s*(\d{1,3}(?:[.,]\d{1,2})?)\s*%', re.IGNORECASE)
    rx_credit_pct = re.compile(r'(\d{1,2}(?:[.,]\d{1,2})?)\s*%\s*(?:Gutschrift|Credit)', re.IGNORECASE)

    def extract(self, doc_id, text):
        items = []
        t = text

        # Indexation presence
        for m in self.rx_index_vpi.finditer(t):
            items.append(ExtractItem(item_type="pricing", subtype="indexation_present",
                                     text_raw=m.group(0), value_norm="present",
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        # Yearly raise with percent
        for m in self.rx_raise_pct_year.finditer(t):
            items.append(ExtractItem(item_type="pricing", subtype="index_raise_percent_pa",
                                     text_raw=m.group(0), value_norm=m.group(2), unit="percent_pa",
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        # Cap percent if stated
        for m in self.rx_cap_pct.finditer(t):
            items.append(ExtractItem(item_type="pricing", subtype="index_cap_percent",
                                     text_raw=m.group(0), value_norm=m.group(1), unit="percent",
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        # Service credits (presence + trigger threshold + credit %)
        credit_found = False
        for m in self.rx_credit.finditer(t):
            credit_found = True
            items.append(ExtractItem(item_type="pricing", subtype="service_credit_present",
                                     text_raw=m.group(0), value_norm="present",
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        for m in self.rx_uptime_trigger.finditer(t):
            items.append(ExtractItem(item_type="pricing", subtype="service_credit_trigger_uptime_lt",
                                     text_raw=m.group(0), value_norm=m.group(1), unit="percent",
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        for m in self.rx_credit_pct.finditer(t):
            items.append(ExtractItem(item_type="pricing", subtype="service_credit_percent",
                                     text_raw=m.group(0), value_norm=m.group(1), unit="percent",
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        return ExtractBatch(doc_id=doc_id, items=items)
