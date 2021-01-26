#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import glob
import importlib
import re
import os.path as osp
from mathics.settings import ENABLE_FILES_MODULE

# Get a list of file in this directory. We'll exclude from the start
# files with leading characters we don't want like __init__ with its leading underscore.
__py_files__ = [
    osp.basename(f[0:-3])
    for f in glob.glob(osp.join(osp.dirname(__file__), "[a-z]*.py"))
]

exclude_files = set(
    ("files", "codetables", "base", "importexport", "constants", "colors")
)
module_names = [
    f for f in __py_files__ if re.match("^[a-z0-9]+$", f) if f not in exclude_files
]

if ENABLE_FILES_MODULE:
    module_names += ["files", "importexport"]

modules = []

for module_name in module_names:
    try:
        module = importlib.import_module("mathics.builtin." + module_name)
    except:
        # print("XXX", module_name)
        continue
    modules.append(module)

from mathics.builtin.base import (
    Builtin,
    SympyObject,
    BoxConstruct,
    Operator,
    PatternObject,
)

builtins = []
builtins_by_module = {}


def is_builtin(var):
    if var == Builtin:
        return True
    if hasattr(var, "__bases__"):
        return any(is_builtin(base) for base in var.__bases__)
    return False


for module in modules:
    builtins_by_module[module.__name__] = []
    vars = dir(module)
    for name in vars:
        var = getattr(module, name)
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
                builtins.append((instance.get_name(), instance))
                builtins_by_module[module.__name__].append(instance)


# builtins = dict(builtins)

mathics_to_sympy = {}  # here we have: name -> sympy object
mathics_to_python = {}  # here we have: name -> string
sympy_to_mathics = {}

box_constructs = {}
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
        if isinstance(builtin, BoxConstruct):
            box_constructs[name] = builtin
        if isinstance(builtin, Operator):
            builtins_precedence[name] = builtin.precedence
        if isinstance(builtin, PatternObject):
            pattern_objects[name] = builtin.__class__
    builtins.update(dict(new_builtins))


new_builtins = builtins
builtins = {}
add_builtins(new_builtins)


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
    # let MakeBoxes contribute first
    builtins["System`MakeBoxes"].contribute(definitions)
    for name, item in builtins.items():
        if name != "System`MakeBoxes":
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
