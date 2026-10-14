"""Symbol table for the Fresh semantic analyzer.

Provides Scope and Symbol types used by the resolver and
type checker to track declared variables and their metadata.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fresh.common.types import FreshType


@dataclass(slots=True)
class Symbol:
    """A declared symbol (variable, function, struct, or parameter).

    Attributes:
        name:        The identifier string.
        type:        The resolved Fresh type (None if not yet inferred).
        is_mutable:  Whether the symbol can be reassigned.
        scope_depth: Nesting depth of the scope where declared.
        slot:        Local stack-slot index (-1 for globals).
        is_defined:  True once the initializer has been fully compiled.
    """

    name: str
    type: FreshType | None = None
    is_mutable: bool = True
    scope_depth: int = 0
    slot: int = -1
    is_defined: bool = False


class Scope:
    """A lexical scope containing symbol definitions.

    Scopes form a linked list via their *parent* pointer, enabling
    recursive lookup through the scope chain.
    """

    def __init__(self, depth: int = 0, parent: Scope | None = None) -> None:
        self.depth = depth
        self.parent = parent
        self.symbols: dict[str, Symbol] = {}

    def define(self, name: str, symbol: Symbol) -> None:
        """Define a symbol in this scope."""
        symbol.scope_depth = self.depth
        self.symbols[name] = symbol

    def lookup(self, name: str) -> Symbol | None:
        """Look up a symbol in *this* scope only."""
        return self.symbols.get(name)

    def lookup_chain(self, name: str) -> Symbol | None:
        """Look up a symbol, searching parent scopes if not found locally."""
        sym = self.symbols.get(name)
        if sym is not None:
            return sym
        if self.parent is not None:
            return self.parent.lookup_chain(name)
        return None

    def contains(self, name: str) -> bool:
        """Check whether *name* is declared in this scope."""
        return name in self.symbols
