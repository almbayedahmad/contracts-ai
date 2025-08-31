
from __future__ import annotations
import re

# Normalize various whitespace/dashes and make section headers easier for regex
_RE_MULTISPACE = re.compile(r"[ \t\r\f\v]+")
_RE_FIX_SECTION_NO_SPACE = re.compile(r"§\s*(\d+)")
_RE_NBSP = re.compile(u"\xa0")

def normalize_text(s: str) -> str:
    if not s:
        return s
    # Unify newlines
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    # Replace NBSP with normal space
    s = _RE_NBSP.sub(" ", s)
    # Unify dashes/quotes
    s = s.replace("–", "-").replace("—", "-").replace("‚", "'").replace("“", '"').replace("”", '"')
    # Ensure a space after § numbers: §1 -> § 1
    s = _RE_FIX_SECTION_NO_SPACE.sub(r"§ \1", s)
    # Collapse multiple spaces (not newlines)
    s = "\n".join(_RE_MULTISPACE.sub(" ", line).strip() for line in s.split("\n"))
    # Deduplicate consecutive blank lines
    lines = [ln for ln in s.split("\n")]
    out = []
    prev_blank = False
    for ln in lines:
        blank = (ln.strip() == "")
        if blank and prev_blank:
            continue
        out.append(ln)
        prev_blank = blank
    s = "\n".join(out).strip()
    return s
