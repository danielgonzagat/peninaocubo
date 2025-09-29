import os as _os
import importlib.machinery as _machinery
import importlib.util as _util

_path = _os.path.join(_os.path.dirname(__file__), "1_de_8")
_loader = _machinery.SourceFileLoader(__name__, _path)
_spec = _util.spec_from_loader(__name__, _loader)
_mod = _util.module_from_spec(_spec)
_loader.exec_module(_mod)
globals().update({k: v for k, v in _mod.__dict__.items() if k not in globals()})

