"""Token types and Token data structure for the Fresh lexer.

TokenType is an IntEnum for fast comparison in the parser's
Pratt precedence table and match/case dispatch.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, auto

from fresh.common.span import Span


class TokenType(IntEnum):
    """Every distinct token kind recognised by the Fresh lexer."""

    # ── Literals ──────────────────────────────────────────────
    INT_LIT = auto()        # 42
    FLOAT_LIT = auto()      # 3.14
    STRING_LIT = auto()     # "hello"
    TRUE = auto()           # true
    FALSE = auto()          # false

    # ── Identifiers ───────────────────────────────────────────
    IDENTIFIER = auto()     # foo, bar, my_var

    # ── Single-character tokens ───────────────────────────────
    LEFT_PAREN = auto()     # (
    RIGHT_PAREN = auto()    # )
    LEFT_BRACE = auto()     # {
    RIGHT_BRACE = auto()    # }
    LEFT_BRACKET = auto()   # [
    RIGHT_BRACKET = auto()  # ]
    COMMA = auto()          # ,
    DOT = auto()            # .
    SEMICOLON = auto()      # ;
    COLON = auto()          # :
    PLUS = auto()           # +
    MINUS = auto()          # -
    STAR = auto()           # *
    SLASH = auto()          # /
    PERCENT = auto()        # %
    BANG = auto()           # !
    EQUAL = auto()          # =
    LESS = auto()           # <
    GREATER = auto()        # >

    # ── Two-character tokens ──────────────────────────────────
    EQUAL_EQUAL = auto()    # ==
    BANG_EQUAL = auto()     # !=
    LESS_EQUAL = auto()     # <=
    GREATER_EQUAL = auto()  # >=
    ARROW = auto()          # ->
    FAT_ARROW = auto()      # =>
    AMP_AMP = auto()        # &&
    PIPE_PIPE = auto()      # ||

    # ── Keywords ──────────────────────────────────────────────
    LET = auto()            # let
    FN = auto()             # fn
    RETURN = auto()         # return
    IF = auto()             # if
    ELSE = auto()           # else
    WHILE = auto()          # while
    FOR = auto()            # for
    BREAK = auto()          # break
    CONTINUE = auto()       # continue
    STRUCT = auto()         # struct
    MATCH = auto()          # match
    NIL = auto()            # nil
    IMPORT = auto()         # import

    # ── Type keywords ─────────────────────────────────────────
    INT_TYPE = auto()       # int
    FLOAT_TYPE = auto()     # float
    BOOL_TYPE = auto()      # bool
    STRING_TYPE = auto()    # string

    # ── Special ───────────────────────────────────────────────
    UNDERSCORE = auto()     # _ (wildcard in patterns)
    EOF = auto()            # End of file


# ── Keyword lookup table ──────────────────────────────────────
KEYWORDS: dict[str, TokenType] = {
    "let":      TokenType.LET,
    "fn":       TokenType.FN,
    "return":   TokenType.RETURN,
    "if":       TokenType.IF,
    "else":     TokenType.ELSE,
    "while":    TokenType.WHILE,
    "for":      TokenType.FOR,
    "break":    TokenType.BREAK,
    "continue": TokenType.CONTINUE,
    "struct":   TokenType.STRUCT,
    "match":    TokenType.MATCH,
    "import":   TokenType.IMPORT,
    "true":     TokenType.TRUE,
    "false":    TokenType.FALSE,
    "nil":      TokenType.NIL,
    "int":      TokenType.INT_TYPE,
    "float":    TokenType.FLOAT_TYPE,
    "bool":     TokenType.BOOL_TYPE,
    "string":   TokenType.STRING_TYPE,
}



@dataclass(slots=True)
class Token:
    """A single lexical token produced by the scanner.

    Attributes:
        type:   The kind of token (operator, keyword, literal, etc.).
        lexeme: The raw source text that was matched.
        line:   1-based line number where the token starts.
        column: 1-based column number where the token starts.
        value:  Parsed literal value for INT_LIT, FLOAT_LIT, STRING_LIT.
                None for non-literal tokens.
    """

    type: TokenType
    lexeme: str
    line: int
    column: int
    value: object = None

    @property
    def span(self) -> Span:
        """Create a Span from this token's position."""
        return Span(line=self.line, column=self.column, length=len(self.lexeme))

    def __repr__(self) -> str:
        if self.value is not None:
            return f"Token({self.type.name}, {self.lexeme!r}, value={self.value!r})"
        return f"Token({self.type.name}, {self.lexeme!r})"
