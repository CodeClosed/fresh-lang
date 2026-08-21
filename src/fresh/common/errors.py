"""Fresh compiler error hierarchy with rich source-code diagnostics.

All Fresh errors carry source location information and can render
human-friendly error messages with source-code underlines, e.g.:

    error[FreshSyntaxError]: Unterminated string literal
     --> test.fresh:3:12
      |
    3 | let msg = "hello
      |            ^^^^^
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fresh.common.span import Span


@dataclass(slots=True)
class FreshError(Exception):
    """Base class for all Fresh compiler and runtime errors."""

    message: str
    line: int = 0
    column: int = 0
    source_line: str = ""
    filename: str = "<unknown>"

    def __str__(self) -> str:
        header = f"error[{type(self).__name__}]: {self.message}"
        if self.line == 0:
            return header

        location = f" --> {self.filename}:{self.line}:{self.column}"
        gutter_width = len(str(self.line))
        empty_gutter = " " * gutter_width
        separator = f"{empty_gutter} |"
        source = f"{self.line} | {self.source_line}"

        # Build underline caret
        caret_padding = " " * (gutter_width + 3 + max(0, self.column - 1))
        caret = caret_padding + "^"

        return f"{header}\n{location}\n{separator}\n{source}\n{caret}"

    @classmethod
    def from_span(
        cls,
        message: str,
        span: "Span",
        source_line: str = "",
        filename: str = "<unknown>",
    ) -> "FreshError":
        """Construct an error from a Span object."""
        return cls(
            message=message,
            line=span.line,
            column=span.column,
            source_line=source_line,
            filename=filename,
        )


class FreshSyntaxError(FreshError):
    """Raised during lexical or syntactic analysis.

    Examples: unterminated strings, unexpected characters,
    missing semicolons, malformed expressions.
    """
    pass


class FreshTypeError(FreshError):
    """Raised during semantic analysis / type checking.

    Examples: type mismatches in binary operations,
    wrong number of function arguments, invalid field access.
    """
    pass


class FreshRuntimeError(FreshError):
    """Raised during VM execution.

    Examples: division by zero, stack overflow,
    index out of bounds, undefined variable access.
    """
    pass


class FreshNameError(FreshError):
    """Raised when a name cannot be resolved.

    Examples: undefined variables, duplicate declarations
    in the same scope.
    """
    pass


class FreshCodegenError(FreshError):
    """Raised during code generation when code generator / transpiler encounters unsupported nodes.

    Examples: unsupported AST expressions/statements in C transpiler [E3001].
    """
    pass


# Backward compatibility aliases
VexError = FreshError
VexSyntaxError = FreshSyntaxError
VexTypeError = FreshTypeError
VexRuntimeError = FreshRuntimeError
VexNameError = FreshNameError
VexCodegenError = FreshCodegenError

