
import re
from core.schemas import ExtractItem, ExtractBatch
from core.registry import register_extractor
from extractors.base import BaseExtractor

@register_extractor(name="sla_extra", version="0.1.0")
class SLAExtraExtractor(BaseExtractor):
    # Uptime/Verfügbarkeit %
    rx_uptime = re.compile(r'\b(Verfügbarkeit|Betriebsbereitschaft|Uptime)\b[^%\n\r]{0,60}?(\d{1,3}(?:,\d{1,2})?)\s*%', re.IGNORECASE)

    # Periodicities (monatlich/vierteljährlich/quartalsweise/jährlich/halbjährlich / alle X Monate)
    RX_PER_WORD = r'(monatlich|viertelj[aä]hrlich|quartalsweise|j[aä]hrlich|halbj[aä]hrlich)'
    rx_period_generic = re.compile(RX_PER_WORD, re.IGNORECASE)
    rx_period_xmon = re.compile(r'alle\s+(\d{1,2})\s*Monate', re.IGNORECASE)

    # Anchors for activities
    rx_wartung = re.compile(r'\b(Wartung|Instandhaltung)\b', re.IGNORECASE)
    rx_inspek = re.compile(r'\bInspektion\b', re.IGNORECASE)
    rx_kalib  = re.compile(r'\bKalibrierung|Kalibrieren\b', re.IGNORECASE)

    # Parts inclusion (inklusive/exklusive)
    rx_parts_incl = re.compile(r'\b(Ersatzteile|Verschlei[ßs]teile)\b[^.\n\r]{0,60}?\b(inkl(?:usive)?|einschließlich)\b', re.IGNORECASE)
    rx_parts_excl = re.compile(r'\b(Ersatzteile|Verschlei[ßs]teile)\b[^.\n\r]{0,60}?\b(exkl(?:usive)?|nicht\s*enthalten|ausgeschlossen)\b', re.IGNORECASE)

    def extract(self, doc_id, text):
        items = []
        t = text

        for m in self.rx_uptime.finditer(t):
            label = "Uptime/Verfügbarkeit"
            val = m.group(2)
            items.append(ExtractItem(item_type="other", subtype="uptime_percent",
                                     text_raw=m.group(0), value_norm=val, unit="percent",
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        def _emit_period(subtype, mspan, raw, val):
            items.append(ExtractItem(item_type="other", subtype=subtype,
                                     text_raw=raw, value_norm=val, unit=None,
                                     start=mspan[0], end=mspan[1], extractor=self.__class__.__name__, version=self.__version__))

        # Maintenance periodicities around anchors (look ±120 chars)
        for rx_anchor, subtype in [(self.rx_wartung, "wartung_period"),
                                   (self.rx_inspek, "inspektion_period"),
                                   (self.rx_kalib, "kalibrierung_period")]:
            for ma in rx_anchor.finditer(t):
                s = max(0, ma.start()-120); e = min(len(t), ma.end()+120)
                ctx = t[s:e]
                m1 = self.rx_period_generic.search(ctx)
                if m1:
                    _emit_period(subtype, (s+m1.start(), s+m1.end()), ctx[m1.start():m1.end()], m1.group(1).lower())
                    continue
                m2 = self.rx_period_xmon.search(ctx)
                if m2:
                    _emit_period(subtype, (s+m2.start(), s+m2.end()), ctx[m2.start():m2.end()], f"{m2.group(1)} Monate")
                    continue

        # Parts inclusion/exclusion
        for m in self.rx_parts_incl.finditer(t):
            items.append(ExtractItem(item_type="other", subtype="parts_included",
                                     text_raw=m.group(0), value_norm="inklusive", unit=None,
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))
        for m in self.rx_parts_excl.finditer(t):
            items.append(ExtractItem(item_type="other", subtype="parts_included",
                                     text_raw=m.group(0), value_norm="exklusive", unit=None,
                                     start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

        return ExtractBatch(doc_id=doc_id, items=items)


# Yearly service scope like "2 Wartungen pro Jahr", "1 Inspektion/Jahr", "100 Einsätze pro Jahr"
rx_scope = re.compile(r'(\d{1,3})\s+(Wartungen|Wartung|Inspektionen|Inspektion|Kalibrierungen|Kalibrierung|Einsätze|Einsatz|Stunden)\s*(?:/|pro)\s*Jahr', re.IGNORECASE)

def _emit_scope(self, m):
    count = m.group(1)
    kind = m.group(2)
    return ExtractItem(item_type="other", subtype="service_scope_yearly",
                       text_raw=m.group(0), value_norm=f"{count} {kind}/Jahr",
                       start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__)

def extract(self, doc_id, text):
    # re-run parent logic by duplicating due to decorator constraints (simple merge)
    items = []
    t = text

    # --- existing patterns (uptime/periods/parts) ---
    for m in self.rx_uptime.finditer(t):
        items.append(ExtractItem(item_type="other", subtype="uptime_percent",
                                 text_raw=m.group(0), value_norm=m.group(2), unit="percent",
                                 start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

    def _emit_period(subtype, mspan, raw, val):
        items.append(ExtractItem(item_type="other", subtype=subtype,
                                 text_raw=raw, value_norm=val, unit=None,
                                 start=mspan[0], end=mspan[1], extractor=self.__class__.__name__, version=self.__version__))

    for rx_anchor, subtype in [(self.rx_wartung, "wartung_period"),
                               (self.rx_inspek, "inspektion_period"),
                               (self.rx_kalib, "kalibrierung_period")]:
        for ma in rx_anchor.finditer(t):
            s = max(0, ma.start()-120); e = min(len(t), ma.end()+120)
            ctx = t[s:e]
            m1 = self.rx_period_generic.search(ctx)
            if m1:
                _emit_period(subtype, (s+m1.start(), s+m1.end()), ctx[m1.start():m1.end()], m1.group(1).lower()); continue
            m2 = self.rx_period_xmon.search(ctx)
            if m2:
                _emit_period(subtype, (s+m2.start(), s+m2.end()), ctx[m2.start():m2.end()], f"{m2.group(1)} Monate"); continue

    for m in self.rx_parts_incl.finditer(t):
        items.append(ExtractItem(item_type="other", subtype="parts_included",
                                 text_raw=m.group(0), value_norm="inklusive", unit=None,
                                 start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))
    for m in self.rx_parts_excl.finditer(t):
        items.append(ExtractItem(item_type="other", subtype="parts_included",
                                 text_raw=m.group(0), value_norm="exklusive", unit=None,
                                 start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))

    # --- new: yearly service scope ---
    for m in self.rx_scope.finditer(t):
        items.append(self._emit_scope(m))

    return ExtractBatch(doc_id=doc_id, items=items)


# On-call/night/weekend/holiday surcharges
rx_oncall_trig = re.compile(r'\b(Rufbereitschaft|Bereitschaftsdienst|Rufdienst|Nacht|Wochenende|Feiertag)\b', re.IGNORECASE)
rx_oncall_pct  = re.compile(r'(Rufbereitschaft|Nacht|Wochenende|Feiertag)[^%\n\r]{0,60}?(\d{1,2}(?:[.,]\d{1,2})?)\s*%', re.IGNORECASE)
rx_oncall_eurh = re.compile(r'(Rufbereitschaft|Nacht|Wochenende|Feiertag)[^€\n\r]{0,60}?(\d{1,3}(?:[.\s]\d{3})*(?:,\d{1,2})?)\s*€\s*/\s*(?:h|Std\.?|Stunde[n]?)', re.IGNORECASE)

def _emit_oncall(self, subtype, m):
    return ExtractItem(item_type="sla", subtype=subtype, text_raw=m.group(0),
                       value_norm=m.group(2) if m.lastindex and m.lastindex>=2 else "present",
                       start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__)

# extend extract by wrapping original
_orig_extract = extract
def extract(self, doc_id, text):
    batch = _orig_extract(self, doc_id, text)
    items = list(batch.items or [])

    for m in self.rx_oncall_trig.finditer(text):
        items.append(ExtractItem(item_type="sla", subtype="oncall_trigger",
                                 text_raw=m.group(0), value_norm="present",
                                 start=m.start(), end=m.end(), extractor=self.__class__.__name__, version=self.__version__))
    for m in self.rx_oncall_pct.finditer(text):
        items.append(self._emit_oncall("oncall_surcharge_percent", m))
    for m in self.rx_oncall_eurh.finditer(text):
        items.append(self._emit_oncall("oncall_surcharge_eur_per_hour", m))

    return ExtractBatch(doc_id=doc_id, items=items)
