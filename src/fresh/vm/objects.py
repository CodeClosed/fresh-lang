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


class ObjClass(Obj):
    """Runtime class definition with fields, methods, and optional parent."""

    def __init__(self, name: str, field_names: list[str], parent: ObjClass | None = None) -> None:
        super().__init__()
        self.name = name
        self.field_names: list[str] = list(field_names)
        self.field_indices: dict[str, int] = {fname: i for i, fname in enumerate(field_names)}
        self.methods: dict[str, ObjClosure] = {}
        self.parent: ObjClass | None = parent

    def lookup_method(self, method_name: str) -> ObjClosure | None:
        if method_name in self.methods:
            return self.methods[method_name]
        if method_name in ("init", "constructor"):
            if "init" in self.methods:
                return self.methods["init"]
            if "constructor" in self.methods:
                return self.methods["constructor"]
        if self.parent is not None:
            return self.parent.lookup_method(method_name)
        return None

    def inherit_from(self, parent: ObjClass) -> None:
        self.parent = parent
        # Inherit fields: parent fields come first
        all_fields = list(parent.field_names)
        for fname in self.field_names:
            if fname not in parent.field_indices:
                all_fields.append(fname)
        self.field_names = all_fields
        self.field_indices = {fname: i for i, fname in enumerate(all_fields)}
        # Inherit methods (child methods override parent methods)
        inherited_methods = dict(parent.methods)
        inherited_methods.update(self.methods)
        self.methods = inherited_methods

    def trace_references(self, worklist: list[Obj]) -> None:
        if self.parent is not None and not self.parent.is_marked:
            self.parent.is_marked = True
            worklist.append(self.parent)
        for method in self.methods.values():
            if not method.is_marked:
                method.is_marked = True
                worklist.append(method)

    def __repr__(self) -> str:
        return f"<class {self.name}>"


class ObjInstance(Obj):
    """An instance of a class."""

    def __init__(self, klass: ObjClass) -> None:
        super().__init__()
        self.klass = klass
        self.fields: list[Any] = [None] * len(klass.field_names)

    def get_field(self, name: str) -> Any:
        idx = self.klass.field_indices.get(name)
        if idx is not None and idx < len(self.fields):
            return self.fields[idx]
        return None

    def set_field(self, name: str, value: Any) -> bool:
        idx = self.klass.field_indices.get(name)
        if idx is not None:
            if idx >= len(self.fields):
                self.fields.extend([None] * (idx - len(self.fields) + 1))
            self.fields[idx] = value
            return True
        else:
            self.klass.field_names.append(name)
            idx = len(self.klass.field_names) - 1
            self.klass.field_indices[name] = idx
            self.fields.extend([None] * (idx - len(self.fields) + 1))
            self.fields[idx] = value
            return True

    def trace_references(self, worklist: list[Obj]) -> None:
        if not self.klass.is_marked:
            self.klass.is_marked = True
            worklist.append(self.klass)
        for fval in self.fields:
            if isinstance(fval, Obj) and not fval.is_marked:
                fval.is_marked = True
                worklist.append(fval)

    def __repr__(self) -> str:
        fstrs = [f"{name}: {val!r}" for name, val in zip(self.klass.field_names, self.fields)]
        return f"{self.klass.name} {{ {', '.join(fstrs)} }}"

    def __str__(self) -> str:
        fstrs = [f"{name}: {val}" for name, val in zip(self.klass.field_names, self.fields)]
        return f"{self.klass.name} {{ {', '.join(fstrs)} }}"


class ObjBoundMethod(Obj):
    """A method bound to an instance (receiver)."""

    def __init__(self, receiver: ObjInstance, method: ObjClosure) -> None:
        super().__init__()
        self.receiver = receiver
        self.method = method

    def trace_references(self, worklist: list[Obj]) -> None:
        if not self.receiver.is_marked:
            self.receiver.is_marked = True
            worklist.append(self.receiver)
        if not self.method.is_marked:
            self.method.is_marked = True
            worklist.append(self.method)

    def __repr__(self) -> str:
        return f"<bound method {self.method.function.name}>"
