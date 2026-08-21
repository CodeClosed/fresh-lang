"""Source location tracking for precise error diagnostics.

Every token and AST node carries a Span indicating exactly where it
appears in the original source code. This enables rich error messages
with source-code underlines.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class Span:
    """Represents a contiguous region in a source file.

    Attributes:
        line:   1-based line number.
        column: 1-based column number (byte offset within the line).
        length: Number of characters this span covers.
    """

    line: int
    column: int
    length: int = 1

    def __str__(self) -> str:
        return f"line {self.line}, col {self.column}"


@dataclass(slots=True)
class SourceFile:
    """Holds the entire source text alongside its filename for error reporting."""

    filename: str
    source: str

    def get_line_text(self, line_number: int) -> str:
        """Return the text of a specific 1-based line number."""
        lines = self.source.splitlines()
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1]
        return ""
