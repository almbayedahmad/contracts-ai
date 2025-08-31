
import importlib, types
from tests.helpers import FakeUpload

def test_build_entities_links_called_with_full_text(monkeypatch):
    ui = importlib.import_module("app.ui_streamlit")
    ui.REGISTRY["extractors"] = []  # avoid running real extractors

    calls = {}
    def stub_bel(df_spans, doc_id, full_text):
        calls["args"] = (df_spans, doc_id, full_text)
        import pandas as pd
        ents = pd.DataFrame([{"entity_id":"E1"}])
        links = pd.DataFrame([{"from_id":"E1","to_id":"E1","type":"self"}])
        return ents, links

    # stub price schedule builder too
    import sys, types, pandas as pd
    dummy_pipeline = types.ModuleType("pipeline")
    dummy_post = types.ModuleType("pipeline.postprocess")
    dummy_post.build_price_schedule = lambda df: pd.DataFrame()
    sys.modules["pipeline"] = dummy_pipeline
    sys.modules["pipeline.postprocess"] = dummy_post

    ui.build_entities_links = stub_bel
    ui.summarize = lambda df: "en"
    ui.summarize_de = lambda df: "de"

    up = FakeUpload("mini.txt", b"Testvertrag Berlin.")
    ui.run_local_pipeline(up)

    assert "args" in calls, "build_entities_links was not called"
    assert isinstance(calls["args"][2], str), "full_text was not passed as a string"
