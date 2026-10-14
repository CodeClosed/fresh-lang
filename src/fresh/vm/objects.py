"""Heap object definitions for the Fresh Virtual Machine.

All heap-allocated objects inherit from `Obj` and implement `trace_references()`
to participate in mark-and-sweep garbage collection.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fresh.codegen.chunk import Chunk


class Obj:
    """Base class for all heap-allocated objects in Fresh."""

    def __init__(self) -> None:
        self.is_marked: bool = False

    def trace_references(self, worklist: list[Obj]) -> None:
        """Override in subclasses to push referenced heap objects to GC worklist."""
        pass


class ObjFunction(Obj):
    """Compiled function code template."""

    def __init__(self, name: str, arity: int, chunk: Chunk, upvalue_count: int = 0) -> None:
        super().__init__()
        self.name = name
        self.arity = arity
        self.chunk = chunk
        self.upvalue_count = upvalue_count

    def __repr__(self) -> str:
        return f"<fn {self.name}>"


class ObjUpvalue(Obj):
    """Captures a variable from an enclosing stack frame.

    While the frame is active, `location` holds the stack index (Open Upvalue).
    When the frame exits, `location` is set to None and `closed_value` holds the value.
    """

    def __init__(self, location: int) -> None:
        super().__init__()
        self.location: int | None = location
        self.closed_value: Any = None

    def get(self, stack: list[Any]) -> Any:
        if self.location is not None:
            return stack[self.location]
        return self.closed_value

    def set(self, stack: list[Any], value: Any) -> None:
        if self.location is not None:
            stack[self.location] = value
        else:
            self.closed_value = value

    def trace_references(self, worklist: list[Obj]) -> None:
        if self.location is None and isinstance(self.closed_value, Obj):
            if not self.closed_value.is_marked:
                self.closed_value.is_marked = True
                worklist.append(self.closed_value)

    def __repr__(self) -> str:
        if self.location is not None:
            return f"<upvalue open slot={self.location}>"
        return f"<upvalue closed val={self.closed_value}>"


class ObjClosure(Obj):
    """Executable function closure with bound upvalues."""

    def __init__(self, function: ObjFunction) -> None:
        super().__init__()
        self.function = function
        self.upvalues: list[ObjUpvalue] = []

    def trace_references(self, worklist: list[Obj]) -> None:
        if not self.function.is_marked:
            self.function.is_marked = True
            worklist.append(self.function)
        for u in self.upvalues:
            if not u.is_marked:
                u.is_marked = True
                worklist.append(u)

    def __repr__(self) -> str:
        return f"<closure {self.function.name}>"


class ObjStructDef(Obj):
    """Struct layout definition."""

    def __init__(self, name: str, field_names: list[str]) -> None:
        super().__init__()
        self.name = name
        self.field_names = field_names
        self.field_indices: dict[str, int] = {fname: i for i, fname in enumerate(field_names)}

    def __repr__(self) -> str:
        return f"<struct {self.name}>"


class ObjStructInstance(Obj):
    """An instance of a struct."""

    def __init__(self, struct_def: ObjStructDef) -> None:
        super().__init__()
        self.struct_def = struct_def
        self.fields: list[Any] = [None] * len(struct_def.field_names)

    def trace_references(self, worklist: list[Obj]) -> None:
        if not self.struct_def.is_marked:
            self.struct_def.is_marked = True
            worklist.append(self.struct_def)
        for fval in self.fields:
            if isinstance(fval, Obj) and not fval.is_marked:
                fval.is_marked = True
                worklist.append(fval)

    def __repr__(self) -> str:
        fstrs = [f"{name}: {val!r}" for name, val in zip(self.struct_def.field_names, self.fields)]
        return f"{self.struct_def.name} {{ {', '.join(fstrs)} }}"


class ObjArray(Obj):
    """Dynamic array heap object."""

    def __init__(self, elements: list[Any]) -> None:
        super().__init__()
        self.elements: list[Any] = elements

    def trace_references(self, worklist: list[Obj]) -> None:
        for elem in self.elements:
            if isinstance(elem, Obj) and not elem.is_marked:
                elem.is_marked = True
                worklist.append(elem)

    def __repr__(self) -> str:
        return f"[{', '.join(str(e) for e in self.elements)}]"


class ObjNativeFunction(Obj):
    """Native Python function bound into Fresh stdlib."""

    def __init__(self, name: str, arity: int, function: Any) -> None:
        super().__init__()
        self.name = name
        self.arity = arity
        self.function = function

    def __repr__(self) -> str:
        return f"<native fn {self.name}>"
