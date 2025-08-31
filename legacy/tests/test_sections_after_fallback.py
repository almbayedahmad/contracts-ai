
import importlib
import re
import pytest

def test_sections_after_fallback():
    norm = importlib.import_module('pipeline.normalize')
    text = '§ 1 Vertragsgegenstand\nA\n\n§ 2 Pflichten\nB\n\n§ 3 Vergütung\nC\n\n§ 4 Laufzeit\nD'
    s1 = norm._section(text, 1)
    s2 = norm._section(text, 2)
    s3 = norm._section(text, 3)
    s4 = norm._section(text, 4)
    assert s1 and s2 and s3 and s4
    assert all(len(x) > 0 for x in [s1, s2, s3, s4])
