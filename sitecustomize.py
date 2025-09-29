import sys
import os
import types


def _load_script_as_module(module_name: str, file_path: str) -> None:
    if module_name in sys.modules:
        return
    if not os.path.isfile(file_path):
        return
    module = types.ModuleType(module_name)
    module.__file__ = file_path
    module.__package__ = ""
    code = None
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        source = f.read()
        code = compile(source, file_path, "exec")
    sys.modules[module_name] = module
    exec(code, module.__dict__)


_CANDIDATES = ["1_de_8", "2_de_8", "3_de_8", "4_de_8", "5_de_8", "6_de_8", "7_de_8", "8_de_8"]
_ROOT = os.path.abspath(os.getcwd())

for name in _CANDIDATES:
    path = os.path.join(_ROOT, name)
    _load_script_as_module(name, path)

