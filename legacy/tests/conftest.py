
# -*- coding: utf-8 -*-
# Ensure project root is importable and expose pipeline submodules as attributes for monkeypatch

import os as _os, sys as _sys, importlib as _il

# Put project root (parent of tests) at the front of sys.path
_here = _os.path.dirname(__file__)
_root = _os.path.abspath(_os.path.join(_here, _os.pardir))
if _root not in _sys.path:
    _sys.path.insert(0, _root)

# Eagerly bind submodules as attributes on `pipeline` package
try:
    _pkg = _il.import_module('pipeline')
    for _modname in ('reader', 'normalize', 'summarize', 'postprocess', 'export'):
        try:
            _mod = _il.import_module(f'pipeline.{_modname}')
            if not hasattr(_pkg, _modname):
                setattr(_pkg, _modname, _mod)
        except Exception:
            pass
except Exception:
    pass
