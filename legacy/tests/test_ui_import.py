def test_import_ui():
    import importlib
    mod = importlib.import_module("app.ui_streamlit")
    assert hasattr(mod, "run_local_pipeline")
    assert hasattr(mod, "_safe_run_pipeline")