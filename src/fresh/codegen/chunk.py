"""Chunk / CodeObject data structure holding bytecode, constants, and debug metadata."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Chunk:
    """A contiguous block of compiled bytecode instructions.

    Attributes:
        code:      Sequence of byte values (opcodes and operands).
        constants: Constant pool for numbers, strings, function code, etc.
        lines:     Line numbers matching each byte index in `code`.
    """

    code: list[int] = field(default_factory=list)
    constants: list[Any] = field(default_factory=list)
    lines: list[int] = field(default_factory=list)

    def write(self, byte: int, line: int) -> int:
        """Write a byte to the chunk and record its line number.

        Returns:
            The byte offset where the byte was written.
        """
        self.code.append(byte & 0xFF)
        self.lines.append(line)
        return len(self.code) - 1

    def add_constant(self, value: Any) -> int:
        """Add a value to the constant pool.

        Returns:
            The index of the constant in `constants`.
        """
        try:
            for idx, const in enumerate(self.constants):
                if const == value and type(const) is type(value):
                    return idx
        except Exception:
            pass

        self.constants.append(value)
        return len(self.constants) - 1

    def count(self) -> int:
        """Return the number of instruction bytes in this chunk."""
        return len(self.code)
