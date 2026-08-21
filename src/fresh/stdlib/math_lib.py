"""Math functions for the Fresh standard library."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

from fresh.vm.objects import ObjNativeFunction

if TYPE_CHECKING:
    from fresh.vm.vm import VM


def register_math_lib(vm: VM) -> None:
    """Register math native functions into the VM globals."""

    natives = [
        ("abs", 1, lambda x: abs(x)),
        ("sqrt", 1, lambda x: math.sqrt(x)),
        ("pow", 2, lambda x, y: math.pow(x, y)),
        ("min", 2, lambda x, y: min(x, y)),
        ("max", 2, lambda x, y: max(x, y)),
        ("floor", 1, lambda x: math.floor(x)),
        ("ceil", 1, lambda x: math.ceil(x)),
        ("round", 1, lambda x: round(x)),
    ]

    for name, arity, fn in natives:
        native_obj = ObjNativeFunction(name, arity, fn)
        vm.gc.allocate(native_obj)
        vm.globals[name] = native_obj
