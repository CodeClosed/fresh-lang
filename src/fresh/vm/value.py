"""Runtime value representation for the Fresh Virtual Machine.

Fresh values map to Python types:
  - int      -> Fresh int
  - float    -> Fresh float
  - bool     -> Fresh bool
  - str      -> Fresh string
  - None     -> Fresh nil
  - Obj      -> Heap-allocated objects (ObjClosure, ObjStructInstance, etc.)
"""

from __future__ import annotations

from typing import Any, Union

Value = Union[int, float, bool, str, None, Any]


def value_to_string(value: Value) -> str:
    """Format a Fresh runtime value as a user-visible string."""
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        if value.is_integer():
            return f"{int(value)}.0"
        return str(value)
    return str(value)


def is_falsey(value: Value) -> bool:
    """Evaluate truthiness according to Fresh semantics (nil and false are falsey)."""
    if value is None or value is False:
        return True
    return False
