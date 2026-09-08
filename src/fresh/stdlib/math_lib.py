"""Math functions for the Fresh standard library."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

from fresh.common.errors import FreshRuntimeError
from fresh.vm.objects import ObjNativeFunction

if TYPE_CHECKING:
    from fresh.vm.vm import VM


def _safe_math(name: str, fn: Any, *args: Any) -> Any:
    try:
        return fn(*args)
    except (ValueError, TypeError, OverflowError) as e:
        raise FreshRuntimeError(f"math.{name}() failed on args {args}: {e}")


def register_math_lib(vm: VM) -> None:
    """Register math native functions into the VM globals."""

    natives = [
        ("abs", 1, lambda x: _safe_math("abs", abs, x)),
        ("sqrt", 1, lambda x: _safe_math("sqrt", math.sqrt, x)),
        ("pow", 2, lambda x, y: _safe_math("pow", math.pow, x, y)),
        ("min", 2, lambda x, y: _safe_math("min", min, x, y)),
        ("max", 2, lambda x, y: _safe_math("max", max, x, y)),
        ("floor", 1, lambda x: _safe_math("floor", math.floor, x)),
        ("ceil", 1, lambda x: _safe_math("ceil", math.ceil, x)),
        ("round", 1, lambda x: _safe_math("round", round, x)),
    ]

    for name, arity, fn in natives:
        native_obj = ObjNativeFunction(name, arity, fn)
        vm.gc.allocate(native_obj)
        vm.globals[name] = native_obj
