import importlib, types
import pandas as pd
from tests.helpers import FakeUpload

def test_integrity_no_orphan_links(monkeypatch):
    import sys, types
    ui = importlib.import_module('app.ui_streamlit')
    ui.REGISTRY['extractors'] = []
    ui.summarize = lambda df: 'summary en'
    ui.summarize_de = lambda df: 'Zusammenfassung de'
    dummy_pipeline = types.ModuleType('pipeline')
    dummy_post = types.ModuleType('pipeline.postprocess')
    def _bps(df):
        import pandas as pd
        return pd.DataFrame([{'item':'base','price':'0'}])
    dummy_post.build_price_schedule = _bps
    sys.modules['pipeline'] = dummy_pipeline
    sys.modules['pipeline.postprocess'] = dummy_post

    ui = importlib.import_module("app.ui_streamlit")

    # Safe stubs as in previous test
    def _stub_entities_links(df_spans, doc_id, full_text):
        ents = pd.DataFrame([
            {"entity_id": "E1", "name": "A", "type": "party"},
            {"entity_id": "E2", "name": "B", "type": "party"},
        ])
        links = pd.DataFrame([
            {"from_id": "E1", "to_id": "E2", "type": "relates_to"}
        ])
        return ents, links

    def _stub_price_from_tables(tables):
        return pd.DataFrame([{"item": "base", "price": "0"}])

    import sys, types
    dummy_rules = types.ModuleType("rules")
    dummy_engine = types.ModuleType("rules.engine")
    dummy_engine.evaluate_compliance = lambda frames, policies: pd.DataFrame([])
    sys.modules["rules"] = dummy_rules
    sys.modules["rules.engine"] = dummy_engine

    ui.build_entities_links = _stub_entities_links
    ui.build_price_schedule_from_tables = _stub_price_from_tables

    # Run
    up = FakeUpload("mini.txt", b"Gerichtsstand Berlin. deutsches Recht.")
    _, spans, comp, ents, links, _, _ = ui.run_local_pipeline(up)

    # Integrity: every link endpoint exists in ents
    ent_ids = set(ents["entity_id"]) if not ents.empty else set()
    orphans = []
    for _, row in links.iterrows():
        if row["from_id"] not in ent_ids or row["to_id"] not in ent_ids:
            orphans.append((row["from_id"], row["to_id"]))
    assert not orphans, f"Orphan links found: {orphans}"