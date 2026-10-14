"""Type representations for the Fresh language type system.

Each Fresh type is represented by a Python class. Types support
equality comparison and human-readable string formatting.
"""

from __future__ import annotations

from dataclasses import dataclass, field


class FreshType:
    """Base class for all Fresh types."""

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FreshAny) or isinstance(self, FreshAny):
            return True
        return type(self) is type(other)

    def __hash__(self) -> int:
        return hash(type(self).__name__)

    def __repr__(self) -> str:
        return type(self).__name__


class FreshInt(FreshType):
    """The `int` type: 64-bit signed integer."""

    def __repr__(self) -> str:
        return "int"


class FreshFloat(FreshType):
    """The `float` type: 64-bit IEEE 754 double."""

    def __repr__(self) -> str:
        return "float"


class FreshBool(FreshType):
    """The `bool` type: true or false."""

    def __repr__(self) -> str:
        return "bool"


class FreshString(FreshType):
    """The `string` type: UTF-8 text."""

    def __repr__(self) -> str:
        return "string"


class FreshNil(FreshType):
    """The `nil` type: absence of a value."""

    def __repr__(self) -> str:
        return "nil"


@dataclass
class FreshArray(FreshType):
    """Array type: [element_type]."""

    element_type: FreshType

    def __repr__(self) -> str:
        return f"[{self.element_type!r}]"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FreshAny):
            return True
        return isinstance(other, FreshArray) and self.element_type == other.element_type

    def __hash__(self) -> int:
        return hash(("array", self.element_type))


@dataclass
class FreshFunction(FreshType):
    """Function type: fn(param_types) -> return_type."""

    param_types: list[FreshType] | None = None
    return_type: FreshType | None = None

    def __repr__(self) -> str:
        if self.param_types is None:
            return "fn"
        params = ", ".join(repr(t) for t in self.param_types)
        ret = f" -> {self.return_type!r}" if self.return_type else ""
        return f"fn({params}){ret}"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FreshAny):
            return True
        if not isinstance(other, FreshFunction):
            return False
        param_match = (
            self.param_types is None
            or other.param_types is None
            or self.param_types == other.param_types
        )
        return_match = (
            self.return_type is None
            or other.return_type is None
            or self.return_type == other.return_type
        )
        return param_match and return_match

    def __hash__(self) -> int:
        params_tuple = tuple(self.param_types) if self.param_types is not None else None
        return hash(("fn", params_tuple, self.return_type))



@dataclass
class FreshStruct(FreshType):
    """User-defined struct type."""

    name: str = ""
    fields: dict[str, FreshType] = field(default_factory=dict)

    def __repr__(self) -> str:
        return self.name

    def __eq__(self, other: object) -> bool:
        if isinstance(other, FreshAny):
            return True
        return isinstance(other, FreshStruct) and self.name == other.name

    def __hash__(self) -> int:
        return hash(("struct", self.name))


class FreshAny(FreshType):
    """Wildcard type that matches anything. Used during inference."""

    def __repr__(self) -> str:
        return "any"

    def __eq__(self, other: object) -> bool:
        return isinstance(other, FreshType)

    def __hash__(self) -> int:
        return hash("any")


