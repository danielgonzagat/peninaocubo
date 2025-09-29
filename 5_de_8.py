import os as _os
import importlib.machinery as _machinery
import importlib.util as _util

_base = _os.path.join(_os.path.dirname(__file__), "5_de_8")
if _os.path.isdir(_base):
    _candidate = _os.path.join(_base, "__init__.py")
    _path = _candidate if _os.path.isfile(_candidate) else _base
else:
    _path = _base

_loader = _machinery.SourceFileLoader(__name__, _path)
_spec = _util.spec_from_loader(__name__, _loader)
_mod = _util.module_from_spec(_spec)
_loader.exec_module(_mod)
globals().update({k: v for k, v in _mod.__dict__.items() if k not in globals()})
