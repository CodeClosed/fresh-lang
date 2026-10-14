"""Fresh lexical analyzer (scanner).

Converts raw UTF-8 source text into a flat stream of typed tokens.
Handles:
  - Single-line (//) and multi-line (/* */) comments
  - String literals with escape sequences (\n, \t, \\, \", \0)
  - Integer and floating-point number literals
  - All operators, delimiters, and keywords
  - Accurate line and column tracking for error diagnostics

Usage:
    scanner = Scanner(source_code)
    tokens = scanner.scan_tokens()  # returns list[Token]
"""

from __future__ import annotations

from fresh.common.errors import FreshSyntaxError
from fresh.lexer.tokens import KEYWORDS, Token, TokenType


class Scanner:
    """Scans source code and produces a list of tokens.

    The scanner is a single-pass, character-by-character lexer that
    maintains current position, line, and column for precise error
    reporting.
    """

    def __init__(self, source: str, filename: str = "<stdin>") -> None:
        self.source = source
        self.filename = filename
        self.tokens: list[Token] = []

        # Position tracking
        self._start: int = 0       # Start of current lexeme
        self._current: int = 0     # Current character index
        self._line: int = 1        # Current line (1-based)
        self._column: int = 1      # Current column (1-based)
        self._start_line: int = 1  # Line at start of current lexeme
        self._start_col: int = 1   # Column at start of current lexeme

    # ── Public API ────────────────────────────────────────────

    def scan_tokens(self) -> list[Token]:
        """Scan the entire source and return the complete token list.

        The list always ends with an EOF token.
        """
        while not self._is_at_end():
            self._start = self._current
            self._start_line = self._line
            self._start_col = self._column
            self._scan_token()

        self.tokens.append(
            Token(
                type=TokenType.EOF,
                lexeme="",
                line=self._line,
                column=self._column,
            )
        )
        return self.tokens

    # ── Core scanning ─────────────────────────────────────────

    def _scan_token(self) -> None:
        """Scan a single token starting at self._current."""
        c = self._advance()

        match c:
            # Single-character tokens
            case "(":
                self._add_token(TokenType.LEFT_PAREN)
            case ")":
                self._add_token(TokenType.RIGHT_PAREN)
            case "{":
                self._add_token(TokenType.LEFT_BRACE)
            case "}":
                self._add_token(TokenType.RIGHT_BRACE)
            case "[":
                self._add_token(TokenType.LEFT_BRACKET)
            case "]":
                self._add_token(TokenType.RIGHT_BRACKET)
            case ",":
                self._add_token(TokenType.COMMA)
            case ".":
                self._add_token(TokenType.DOT)
            case ";":
                self._add_token(TokenType.SEMICOLON)
            case ":":
                self._add_token(TokenType.COLON)
            case "+":
                self._add_token(TokenType.PLUS)
            case "*":
                self._add_token(TokenType.STAR)
            case "%":
                self._add_token(TokenType.PERCENT)

            # Potentially two-character tokens
            case "-":
                if self._match(">"):
                    self._add_token(TokenType.ARROW)
                else:
                    self._add_token(TokenType.MINUS)
            case "!":
                if self._match("="):
                    self._add_token(TokenType.BANG_EQUAL)
                else:
                    self._add_token(TokenType.BANG)
            case "=":
                if self._match("="):
                    self._add_token(TokenType.EQUAL_EQUAL)
                elif self._match(">"):
                    self._add_token(TokenType.FAT_ARROW)
                else:
                    self._add_token(TokenType.EQUAL)
            case "<":
                if self._match("="):
                    self._add_token(TokenType.LESS_EQUAL)
                else:
                    self._add_token(TokenType.LESS)
            case ">":
                if self._match("="):
                    self._add_token(TokenType.GREATER_EQUAL)
                else:
                    self._add_token(TokenType.GREATER)
            case "&":
                if self._match("&"):
                    self._add_token(TokenType.AMP_AMP)
                else:
                    self._error("Unexpected character '&'. Did you mean '&&'?")
            case "|":
                if self._match("|"):
                    self._add_token(TokenType.PIPE_PIPE)
                else:
                    self._error("Unexpected character '|'. Did you mean '||'?")

            # Slash: division or comment
            case "/":
                if self._match("/"):
                    self._single_line_comment()
                elif self._match("*"):
                    self._multi_line_comment()
                else:
                    self._add_token(TokenType.SLASH)

            # Whitespace
            case " " | "\r" | "\t":
                pass  # Skip whitespace
            case "\n":
                self._newline()

            # String literals
            case '"':
                self._string()

            # Underscore: could be identifier or wildcard
            case "_":
                if self._peek().isalnum() or self._peek() == "_":
                    self._identifier()
                else:
                    self._add_token(TokenType.UNDERSCORE)

            case _:
                if c.isdigit():
                    self._number()
                elif c.isalpha():
                    self._identifier()
                else:
                    self._error(f"Unexpected character '{c}'.")

    # ── Literal scanners ──────────────────────────────────────

    def _string(self) -> None:
        """Scan a string literal with escape sequence support."""
        value_chars: list[str] = []

        while not self._is_at_end() and self._peek() != '"':
            if self._peek() == "\r":
                self._advance()
                if self._peek() == "\n":
                    self._advance()
                    self._newline()
                    value_chars.append("\n")
                else:
                    value_chars.append("\r")
                continue

            if self._peek() == "\n":
                self._advance()
                self._newline()
                value_chars.append("\n")
                continue

            if self._peek() == "\\":
                self._advance()  # consume the backslash
                if self._is_at_end():
                    self._error("Unterminated escape sequence at end of file.")
                    return

                esc = self._advance()
                match esc:
                    case "n":
                        value_chars.append("\n")
                    case "t":
                        value_chars.append("\t")
                    case "\\":
                        value_chars.append("\\")
                    case '"':
                        value_chars.append('"')
                    case "0":
                        value_chars.append("\0")
                    case "r":
                        value_chars.append("\r")
                    case "x":
                        h1 = self._advance() if not self._is_at_end() else ""
                        h2 = self._advance() if not self._is_at_end() else ""
                        hex_str = h1 + h2
                        if len(hex_str) == 2 and all(c in "0123456789abcdefABCDEF" for c in hex_str):
                            value_chars.append(chr(int(hex_str, 16)))
                        else:
                            self._error(f"Invalid hex escape sequence '\\x{hex_str}'.")
                            return
                    case "u":
                        u_chars = [self._advance() for _ in range(4) if not self._is_at_end()]
                        u_str = "".join(u_chars)
                        if len(u_str) == 4 and all(c in "0123456789abcdefABCDEF" for c in u_str):
                            value_chars.append(chr(int(u_str, 16)))
                        else:
                            self._error(f"Invalid unicode escape sequence '\\u{u_str}'.")
                            return
                    case _:
                        self._error(f"Invalid escape sequence '\\{esc}'.")
                        return
            else:
                value_chars.append(self._advance())

        if self._is_at_end():
            self._error("Unterminated string literal.")
            return

        # Consume the closing "
        self._advance()

        string_value = "".join(value_chars)
        self._add_token(TokenType.STRING_LIT, value=string_value)

    def _number(self) -> None:
        """Scan an integer or floating-point number literal."""
        is_float = False

        while not self._is_at_end() and self._peek().isdigit():
            self._advance()

        # Check for fractional part
        if (
            not self._is_at_end()
            and self._peek() == "."
            and self._peek_next().isdigit()
        ):
            is_float = True
            self._advance()  # consume the '.'
            while not self._is_at_end() and self._peek().isdigit():
                self._advance()

        lexeme = self.source[self._start : self._current]

        if is_float:
            self._add_token(TokenType.FLOAT_LIT, value=float(lexeme))
        else:
            self._add_token(TokenType.INT_LIT, value=int(lexeme))

    def _identifier(self) -> None:
        """Scan an identifier or keyword."""
        while not self._is_at_end() and (
            self._peek().isalnum() or self._peek() == "_"
        ):
            self._advance()

        lexeme = self.source[self._start : self._current]
        token_type = KEYWORDS.get(lexeme, TokenType.IDENTIFIER)
        self._add_token(token_type)

    # ── Comment scanners ──────────────────────────────────────

    def _single_line_comment(self) -> None:
        """Skip a // comment until end of line."""
        while not self._is_at_end() and self._peek() != "\n":
            self._advance()

    def _multi_line_comment(self) -> None:
        """Skip a /* */ comment, supporting nesting."""
        depth = 1
        while not self._is_at_end() and depth > 0:
            if self._peek() == "/" and self._peek_next() == "*":
                self._advance()
                self._advance()
                depth += 1
            elif self._peek() == "*" and self._peek_next() == "/":
                self._advance()
                self._advance()
                depth -= 1
            elif self._peek() == "\n":
                self._newline()
                self._current += 1
            else:
                self._advance()

        if depth > 0:
            self._error("Unterminated multi-line comment.")

    # ── Character-level helpers ───────────────────────────────

    def _advance(self) -> str:
        """Consume and return the current character, advancing the cursor."""
        c = self.source[self._current]
        self._current += 1
        self._column += 1
        return c

    def _peek(self) -> str:
        """Return the current character without consuming it."""
        if self._is_at_end():
            return "\0"
        return self.source[self._current]

    def _peek_next(self) -> str:
        """Return the next character (lookahead of 2) without consuming."""
        if self._current + 1 >= len(self.source):
            return "\0"
        return self.source[self._current + 1]

    def _match(self, expected: str) -> bool:
        """Conditionally consume the current character if it matches."""
        if self._is_at_end():
            return False
        if self.source[self._current] != expected:
            return False
        self._current += 1
        self._column += 1
        return True

    def _is_at_end(self) -> bool:
        """Check if we've consumed all source characters."""
        return self._current >= len(self.source)

    def _newline(self) -> None:
        """Track a newline: increment line counter, reset column."""
        self._line += 1
        self._column = 1

    # ── Token construction ────────────────────────────────────

    def _add_token(self, token_type: TokenType, value: object = None) -> None:
        """Append a token to the output list."""
        lexeme = self.source[self._start : self._current]
        self.tokens.append(
            Token(
                type=token_type,
                lexeme=lexeme,
                line=self._start_line,
                column=self._start_col,
                value=value,
            )
        )

    # ── Error reporting ───────────────────────────────────────

    def _error(self, message: str) -> None:
        """Raise a syntax error with the current source location."""
        source_lines = self.source.splitlines()
        source_line = ""
        if 1 <= self._start_line <= len(source_lines):
            source_line = source_lines[self._start_line - 1]

        raise FreshSyntaxError(
            message=message,
            line=self._start_line,
            column=self._start_col,
            source_line=source_line,
            filename=self.filename,
        )
