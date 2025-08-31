from . import reader as reader

# --- Robust attribute binding for submodules on package object ---
# Ensures `pipeline.reader` (and peers) exists as attributes for monkeypatch targets.
import importlib as _il, sys as _sys

def _bind_attr(_name: str):
    try:
        # Try relative import first
        _mod = _il.import_module(__name__ + "." + _name)
        setattr(_sys.modules[__name__], _name, _mod)
    except Exception:
        pass

for _n in ("reader", "normalize", "summarize", "postprocess", "export"):
    if not hasattr(_sys.modules[__name__], _n):
        _bind_attr(_n)


from . import reader


import importlib as _il
import sys as _sys

# Ensure submodules are exposed as attributes on the package (reader already handled)
for _mod in ("reader", "normalize", "summarize", "postprocess", "export"):
    try:
        _m = _il.import_module(__name__ + "." + _mod)
        setattr(_sys.modules[__name__], _mod, _m)
    except Exception:
        # Do not crash on optional modules
        pass
