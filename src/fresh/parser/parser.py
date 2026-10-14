"""Fresh parser: transforms a token stream into an Abstract Syntax Tree.

Combines two parsing strategies:
  - **Pratt parser** (top-down operator precedence) for expressions,
    handling binary, unary, call, index, field access, assignment,
    match expressions, lambdas, and struct literals.
  - **Recursive descent** for statements and declarations (let, fn,
    struct, if, while, for, return, break, continue, blocks).

Usage:
    from fresh.lexer import Scanner
    from fresh.parser import Parser

    tokens = Scanner(source).scan_tokens()
    ast = Parser(tokens).parse()   # returns list[Stmt]
"""

from __future__ import annotations

from enum import IntEnum
from typing import Callable

from fresh.common.errors import FreshSyntaxError
from fresh.lexer.tokens import Token, TokenType
from fresh.parser.ast import (
    # Expressions
    ArrayExpr,
    AssignExpr,
    BinaryExpr,
    # Statements
    BlockStmt,
    BreakStmt,
    CallExpr,
    ContinueStmt,
    Expr,
    ExprStmt,
    FieldAccessExpr,
    FieldSetExpr,
    FnDeclStmt,
    ForStmt,
    IfStmt,
    ImportStmt,
    IndexExpr,
    IndexSetExpr,
    LambdaExpr,
    LiteralExpr,
    # Patterns
    LiteralPattern,
    LogicalExpr,
    MatchArm,
    MatchExpr,
    # Helpers
    Parameter,
    Pattern,
    ReturnStmt,
    Stmt,
    StructDeclStmt,
    StructField,
    StructLiteralExpr,
    StructPattern,
    TypeAnnotation,
    UnaryExpr,
    VarDeclStmt,
    VariableExpr,
    VariablePattern,
    WhileStmt,
    WildcardPattern,
)

# ══════════════════════════════════════════════════════════════
#  Precedence Levels
# ══════════════════════════════════════════════════════════════


class Precedence(IntEnum):
    """Operator precedence levels for the Pratt parser.

    Higher values bind tighter.  Assignment is the lowest
    precedence; primary expressions are the highest.
    """

    NONE = 0
    ASSIGNMENT = 1  # =
    OR = 2  # ||
    AND = 3  # &&
    EQUALITY = 4  # == !=
    COMPARISON = 5  # < > <= >=
    TERM = 6  # + -
    FACTOR = 7  # * / %
    UNARY = 8  # ! - (prefix)
    CALL = 9  # () [] .
    PRIMARY = 10


# ══════════════════════════════════════════════════════════════
#  Parser
# ══════════════════════════════════════════════════════════════


