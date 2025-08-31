
import types
import builtins
import importlib
import pytest

def test_read_docx_with_fallback(monkeypatch, tmp_path):
    # Create a dummy file path
    p = tmp_path / "dummy.docx"
    p.write_bytes(b"not a real docx, but ok for test")

    # Import module
    rdr = importlib.import_module('pipeline.reader')

    # Monkeypatch Document to raise and docx2txt.process to return text
    class DummyDoc:
        def __init__(self, *a, **k):
            raise ValueError('docx parse error')

    monkeypatch.setattr(rdr, 'Document', DummyDoc, raising=True)
    monkeypatch.setattr(rdr, 'docx2txt', types.SimpleNamespace(process=lambda path: 'HEADER\n§ 1 Vertragsgegenstand\nText...'), raising=True)

    txt, meta = rdr.read_docx_with_fallback(str(p), prefer='python-docx')
    assert meta['had_fallback'] is True
    assert isinstance(txt, str) and len(txt) > 0
