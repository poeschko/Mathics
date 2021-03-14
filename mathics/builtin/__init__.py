# -*- coding: utf-8 -*-

import glob
import importlib
import re
import os.path as osp
from mathics.settings import ENABLE_FILES_MODULE
from mathics.version import __version__  # noqa used in loading to check consistency.



import importlib
from contextlib import contextmanager
from demandimport import _demandmod as lazy_module

# Get a list of file in this directory. We'll exclude from the start
# files with leading characters we don't want like __init__ with its leading underscore.
__py_files__ = [
    osp.basename(f[0:-3])
    for f in glob.glob(osp.join(osp.dirname(__file__), "[a-z]*.py"))
]

from mathics.builtin.base import (
    Builtin,
    SympyObject,
    BoxConstruct,
    Operator,
    PatternObject,
)

exclude_files = set(("files", "codetables", "base", "importexport", "colors"))
module_names = [
    f for f in __py_files__ if re.match("^[a-z0-9]+$", f) if f not in exclude_files
]

from mathics.settings import ENABLE_FILES_MODULE, BENCHMARK_STARTUP

if ENABLE_FILES_MODULE:
    module_names += ["files", "importexport"]

modules = []

for module_name in module_names:
    try:
        module = importlib.import_module("mathics.builtin." + module_name)
    except Exception as e:
        print(e)
        print(f"    Not able to load {module_name}. Check your installation.")
        print(f"    mathics.builtin loads from {__file__[:-11]}")
        continue

    if __version__ != module.__version__:
        print(
            f"Version {module.__version__} in the module do not match with {__version__}"
        )

    modules.append(module)

_builtins = []
builtins_by_module = {}

if BENCHMARK_STARTUP:
    class Loader:
        def __init__(self, section):
            self._benchmarks = []
            self._section = section

        def __enter__(self):
            @contextmanager
            def load(name):
                from time import time
                t0 = time()
                yield
                t1 = time()
                self._benchmarks.append((name, t1 - t0))
            return load

        def __exit__(self, type, value, tb):
            duration = sum(map(lambda rec: rec[1], self._benchmarks))
            print('%s took %.1f s:' % (self._section, duration))
            self._benchmarks.sort(key=lambda rec: rec[1], reverse=True)
            for name, dt in self._benchmarks[:10]:
                print('    %s %f' % (name, dt))
            print('    ...')
            print()
else:
    @contextmanager
    def _load(name):
        yield

    class Loader:
        def __init__(self, section):
            pass

        def __enter__(self):
            return _load

        def __exit__(self, type, value, tb):
            pass


def is_builtin(var):
    if var == Builtin:
        return True
    if hasattr(var, "__bases__"):
        return any(is_builtin(base) for base in var.__bases__)
    return False



def load_module(name):
    module = importlib.import_module("mathics.builtin.%s" % name)
    builtins_by_module[module.__name__] = []
    vars = dir(module)
    for name in vars:
        if name.startswith('_'):
            continue

        var = getattr(module, name)
        if isinstance(var, lazy_module):
            continue

        if (
            hasattr(var, "__module__")
            and var.__module__.startswith("mathics.builtin.")
            and var.__module__ != "mathics.builtin.base"
            and is_builtin(var)
            and not name.startswith("_")
            and var.__module__ == module.__name__
        ):  # nopep8
            instance = var(expression=False)
            if isinstance(instance, Builtin):
                # This set the default context for symbols in mathics.builtins
                if not type(instance).context:
                    type(instance).context = "System`"
                _builtins.append((instance.get_name(), instance))
                builtins_by_module[module.__name__].append(instance)

    return module


def load_modules():
    with Loader('import') as loader:
        for name in module_names:
            with loader(name):
                yield load_module(name)

modules = list(load_modules())

# builtins = dict(builtins)

mathics_to_sympy = {}  # here we have: name -> sympy object
mathics_to_python = {}  # here we have: name -> string
sympy_to_mathics = {}

pattern_objects = {}
builtins_precedence = {}


def add_builtins(new_builtins):
    for var_name, builtin in new_builtins:
        name = builtin.get_name()
        if hasattr(builtin, "python_equivalent"):
            # print("XXX", builtin.python_equivalent)
            mathics_to_python[name] = builtin.python_equivalent

        if isinstance(builtin, SympyObject):
            mathics_to_sympy[name] = builtin
            for sympy_name in builtin.get_sympy_names():
                sympy_to_mathics[sympy_name] = builtin
        if isinstance(builtin, Operator):
            builtins_precedence[name] = builtin.precedence
        if isinstance(builtin, PatternObject):
            pattern_objects[name] = builtin.__class__
    _builtins.update(dict(new_builtins))


new_builtins = _builtins
_builtins = {}
add_builtins(new_builtins)


def builtins_dict():
    return {
        builtin.get_name(): builtin
        for modname, builtins in builtins_by_module.items()
        for builtin in builtins
    }


def get_module_doc(module):
    doc = module.__doc__
    if doc is not None:
        doc = doc.strip()
    if doc:
        title = doc.splitlines()[0]
        text = "\n".join(doc.splitlines()[1:])
    else:
        title = module.__name__
        for prefix in ("mathics.builtin.", "mathics.optional."):
            if title.startswith(prefix):
                title = title[len(prefix) :]
        title = title.capitalize()
        text = ""
    return title, text


def contribute(definitions):
    with Loader('contribute') as loader:
        # let MakeBoxes contribute first
        _builtins['System`MakeBoxes'].contribute(definitions)
        for name, item in _builtins.items():
            if name != 'System`MakeBoxes':
                with loader(name):
                    item.contribute(definitions)

    from mathics.core.expression import ensure_context
    from mathics.core.parser import all_operator_names
    from mathics.core.definitions import Definition

    # All builtins are loaded. Create dummy builtin definitions for
    # any remaining operators that don't have them. This allows
    # operators like \[Cup] to behave correctly.
    for operator in all_operator_names:
        if not definitions.have_definition(ensure_context(operator)):
            op = ensure_context(operator)
            definitions.builtin[op] = Definition(name=op)