class Parser:
    """Parses a Fresh token stream into an AST.

    The parser owns three lookup tables that drive Pratt expression
    parsing: *prefix rules*, *infix rules*, and a *precedence table*.
    Statement / declaration parsing is handled via classic recursive
    descent methods.
    """

    def __init__(self, tokens: list[Token], filename: str = "<stdin>") -> None:
        self.tokens = tokens
        self.filename = filename
        self._current: int = 0

        # ── Pratt tables ──────────────────────────────────────

        self._prefix_rules: dict[TokenType, Callable[[], Expr]] = {
            TokenType.INT_LIT: self._literal,
            TokenType.FLOAT_LIT: self._literal,
            TokenType.STRING_LIT: self._literal,
            TokenType.TRUE: self._literal,
            TokenType.FALSE: self._literal,
            TokenType.NIL: self._literal,
            TokenType.IDENTIFIER: self._variable,
            TokenType.LEFT_PAREN: self._grouping,
            TokenType.MINUS: self._unary,
            TokenType.BANG: self._unary,
            TokenType.LEFT_BRACKET: self._array_literal,
            TokenType.FN: self._lambda,
            TokenType.MATCH: self._match_expr,
        }

        self._infix_rules: dict[TokenType, Callable[[Expr], Expr]] = {
            TokenType.PLUS: self._binary,
            TokenType.MINUS: self._binary,
            TokenType.STAR: self._binary,
            TokenType.SLASH: self._binary,
            TokenType.PERCENT: self._binary,
            TokenType.EQUAL_EQUAL: self._binary,
            TokenType.BANG_EQUAL: self._binary,
            TokenType.LESS: self._binary,
            TokenType.LESS_EQUAL: self._binary,
            TokenType.GREATER: self._binary,
            TokenType.GREATER_EQUAL: self._binary,
            TokenType.PIPE_PIPE: self._logical,
            TokenType.AMP_AMP: self._logical,
            TokenType.LEFT_PAREN: self._call,
            TokenType.LEFT_BRACKET: self._index,
            TokenType.DOT: self._dot,
            TokenType.EQUAL: self._assign,
        }

        self._precedence_table: dict[TokenType, Precedence] = {
            TokenType.EQUAL: Precedence.ASSIGNMENT,
            TokenType.PIPE_PIPE: Precedence.OR,
            TokenType.AMP_AMP: Precedence.AND,
            TokenType.EQUAL_EQUAL: Precedence.EQUALITY,
            TokenType.BANG_EQUAL: Precedence.EQUALITY,
            TokenType.LESS: Precedence.COMPARISON,
            TokenType.LESS_EQUAL: Precedence.COMPARISON,
            TokenType.GREATER: Precedence.COMPARISON,
            TokenType.GREATER_EQUAL: Precedence.COMPARISON,
            TokenType.PLUS: Precedence.TERM,
            TokenType.MINUS: Precedence.TERM,
            TokenType.STAR: Precedence.FACTOR,
            TokenType.SLASH: Precedence.FACTOR,
            TokenType.PERCENT: Precedence.FACTOR,
            TokenType.LEFT_PAREN: Precedence.CALL,
            TokenType.LEFT_BRACKET: Precedence.CALL,
            TokenType.DOT: Precedence.CALL,
        }

        self.recursion_depth: int = 0


    def parse(self) -> list[Stmt]:
        """Parse the entire token stream into a list of statements with synchronization recovery."""
        statements: list[Stmt] = []
        errors: list[FreshSyntaxError] = []

        while not self._is_at_end():
            try:
                decl = self._declaration()
                if decl is not None:
                    statements.append(decl)
            except FreshSyntaxError as err:
                errors.append(err)
                self._synchronize()

        if errors:
            raise errors[0]

        return statements

    def _synchronize(self) -> None:
        """Discard tokens until a statement boundary is found for error recovery."""
        self._advance()
        while not self._is_at_end():
            if self._previous().type == TokenType.SEMICOLON:
                return

            if self._peek().type in (
                TokenType.FN,
                TokenType.LET,
                TokenType.FOR,
                TokenType.IF,
                TokenType.WHILE,
                TokenType.RETURN,
                TokenType.STRUCT,
                TokenType.IMPORT,
            ):
                return

            self._advance()

    # ══════════════════════════════════════════════════════════
    #  Declaration Parsing
    # ══════════════════════════════════════════════════════════

    def _declaration(self) -> Stmt:

        """Parse a declaration or fall through to a statement."""
        if self._match(TokenType.LET):
            return self._var_declaration()
        if self._match(TokenType.FN):
            return self._fn_declaration()
        if self._match(TokenType.STRUCT):
            return self._struct_declaration()
        if self._match(TokenType.IMPORT):
            return self._import_declaration()
        return self._statement()

    def _import_declaration(self) -> ImportStmt:
        """Parse: ``import module_name;`` or ``import "path.fresh";``"""
        keyword = self._previous()
        if self._check(TokenType.IDENTIFIER) or self._check(TokenType.STRING_LIT):
            self._advance()
            mod_tok = self._previous()
        else:
            raise self._error(self._peek(), "Expected module identifier or file path string after 'import'.")
        self._consume(TokenType.SEMICOLON, "Expected ';' after import path.")
        return ImportStmt(keyword=keyword, module_token=mod_tok)


    def _var_declaration(self) -> VarDeclStmt:
        """Parse: ``let name [: type] = expr ;``"""
        name = self._consume(TokenType.IDENTIFIER, "Expected variable name after 'let'.")

        type_ann: TypeAnnotation | None = None
        if self._match(TokenType.COLON):
            type_ann = self._type_annotation()

        self._consume(TokenType.EQUAL, "Expected '=' after variable name.")
        initializer = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after variable declaration.")

        return VarDeclStmt(name=name, type_annotation=type_ann, initializer=initializer)

    def _fn_declaration(self) -> FnDeclStmt:
        """Parse: ``fn name ( [params] ) [-> type] { body }``"""
        name = self._consume(TokenType.IDENTIFIER, "Expected function name after 'fn'.")
        return self._fn_body(name)

    def _fn_body(self, name: Token) -> FnDeclStmt:
        """Parse the parameter list, optional return type, and block body."""
        self._consume(TokenType.LEFT_PAREN, "Expected '(' after function name.")
        params = self._parameter_list()
        self._consume(TokenType.RIGHT_PAREN, "Expected ')' after parameters.")

        return_type: TypeAnnotation | None = None
        if self._match(TokenType.ARROW):
            return_type = self._type_annotation()

        body = self._block_statements()
        return FnDeclStmt(name=name, params=params, return_type=return_type, body=body)

    def _struct_declaration(self) -> StructDeclStmt:
        """Parse: ``struct Name { field: type, ... }``"""
        name = self._consume(TokenType.IDENTIFIER, "Expected struct name after 'struct'.")
        self._consume(TokenType.LEFT_BRACE, "Expected '{' after struct name.")

        fields: list[StructField] = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            field_name = self._consume(TokenType.IDENTIFIER, "Expected field name.")
            self._consume(TokenType.COLON, "Expected ':' after field name.")
            field_type = self._type_annotation()
            fields.append(StructField(name=field_name, type_annotation=field_type))
            if not self._check(TokenType.RIGHT_BRACE):
                self._consume(TokenType.COMMA, "Expected ',' between struct fields.")

        self._consume(TokenType.RIGHT_BRACE, "Expected '}' after struct fields.")
        return StructDeclStmt(name=name, fields=fields)

    def _parameter_list(self) -> list[Parameter]:
        """Parse a comma-separated parameter list: ``name: type, ...``"""
        params: list[Parameter] = []
        if not self._check(TokenType.RIGHT_PAREN):
            while True:
                if len(params) >= 255:
                    raise self._error(self._peek(), "Cannot have more than 255 parameters.")
                param_name = self._consume(TokenType.IDENTIFIER, "Expected parameter name.")
                self._consume(TokenType.COLON, "Expected ':' after parameter name.")
                type_ann = self._type_annotation()
                params.append(Parameter(name=param_name, type_annotation=type_ann))
                if not self._match(TokenType.COMMA):
                    break
        return params

    def _type_annotation(self) -> TypeAnnotation:
        """Parse a type: ``int | float | bool | string | [type] | fn | Identifier``."""
        # Array type: [element_type]
        if self._match(TokenType.LEFT_BRACKET):
            element_type = self._type_annotation()
            bracket_tok = self._consume(
                TokenType.RIGHT_BRACKET, "Expected ']' after array element type."
            )
            # Synthesise a token to represent the array type
            array_tok = Token(
                type=TokenType.LEFT_BRACKET,
                lexeme="[]",
                line=bracket_tok.line,
                column=bracket_tok.column,
            )
            return TypeAnnotation(name=array_tok, element_type=element_type)

        # Primitive / custom types
        if self._match(
            TokenType.INT_TYPE,
            TokenType.FLOAT_TYPE,
            TokenType.BOOL_TYPE,
            TokenType.STRING_TYPE,
            TokenType.FN,
            TokenType.IDENTIFIER,
        ):
            return TypeAnnotation(name=self._previous())

        raise self._error(self._peek(), "Expected type annotation.")

    # ══════════════════════════════════════════════════════════
    #  Statement Parsing
    # ══════════════════════════════════════════════════════════

    def _statement(self) -> Stmt:
        """Route to the appropriate statement parser."""
        self.recursion_depth += 1
        if self.recursion_depth > 200:
            self.recursion_depth -= 1
            raise self._error(self._peek(), "Statement nesting depth exceeded limit.")
        try:
            if self._match(TokenType.IF):
                return self._if_statement()
            if self._match(TokenType.WHILE):
                return self._while_statement()
            if self._match(TokenType.FOR):
                return self._for_statement()
            if self._match(TokenType.RETURN):
                return self._return_statement()
            if self._match(TokenType.BREAK):
                return self._break_statement()
            if self._match(TokenType.CONTINUE):
                return self._continue_statement()
            if self._check(TokenType.LEFT_BRACE):
                self._advance()
                return BlockStmt(statements=self._block_body())
            return self._expression_statement()
        finally:
            self.recursion_depth -= 1

    def _if_statement(self) -> IfStmt:
        """Parse: ``if (cond) { ... } [else { ... } | else if ...]``"""
        keyword = self._previous()
        self._consume(TokenType.LEFT_PAREN, "Expected '(' after 'if'.")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expected ')' after if condition.")

        then_branch = self._block_statements()

        else_branch: list[Stmt] | None = None
        if self._match(TokenType.ELSE):
            if self._match(TokenType.IF):
                # ``else if`` chain → wrap the nested IfStmt in a list
                else_branch = [self._if_statement()]
            else:
                else_branch = self._block_statements()

        return IfStmt(
            keyword=keyword,
            condition=condition,
            then_branch=then_branch,
            else_branch=else_branch,
        )

    def _while_statement(self) -> WhileStmt:
        """Parse: ``while (condition) { body }``"""
        keyword = self._previous()
        self._consume(TokenType.LEFT_PAREN, "Expected '(' after 'while'.")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expected ')' after while condition.")
        body = self._block_statements()
        return WhileStmt(keyword=keyword, condition=condition, body=body)

    def _for_statement(self) -> ForStmt:
        """Parse: ``for (init; condition; increment) { body }``"""
        keyword = self._previous()
        self._consume(TokenType.LEFT_PAREN, "Expected '(' after 'for'.")

        # Initializer clause
        initializer: Stmt | None = None
        if self._match(TokenType.SEMICOLON):
            pass  # No initializer
        elif self._match(TokenType.LET):
            initializer = self._var_declaration()
        else:
            initializer = self._expression_statement()

        # Condition clause
        condition: Expr | None = None
        if not self._check(TokenType.SEMICOLON):
            condition = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after for-loop condition.")

        # Increment clause
        increment: Expr | None = None
        if not self._check(TokenType.RIGHT_PAREN):
            increment = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expected ')' after for-loop clauses.")

        body = self._block_statements()
        return ForStmt(
            keyword=keyword,
            initializer=initializer,
            condition=condition,
            increment=increment,
            body=body,
        )

    def _return_statement(self) -> ReturnStmt:
        """Parse: ``return [expr] ;``"""
        keyword = self._previous()
        value: Expr | None = None
        if not self._check(TokenType.SEMICOLON):
            value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after return value.")
        return ReturnStmt(keyword=keyword, value=value)

    def _break_statement(self) -> BreakStmt:
        """Parse: ``break ;``"""
        keyword = self._previous()
        self._consume(TokenType.SEMICOLON, "Expected ';' after 'break'.")
        return BreakStmt(keyword=keyword)

    def _continue_statement(self) -> ContinueStmt:
        """Parse: ``continue ;``"""
        keyword = self._previous()
        self._consume(TokenType.SEMICOLON, "Expected ';' after 'continue'.")
        return ContinueStmt(keyword=keyword)

    def _expression_statement(self) -> ExprStmt:
        """Parse: ``expression ;``

        Match expressions are allowed without a trailing semicolon
        since they end with ``}`` and the semicolon would be ugly.
        """
        expr = self._expression()
        # Match expressions don't require a trailing semicolon
        if isinstance(expr, MatchExpr):
            self._match(TokenType.SEMICOLON)  # consume if present, ignore if absent
        else:
            self._consume(TokenType.SEMICOLON, "Expected ';' after expression.")
        return ExprStmt(expression=expr)

    def _block_statements(self) -> list[Stmt]:
        """Consume ``{`` then parse declarations until ``}``."""
        self._consume(TokenType.LEFT_BRACE, "Expected '{'.")
        return self._block_body()

    def _block_body(self) -> list[Stmt]:
        """Parse the interior of a block (``{`` already consumed)."""
        statements: list[Stmt] = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            statements.append(self._declaration())
        self._consume(TokenType.RIGHT_BRACE, "Expected '}'.")
        return statements

    # ══════════════════════════════════════════════════════════
    #  Pratt Expression Parser
    # ══════════════════════════════════════════════════════════

    def _expression(self) -> Expr:
        """Parse an expression starting at the lowest precedence."""
        return self._parse_precedence(Precedence.ASSIGNMENT)

    def _parse_precedence(self, min_precedence: Precedence) -> Expr:
        """Core Pratt loop: parse at or above *min_precedence*.

        1. Consume a token and invoke its *prefix* rule to get ``left``.
        2. While the next token's *infix* precedence >= ``min_precedence``,
           consume it and invoke its *infix* rule with ``left``.
        3. Return the final expression tree.
        """
        self.recursion_depth += 1
        if self.recursion_depth > 200:
            self.recursion_depth -= 1
            raise self._error(self._peek(), "Expression nesting depth exceeded limit.")

        try:
            self._advance()

            prefix_fn = self._prefix_rules.get(self._previous().type)
            if prefix_fn is None:
                raise self._error(
                    self._previous(),
                    f"Expected expression, got '{self._previous().lexeme}'.",
                )

            left = prefix_fn()

            while (
                not self._is_at_end()
                and min_precedence <= self._get_precedence(self._peek().type)
            ):
                self._advance()
                infix_fn = self._infix_rules.get(self._previous().type)
                if infix_fn is None:
                    break  # pragma: no cover — shouldn't happen if tables are consistent
                left = infix_fn(left)

            return left
        finally:
            self.recursion_depth -= 1


    def _get_precedence(self, token_type: TokenType) -> Precedence:
        """Look up the infix precedence of a token type."""
        return self._precedence_table.get(token_type, Precedence.NONE)

    # ── Prefix Parselets ──────────────────────────────────────

    def _literal(self) -> Expr:
        """Number, string, boolean, or nil literal."""
        token = self._previous()
        match token.type:
            case TokenType.INT_LIT | TokenType.FLOAT_LIT | TokenType.STRING_LIT:
                return LiteralExpr(value=token.value, token=token)
            case TokenType.TRUE:
                return LiteralExpr(value=True, token=token)
            case TokenType.FALSE:
                return LiteralExpr(value=False, token=token)
            case TokenType.NIL:
                return LiteralExpr(value=None, token=token)
            case _:
                raise self._error(token, f"Unexpected literal '{token.lexeme}'.")

    def _variable(self) -> Expr:
        """Variable reference, or struct literal if followed by ``{ id: ... }``."""
        name = self._previous()

        # Struct literal:  Name { field: expr, ... }
        if self._check(TokenType.LEFT_BRACE) and self._is_struct_literal_ahead():
            return self._struct_literal(name)

        return VariableExpr(name=name)

    def _grouping(self) -> Expr:
        """Parenthesised expression ``( expr )``."""
        expr = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expected ')' after expression.")
        return expr

    def _unary(self) -> Expr:
        """Prefix unary: ``-expr``  or  ``!expr``."""
        operator = self._previous()
        operand = self._parse_precedence(Precedence.UNARY)
        return UnaryExpr(operator=operator, operand=operand)

    def _array_literal(self) -> Expr:
        """Array literal: ``[expr, expr, ...]``."""
        bracket = self._previous()
        elements: list[Expr] = []

        if not self._check(TokenType.RIGHT_BRACKET):
            while True:
                elements.append(self._expression())
                if not self._match(TokenType.COMMA):
                    break
                if self._check(TokenType.RIGHT_BRACKET):
                    break

        self._consume(TokenType.RIGHT_BRACKET, "Expected ']' after array elements.")
        return ArrayExpr(bracket=bracket, elements=elements)

    def _lambda(self) -> Expr:
        """Anonymous function: ``fn(params) [-> type] { body }``."""
        keyword = self._previous()
        self._consume(TokenType.LEFT_PAREN, "Expected '(' after 'fn' in lambda.")
        params = self._parameter_list()
        self._consume(TokenType.RIGHT_PAREN, "Expected ')' after lambda parameters.")

        return_type: TypeAnnotation | None = None
        if self._match(TokenType.ARROW):
            return_type = self._type_annotation()

        body = self._block_statements()
        return LambdaExpr(
            keyword=keyword, params=params, return_type=return_type, body=body
        )

    def _match_expr(self) -> Expr:
        """Match expression: ``match scrutinee { pattern => body, ... }``."""
        keyword = self._previous()
        scrutinee = self._parse_precedence(Precedence.ASSIGNMENT)
        self._consume(TokenType.LEFT_BRACE, "Expected '{' after match scrutinee.")

        arms: list[MatchArm] = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            pattern = self._pattern()

            # Optional guard clause:  ``pattern if cond => ...``
            guard: Expr | None = None
            if self._match(TokenType.IF):
                guard = self._expression()

            self._consume(TokenType.FAT_ARROW, "Expected '=>' after match pattern.")
            body = self._expression()
            arms.append(MatchArm(pattern=pattern, guard=guard, body=body))

            # Arms are separated by commas; trailing comma before ``}`` is OK
            if not self._check(TokenType.RIGHT_BRACE):
                self._consume(TokenType.COMMA, "Expected ',' between match arms.")

        self._consume(TokenType.RIGHT_BRACE, "Expected '}' after match arms.")
        return MatchExpr(keyword=keyword, scrutinee=scrutinee, arms=arms)

    # ── Infix Parselets ───────────────────────────────────────

    def _binary(self, left: Expr) -> Expr:
        """Left-associative binary op: ``left + right``, ``left * right``, etc."""
        operator = self._previous()
        prec = self._get_precedence(operator.type)
        right = self._parse_precedence(Precedence(prec + 1))
        return BinaryExpr(left=left, operator=operator, right=right)

    def _logical(self, left: Expr) -> Expr:
        """Short-circuit logical: ``left && right``, ``left || right``."""
        operator = self._previous()
        prec = self._get_precedence(operator.type)
        right = self._parse_precedence(Precedence(prec + 1))
        return LogicalExpr(left=left, operator=operator, right=right)

    def _call(self, left: Expr) -> Expr:
        """Function call: ``callee(arg1, arg2, ...)``."""
        paren = self._previous()
        arguments: list[Expr] = []

        if not self._check(TokenType.RIGHT_PAREN):
            while True:
                if len(arguments) >= 255:
                    raise self._error(self._peek(), "Cannot have more than 255 arguments.")
                arguments.append(self._expression())
                if not self._match(TokenType.COMMA):
                    break
                if self._check(TokenType.RIGHT_PAREN):
                    break

        self._consume(TokenType.RIGHT_PAREN, "Expected ')' after arguments.")
        return CallExpr(callee=left, paren=paren, arguments=arguments)

    def _index(self, left: Expr) -> Expr:
        """Index access: ``obj[index]``."""
        bracket = self._previous()
        index_expr = self._expression()
        self._consume(TokenType.RIGHT_BRACKET, "Expected ']' after index.")
        return IndexExpr(obj=left, bracket=bracket, index=index_expr)

    def _dot(self, left: Expr) -> Expr:
        """Field access: ``obj.field``."""
        name = self._consume(TokenType.IDENTIFIER, "Expected field name after '.'.")
        return FieldAccessExpr(obj=left, name=name)

    def _assign(self, left: Expr) -> Expr:
        """Assignment (right-associative): ``target = value``.

        Valid targets: variables, field accesses, and index accesses.
        """
        equals = self._previous()
        # Right-associative: parse RHS at *same* precedence level
        value = self._parse_precedence(Precedence.ASSIGNMENT)

        if isinstance(left, VariableExpr):
            return AssignExpr(name=left.name, value=value)

        if isinstance(left, FieldAccessExpr):
            return FieldSetExpr(obj=left.obj, name=left.name, value=value)

        if isinstance(left, IndexExpr):
            return IndexSetExpr(
                obj=left.obj, bracket=left.bracket, index=left.index, value=value
            )

        raise self._error(equals, "Invalid assignment target.")

    # ── Struct Literal Parsing ────────────────────────────────

    def _is_struct_literal_ahead(self) -> bool:
        """Lookahead: does ``{`` start a struct literal?

        Checks whether the tokens after ``{`` match
        ``IDENTIFIER :`` (struct with fields) or ``}`` (empty struct).
        """
        pos = self._current  # currently points to the ``{`` token
        if pos + 1 >= len(self.tokens):
            return False

        # Empty struct:  Name { }
        if self.tokens[pos + 1].type == TokenType.RIGHT_BRACE:
            return True

        # Struct with fields:  Name { identifier : ...
        if pos + 2 >= len(self.tokens):
            return False
        return (
            self.tokens[pos + 1].type == TokenType.IDENTIFIER
            and self.tokens[pos + 2].type == TokenType.COLON
        )

    def _struct_literal(self, name: Token) -> Expr:
        """Parse ``Name { field: expr, ... }``."""
        self._consume(TokenType.LEFT_BRACE, "Expected '{' for struct literal.")

        fields: list[tuple[Token, Expr]] = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            field_name = self._consume(TokenType.IDENTIFIER, "Expected field name.")
            self._consume(TokenType.COLON, "Expected ':' after field name in struct literal.")
            field_value = self._expression()
            fields.append((field_name, field_value))
            if not self._check(TokenType.RIGHT_BRACE):
                self._consume(TokenType.COMMA, "Expected ',' between struct fields.")

        self._consume(TokenType.RIGHT_BRACE, "Expected '}' after struct literal.")
        return StructLiteralExpr(name=name, fields=fields)

    # ══════════════════════════════════════════════════════════
    #  Pattern Parsing
    # ══════════════════════════════════════════════════════════

    def _pattern(self) -> Pattern:
        """Parse a pattern for ``match`` arms.

        Supported patterns:
          - ``_``                       wildcard
          - ``42``, ``"hi"``, ``true``  literal
          - ``x``                       variable binding
          - ``Point { x: px, y: py }``  struct destructuring
        """
        # Wildcard
        if self._match(TokenType.UNDERSCORE):
            return WildcardPattern(token=self._previous())

        # Literal patterns
        if self._match(TokenType.INT_LIT, TokenType.FLOAT_LIT, TokenType.STRING_LIT):
            tok = self._previous()
            return LiteralPattern(value=tok.value, token=tok)

        if self._match(TokenType.TRUE):
            return LiteralPattern(value=True, token=self._previous())
        if self._match(TokenType.FALSE):
            return LiteralPattern(value=False, token=self._previous())
        if self._match(TokenType.NIL):
            return LiteralPattern(value=None, token=self._previous())

        # Identifier: variable binding, or struct pattern
        if self._match(TokenType.IDENTIFIER):
            name = self._previous()

            # Struct pattern:  Name { field: pattern, ... }
            if self._match(TokenType.LEFT_BRACE):
                field_patterns: list[tuple[Token, Pattern]] = []
                while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
                    fld = self._consume(
                        TokenType.IDENTIFIER, "Expected field name in struct pattern."
                    )
                    self._consume(TokenType.COLON, "Expected ':' after field name in pattern.")
                    pat = self._pattern()
                    field_patterns.append((fld, pat))
                    if not self._check(TokenType.RIGHT_BRACE):
                        self._consume(TokenType.COMMA, "Expected ',' between field patterns.")
                self._consume(TokenType.RIGHT_BRACE, "Expected '}' after struct pattern.")
                return StructPattern(name=name, field_patterns=field_patterns)

            # Simple variable binding
            return VariablePattern(name=name)

        raise self._error(self._peek(), f"Expected pattern, got '{self._peek().lexeme}'.")

    # ══════════════════════════════════════════════════════════
    #  Token Navigation
    # ══════════════════════════════════════════════════════════

    def _advance(self) -> Token:
        """Consume and return the current token."""
        if not self._is_at_end():
            self._current += 1
        return self._previous()

    def _peek(self) -> Token:
        """Return the current token without consuming it."""
        return self.tokens[self._current]

    def _previous(self) -> Token:
        """Return the most recently consumed token."""
        return self.tokens[self._current - 1]

    def _is_at_end(self) -> bool:
        """``True`` when we've reached the EOF sentinel token."""
        return self._peek().type == TokenType.EOF

    def _check(self, token_type: TokenType) -> bool:
        """Check the current token type without consuming."""
        if self._is_at_end():
            return False
        return self._peek().type == token_type

    def _match(self, *types: TokenType) -> bool:
        """Consume the current token if it matches any of *types*."""
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _consume(self, token_type: TokenType, message: str) -> Token:
        """Consume the current token or raise a syntax error."""
        if self._check(token_type):
            return self._advance()
        raise self._error(self._peek(), message)

    # ══════════════════════════════════════════════════════════
    #  Error Helpers
    # ══════════════════════════════════════════════════════════

    def _error(self, token: Token, message: str) -> FreshSyntaxError:
        """Create a ``FreshSyntaxError`` pointing at *token*."""
        return FreshSyntaxError(
            message=message,
            line=token.line,
            column=token.column,
            filename=self.filename,
        )
