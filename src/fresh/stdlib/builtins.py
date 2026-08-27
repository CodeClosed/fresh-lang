"""Built-in native functions for the Fresh standard library."""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

from fresh.common.errors import FreshRuntimeError
from fresh.vm.objects import ObjArray, ObjNativeFunction, ObjStructInstance
from fresh.vm.value import value_to_string

if TYPE_CHECKING:
    from fresh.vm.vm import VM


def register_builtins(vm: VM) -> None:
    """Register core built-in native functions into the VM globals."""

    def _native_print(*args: Any) -> None:
        out = " ".join(value_to_string(a) for a in args)
        print(out, end="")
        return None

    def _native_println(*args: Any) -> None:
        out = " ".join(value_to_string(a) for a in args)
        print(out)
        return None

    def _native_input(*args: Any) -> str:
        prompt = value_to_string(args[0]) if args else ""
        return input(prompt)

    def _native_read_int() -> int:
        raw = input()
        try:
            return int(raw.strip())
        except ValueError:
            raise FreshRuntimeError(f"read_int() expected integer, got '{raw}'")

    def _native_len(obj: Any) -> int:
        if isinstance(obj, ObjArray):
            return len(obj.elements)
        if isinstance(obj, str):
            return len(obj)
        raise FreshRuntimeError(f"len() not supported for type '{type(obj).__name__}'")

    def _native_push(arr: Any, item: Any) -> None:
        if isinstance(arr, ObjArray):
            arr.elements.append(item)
            return None
        raise FreshRuntimeError(f"push() requires array, got '{type(arr).__name__}'")

    def _native_pop(arr: Any) -> Any:
        if isinstance(arr, ObjArray):
            if not arr.elements:
                raise FreshRuntimeError("Cannot pop() from empty array")
            return arr.elements.pop()
        raise FreshRuntimeError(f"pop() requires array, got '{type(arr).__name__}'")

    def _native_clock() -> float:
        return time.time()

    def _native_type(val: Any) -> str:
        if val is None:
            return "nil"
        if isinstance(val, bool):
            return "bool"
        if isinstance(val, int):
            return "int"
        if isinstance(val, float):
            return "float"
        if isinstance(val, str):
            return "string"
        if isinstance(val, ObjArray):
            return "array"
        if isinstance(val, ObjStructInstance):
            return val.struct_def.name
        return type(val).__name__

    def _native_to_string(val: Any) -> str:
        return value_to_string(val)

    def _native_to_int(val: Any) -> int:
        try:
            return int(val)
        except (ValueError, TypeError) as e:
            raise FreshRuntimeError(f"to_int() failed on value '{val}': {e}")

    def _native_to_float(val: Any) -> float:
        try:
            return float(val)
        except (ValueError, TypeError) as e:
            raise FreshRuntimeError(f"to_float() failed on value '{val}': {e}")

    def _native_read_file(path_str: Any) -> str:
        p = str(path_str)
        try:
            return Path(p).read_text(encoding="utf-8")
        except Exception as e:
            raise FreshRuntimeError(f"read_file('{p}') failed: {e}")

    def _native_write_file(path_str: Any, content: Any) -> bool:
        p = str(path_str)
        try:
            Path(p).write_text(str(content), encoding="utf-8")
            return True
        except Exception as e:
            raise FreshRuntimeError(f"write_file('{p}') failed: {e}")

    def _native_file_exists(path_str: Any) -> bool:
        return Path(str(path_str)).exists()

    natives = [
        ("print", -1, _native_print),
        ("println", -1, _native_println),
        ("input", -1, _native_input),
        ("read_int", 0, _native_read_int),
        ("len", 1, _native_len),
        ("push", 2, _native_push),
        ("pop", 1, _native_pop),
        ("clock", 0, _native_clock),
        ("type", 1, _native_type),
        ("to_string", 1, _native_to_string),
        ("to_int", 1, _native_to_int),
        ("to_float", 1, _native_to_float),
        ("read_file", 1, _native_read_file),
        ("write_file", 2, _native_write_file),
        ("file_exists", 1, _native_file_exists),
    ]

    for name, arity, fn in natives:
        native_obj = ObjNativeFunction(name, arity, fn)
        vm.gc.allocate(native_obj)
        vm.globals[name] = native_obj
