"""Fresh parser: transforms a token stream into an Abstract Syntax Tree.

Combines two parsing strategies:
  - Pratt parser (top-down operator precedence) for expressions
  - Recursive descent for statements and declarations
"""

from __future__ import annotations

from enum import IntEnum
from typing import Callable

from fresh.common.errors import FreshSyntaxError
from fresh.lexer.tokens import Token, TokenType
from fresh.parser.ast import (
    ArrayExpr,
    AssignExpr,
    BinaryExpr,
    BlockStmt,
    BreakStmt,
    CallExpr,
    ClassDeclStmt,
    ConstructorDecl,
    ContinueStmt,
    Expr,
    ExprStmt,
    PrintStmt,
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
    LiteralPattern,
    LogicalExpr,
    MatchArm,
    MatchExpr,
    Parameter,
    Pattern,
    ReturnStmt,
    Stmt,
    StructDeclStmt,
    StructField,
    StructLiteralExpr,
    StructPattern,
    SuperExpr,
    ThisExpr,
    TypeAnnotation,
    UnaryExpr,
    VarDeclStmt,
    VariableExpr,
    VariablePattern,
    WhileStmt,
    WildcardPattern,
)


class Precedence(IntEnum):
    NONE = 0
    ASSIGNMENT = 1
    OR = 2
    AND = 3
    EQUALITY = 4
    COMPARISON = 5
    TERM = 6
    FACTOR = 7
    UNARY = 8
    CALL = 9
    PRIMARY = 10


class Parser:
    def __init__(self, tokens: list[Token], filename: str = "<stdin>") -> None:
        self.tokens = tokens
        self.filename = filename
        self._current: int = 0
        self.recursion_depth: int = 0

        self._prefix_rules: dict[TokenType, Callable] = {
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
            TokenType.THIS: self._this_expr,
            TokenType.SUPER: self._super_expr,
        }

        self._infix_rules: dict[TokenType, Callable] = {
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

    # ── Top-level ──────────────────────────────────────────────

    def parse(self) -> list[Stmt]:
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
        self._advance()
        while not self._is_at_end():
            if self._previous().type == TokenType.SEMICOLON:
                return
            if self._peek().type in (
                TokenType.FN, TokenType.LET, TokenType.FOR, TokenType.IF,
                TokenType.WHILE, TokenType.RETURN, TokenType.STRUCT,
                TokenType.IMPORT, TokenType.CLASS,
            ):
                return
            self._advance()

    # ── Declarations ───────────────────────────────────────────

    def _declaration(self) -> Stmt:
        if self._match(TokenType.LET):
            return self._var_declaration()
        if self._match(TokenType.VAR):
            return self._var_declaration()
        if self._match(TokenType.FN):
            return self._fn_declaration()
        if self._match(TokenType.STRUCT):
            return self._struct_declaration()
        if self._match(TokenType.IMPORT):
            return self._import_declaration()
        if self._match(TokenType.CLASS):
            return self._class_declaration()
        return self._statement()

    def _declaration_or_statement(self) -> Stmt:
        if self._match(TokenType.LET):
            return self._var_declaration()
        if self._match(TokenType.VAR):
            return self._var_declaration()
        if self._match(TokenType.FN):
            return self._fn_declaration()
        if self._match(TokenType.STRUCT):
            return self._struct_declaration()
        if self._match(TokenType.IMPORT):
            return self._import_declaration()
        if self._match(TokenType.CLASS):
            return self._class_declaration()
        return self._statement()

    def _import_declaration(self) -> ImportStmt:
        keyword = self._previous()
        if self._check(TokenType.IDENTIFIER) or self._check(TokenType.STRING_LIT):
            self._advance()
            mod_tok = self._previous()
        else:
            raise self._error(self._peek(), "Expected module name after import.")
        self._consume(TokenType.SEMICOLON, "Expected ';' after import.")
        return ImportStmt(keyword=keyword, module_token=mod_tok)

    def _var_declaration(self) -> VarDeclStmt:
        name = self._consume(TokenType.IDENTIFIER, "Expected variable name.")
        type_ann: TypeAnnotation | None = None
        if self._match(TokenType.COLON):
            type_ann = self._type_annotation()
        self._consume(TokenType.EQUAL, "Expected '=' after variable name.")
        initializer = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after variable declaration.")
        return VarDeclStmt(name=name, type_annotation=type_ann, initializer=initializer)

    def _fn_declaration(self) -> FnDeclStmt:
        name = self._consume(TokenType.IDENTIFIER, "Expected function name.")
        return self._fn_body(name)

    def _fn_body(self, name: Token) -> FnDeclStmt:
        self._consume(TokenType.LEFT_PAREN, "Expected '(' after function name.")
        params = self._parameter_list()
        self._consume(TokenType.RIGHT_PAREN, "Expected ')' after parameters.")
        return_type: TypeAnnotation | None = None
        if self._match(TokenType.ARROW):
            return_type = self._type_annotation()
        body = self._block_statements()
        return FnDeclStmt(name=name, params=params, return_type=return_type, body=body)

    def _struct_declaration(self) -> StructDeclStmt:
        name = self._consume(TokenType.IDENTIFIER, "Expected struct name.")
        self._consume(TokenType.LEFT_BRACE, "Expected '{' after struct name.")
        fields: list[StructField] = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            field_name = self._consume(TokenType.IDENTIFIER, "Expected field name.")
            self._consume(TokenType.COLON, "Expected ':' after field name.")
            field_type = self._type_annotation()
            fields.append(StructField(name=field_name, type_annotation=field_type))
            if not self._check(TokenType.RIGHT_BRACE):
                self._consume(TokenType.COMMA, "Expected ',' between fields.")
        self._consume(TokenType.RIGHT_BRACE, "Expected '}' after struct.")
        return StructDeclStmt(name=name, fields=fields)

    def _class_declaration(self) -> ClassDeclStmt:
        name = self._consume(TokenType.IDENTIFIER, "Expected class name.")
        parent_name: Token | None = None
        if self._match(TokenType.COLON) or self._match(TokenType.EXTENDS):
            parent_name = self._consume(TokenType.IDENTIFIER, "Expected parent class name.")
        self._consume(TokenType.LEFT_BRACE, "Expected '{' after class name.")
        fields: list[StructField] = []
        constructor: ConstructorDecl | None = None
        methods: list[FnDeclStmt] = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            if self._match(TokenType.CONSTRUCTOR):
                if constructor is not None:
                    raise self._error(self._previous(), "Only one constructor allowed.")
                constructor = self._constructor_declaration()
            elif self._match(TokenType.FN):
                method_name = self._consume(TokenType.IDENTIFIER, "Expected method name.")
                methods.append(self._fn_body(method_name))
            elif (self._check(TokenType.IDENTIFIER) and
                  self._current + 1 < len(self.tokens) and
                  self.tokens[self._current + 1].type == TokenType.LEFT_PAREN):
                method_name = self._consume(TokenType.IDENTIFIER, "Expected method name.")
                methods.append(self._fn_body(method_name))
            else:
                if self._match(TokenType.VAR):
                    pass
                field_name = self._consume(TokenType.IDENTIFIER, "Expected field name.")
                field_type: TypeAnnotation | None = None
                if self._match(TokenType.COLON):
                    field_type = self._type_annotation()
                fields.append(StructField(name=field_name, type_annotation=field_type))
                self._consume(TokenType.SEMICOLON, "Expected ';' after field.")
                if (not self._check(TokenType.RIGHT_BRACE) and
                        not self._check(TokenType.CONSTRUCTOR) and
                        not self._check(TokenType.FN)):
                    self._match(TokenType.COMMA)
        self._consume(TokenType.RIGHT_BRACE, "Expected '}' after class body.")
        return ClassDeclStmt(name=name, parent_name=parent_name, fields=fields,
                             constructor=constructor, methods=methods)

    def _constructor_declaration(self) -> ConstructorDecl:
        keyword = self._previous()
        self._consume(TokenType.LEFT_PAREN, "Expected '(' after constructor.")
        params = self._parameter_list()
        self._consume(TokenType.RIGHT_PAREN, "Expected ')' after constructor params.")
        self._consume(TokenType.LEFT_BRACE, "Expected '{' for constructor body.")
        body_stmts: list[Stmt] = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            body_stmts.append(self._declaration())
        self._consume(TokenType.RIGHT_BRACE, "Expected '}' after constructor body.")
        return ConstructorDecl(keyword=keyword, params=params, body=body_stmts, super_args=None)

    def _parameter_list(self) -> list[Parameter]:
        params: list[Parameter] = []
        if not self._check(TokenType.RIGHT_PAREN):
            while True:
                if len(params) >= 255:
                    raise self._error(self._peek(), "Too many parameters.")
                param_name = self._consume(TokenType.IDENTIFIER, "Expected parameter name.")
                type_ann: TypeAnnotation | None = None
                if self._match(TokenType.COLON):
                    type_ann = self._type_annotation()
                params.append(Parameter(name=param_name, type_annotation=type_ann))
                if not self._match(TokenType.COMMA):
                    break
        return params

    def _type_annotation(self) -> TypeAnnotation:
        if self._match(TokenType.LEFT_BRACKET):
            element_type = self._type_annotation()
            bracket_tok = self._consume(TokenType.RIGHT_BRACKET, "Expected ']' after array type.")
            array_tok = Token(type=TokenType.LEFT_BRACKET, lexeme="[]",
                              line=bracket_tok.line, column=bracket_tok.column)
            return TypeAnnotation(name=array_tok, element_type=element_type)
        if self._match(TokenType.INT_TYPE, TokenType.FLOAT_TYPE, TokenType.BOOL_TYPE,
                       TokenType.STRING_TYPE, TokenType.FN, TokenType.IDENTIFIER):
            return TypeAnnotation(name=self._previous())
        raise self._error(self._peek(), "Expected type annotation.")

    # ── Statements ─────────────────────────────────────────────

    def _statement(self) -> Stmt:
        self.recursion_depth += 1
        if self.recursion_depth > 200:
            self.recursion_depth -= 1
            raise self._error(self._peek(), "Statement nesting too deep.")
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
            if self._match(TokenType.PRINT):
                return self._print_statement()
            if self._check(TokenType.LEFT_BRACE):
                self._advance()
                return BlockStmt(statements=self._block_body())
            return self._expression_statement()
        finally:
            self.recursion_depth -= 1

    def _if_statement(self) -> IfStmt:
        keyword = self._previous()
        self._consume(TokenType.LEFT_PAREN, "Expected '(' after 'if'.")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expected ')' after condition.")
        then_branch = self._block_statements()
        else_branch: list[Stmt] | None = None
        if self._match(TokenType.ELSE):
            if self._match(TokenType.IF):
                else_branch = [self._if_statement()]
            else:
                else_branch = self._block_statements()
        return IfStmt(keyword=keyword, condition=condition,
                      then_branch=then_branch, else_branch=else_branch)

    def _while_statement(self) -> WhileStmt:
        keyword = self._previous()
        self._consume(TokenType.LEFT_PAREN, "Expected '(' after 'while'.")
        condition = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expected ')' after condition.")
        body = self._block_statements()
        return WhileStmt(keyword=keyword, condition=condition, body=body)

    def _for_statement(self) -> ForStmt:
        keyword = self._previous()
        self._consume(TokenType.LEFT_PAREN, "Expected '(' after 'for'.")
        initializer: Stmt | None = None
        if self._match(TokenType.SEMICOLON):
            pass
        elif self._match(TokenType.LET):
            initializer = self._var_declaration()
        else:
            initializer = self._expression_statement()
        condition: Expr | None = None
        if not self._check(TokenType.SEMICOLON):
            condition = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after for condition.")
        increment: Expr | None = None
        if not self._check(TokenType.RIGHT_PAREN):
            increment = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expected ')' after for clauses.")
        body = self._block_statements()
        return ForStmt(keyword=keyword, initializer=initializer,
                       condition=condition, increment=increment, body=body)

    def _return_statement(self) -> ReturnStmt:
        keyword = self._previous()
        value: Expr | None = None
        if not self._check(TokenType.SEMICOLON):
            value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after return.")
        return ReturnStmt(keyword=keyword, value=value)

    def _break_statement(self) -> BreakStmt:
        keyword = self._previous()
        self._consume(TokenType.SEMICOLON, "Expected ';' after break.")
        return BreakStmt(keyword=keyword)

    def _continue_statement(self) -> ContinueStmt:
        keyword = self._previous()
        self._consume(TokenType.SEMICOLON, "Expected ';' after continue.")
        return ContinueStmt(keyword=keyword)

    def _expression_statement(self) -> ExprStmt:
        expr = self._expression()
        if isinstance(expr, MatchExpr):
            self._match(TokenType.SEMICOLON)
        else:
            self._consume(TokenType.SEMICOLON, "Expected ';' after expression.")
        return ExprStmt(expression=expr)

    def _print_statement(self) -> PrintStmt:
        keyword = self._previous()
        value = self._expression()
        self._consume(TokenType.SEMICOLON, "Expected ';' after print.")
        return PrintStmt(keyword=keyword, value=value)

    def _block_statements(self) -> list[Stmt]:
        self._consume(TokenType.LEFT_BRACE, "Expected '{'.")
        return self._block_body()

    def _block_body(self) -> list[Stmt]:
        statements: list[Stmt] = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            statements.append(self._declaration_or_statement())
        self._consume(TokenType.RIGHT_BRACE, "Expected '}'.")
        return statements

    # ── Pratt Expression Parser ────────────────────────────────

    def _expression(self) -> Expr:
        return self._parse_precedence(Precedence.ASSIGNMENT)

    def _parse_precedence(self, min_precedence: Precedence) -> Expr:
        self.recursion_depth += 1
        if self.recursion_depth > 200:
            self.recursion_depth -= 1
            raise self._error(self._peek(), "Expression nesting too deep.")
        try:
            self._advance()
            prefix_fn = self._prefix_rules.get(self._previous().type)
            if prefix_fn is None:
                raise self._error(self._previous(),
                    f"Expected expression, got \'{self._previous().lexeme}\'.")
            left = prefix_fn()
            while (not self._is_at_end() and
                   min_precedence <= self._get_precedence(self._peek().type)):
                self._advance()
                infix_fn = self._infix_rules.get(self._previous().type)
                if infix_fn is None:
                    break
                left = infix_fn(left)
            return left
        finally:
            self.recursion_depth -= 1

    def _get_precedence(self, token_type: TokenType) -> Precedence:
        return self._precedence_table.get(token_type, Precedence.NONE)

    # ── Prefix Parselets ───────────────────────────────────────

    def _literal(self) -> Expr:
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
                raise self._error(token, f"Unexpected literal \'{token.lexeme}\'.")

    def _variable(self) -> Expr:
        name = self._previous()
        if self._check(TokenType.LEFT_BRACE) and self._is_struct_literal_ahead():
            return self._struct_literal(name)
        return VariableExpr(name=name)

    def _grouping(self) -> Expr:
        expr = self._expression()
        self._consume(TokenType.RIGHT_PAREN, "Expected ')' after expression.")
        return expr

    def _unary(self) -> Expr:
        operator = self._previous()
        operand = self._parse_precedence(Precedence.UNARY)
        return UnaryExpr(operator=operator, operand=operand)

    def _array_literal(self) -> Expr:
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

    def _this_expr(self) -> Expr:
        return ThisExpr(keyword=self._previous())

    def _super_expr(self) -> Expr:
        keyword = self._previous()
        self._consume(TokenType.DOT, "Expected '.' after 'super'.")
        if self._check(TokenType.IDENTIFIER):
            method = self._consume(TokenType.IDENTIFIER, "Expected method name after super.")
        elif self._match(TokenType.CONSTRUCTOR):
            method = self._previous()
        else:
            raise self._error(self._peek(), "Expected method name after super.")
        return SuperExpr(keyword=keyword, method=method)

    def _lambda(self) -> Expr:
        keyword = self._previous()
        self._consume(TokenType.LEFT_PAREN, "Expected '(' after 'fn'.")
        params = self._parameter_list()
        self._consume(TokenType.RIGHT_PAREN, "Expected ')' after lambda params.")
        return_type: TypeAnnotation | None = None
        if self._match(TokenType.ARROW):
            return_type = self._type_annotation()
        body = self._block_statements()
        return LambdaExpr(keyword=keyword, params=params, return_type=return_type, body=body)

    def _match_expr(self) -> Expr:
        keyword = self._previous()
        scrutinee = self._parse_precedence(Precedence.ASSIGNMENT)
        self._consume(TokenType.LEFT_BRACE, "Expected '{' after match scrutinee.")
        arms: list[MatchArm] = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            pattern = self._pattern()
            guard: Expr | None = None
            if self._match(TokenType.IF):
                guard = self._expression()
            self._consume(TokenType.FAT_ARROW, "Expected '=>' after pattern.")
            body = self._expression()
            arms.append(MatchArm(pattern=pattern, guard=guard, body=body))
            if not self._check(TokenType.RIGHT_BRACE):
                self._consume(TokenType.COMMA, "Expected ',' between match arms.")
        self._consume(TokenType.RIGHT_BRACE, "Expected '}' after match arms.")
        return MatchExpr(keyword=keyword, scrutinee=scrutinee, arms=arms)

    # ── Infix Parselets ────────────────────────────────────────

    def _binary(self, left: Expr) -> Expr:
        operator = self._previous()
        prec = self._get_precedence(operator.type)
        right = self._parse_precedence(Precedence(prec + 1))
        return BinaryExpr(left=left, operator=operator, right=right)

    def _logical(self, left: Expr) -> Expr:
        operator = self._previous()
        prec = self._get_precedence(operator.type)
        right = self._parse_precedence(Precedence(prec + 1))
        return LogicalExpr(left=left, operator=operator, right=right)

    def _call(self, left: Expr) -> Expr:
        paren = self._previous()
        arguments: list[Expr] = []
        if not self._check(TokenType.RIGHT_PAREN):
            while True:
                if len(arguments) >= 255:
                    raise self._error(self._peek(), "Too many arguments.")
                arguments.append(self._expression())
                if not self._match(TokenType.COMMA):
                    break
                if self._check(TokenType.RIGHT_PAREN):
                    break
        self._consume(TokenType.RIGHT_PAREN, "Expected ')' after arguments.")
        return CallExpr(callee=left, paren=paren, arguments=arguments)

    def _index(self, left: Expr) -> Expr:
        bracket = self._previous()
        index_expr = self._expression()
        self._consume(TokenType.RIGHT_BRACKET, "Expected ']' after index.")
        return IndexExpr(obj=left, bracket=bracket, index=index_expr)

    def _dot(self, left: Expr) -> Expr:
        name = self._consume(TokenType.IDENTIFIER, "Expected field name after '.'.")
        return FieldAccessExpr(obj=left, name=name)

    def _assign(self, left: Expr) -> Expr:
        equals = self._previous()
        value = self._parse_precedence(Precedence.ASSIGNMENT)
        if isinstance(left, VariableExpr):
            return AssignExpr(name=left.name, value=value)
        if isinstance(left, FieldAccessExpr):
            return FieldSetExpr(obj=left.obj, name=left.name, value=value)
        if isinstance(left, IndexExpr):
            return IndexSetExpr(obj=left.obj, bracket=left.bracket,
                                index=left.index, value=value)
        raise self._error(equals, "Invalid assignment target.")

    # ── Struct Literal ─────────────────────────────────────────

    def _is_struct_literal_ahead(self) -> bool:
        pos = self._current
        if pos + 1 >= len(self.tokens):
            return False
        if self.tokens[pos + 1].type == TokenType.RIGHT_BRACE:
            return True
        if pos + 2 >= len(self.tokens):
            return False
        return (self.tokens[pos + 1].type == TokenType.IDENTIFIER and
                self.tokens[pos + 2].type == TokenType.COLON)

    def _struct_literal(self, name: Token) -> Expr:
        self._consume(TokenType.LEFT_BRACE, "Expected '{' for struct literal.")
        fields: list[tuple[Token, Expr]] = []
        while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
            field_name = self._consume(TokenType.IDENTIFIER, "Expected field name.")
            self._consume(TokenType.COLON, "Expected ':' after field name.")
            field_value = self._expression()
            fields.append((field_name, field_value))
            if not self._check(TokenType.RIGHT_BRACE):
                self._consume(TokenType.COMMA, "Expected ',' between fields.")
        self._consume(TokenType.RIGHT_BRACE, "Expected '}' after struct literal.")
        return StructLiteralExpr(name=name, fields=fields)

    # ── Pattern Parsing ────────────────────────────────────────

    def _pattern(self) -> Pattern:
        if self._match(TokenType.UNDERSCORE):
            return WildcardPattern(token=self._previous())
        if self._match(TokenType.INT_LIT, TokenType.FLOAT_LIT, TokenType.STRING_LIT):
            tok = self._previous()
            return LiteralPattern(value=tok.value, token=tok)
        if self._match(TokenType.TRUE):
            return LiteralPattern(value=True, token=self._previous())
        if self._match(TokenType.FALSE):
            return LiteralPattern(value=False, token=self._previous())
        if self._match(TokenType.NIL):
            return LiteralPattern(value=None, token=self._previous())
        if self._match(TokenType.IDENTIFIER):
            name = self._previous()
            if self._match(TokenType.LEFT_BRACE):
                field_patterns: list[tuple[Token, Pattern]] = []
                while not self._check(TokenType.RIGHT_BRACE) and not self._is_at_end():
                    fld = self._consume(TokenType.IDENTIFIER, "Expected field name in pattern.")
                    self._consume(TokenType.COLON, "Expected ':' in pattern.")
                    pat = self._pattern()
                    field_patterns.append((fld, pat))
                    if not self._check(TokenType.RIGHT_BRACE):
                        self._consume(TokenType.COMMA, "Expected ','.")
                self._consume(TokenType.RIGHT_BRACE, "Expected '}'.")
                return StructPattern(name=name, field_patterns=field_patterns)
            return VariablePattern(name=name)
        raise self._error(self._peek(), f"Expected pattern, got \'{self._peek().lexeme}\'.")

    # ── Token Navigation ───────────────────────────────────────

    def _advance(self) -> Token:
        if not self._is_at_end():
            self._current += 1
        return self._previous()

    def _peek(self) -> Token:
        return self.tokens[self._current]

    def _peek_next(self) -> Token:
        if self._current + 1 >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self._current + 1]

    def _peek_next_is(self, token_type: TokenType) -> bool:
        return self._peek_next().type == token_type

    def _previous(self) -> Token:
        return self.tokens[self._current - 1]

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _check(self, token_type: TokenType) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type == token_type

    def _match(self, *types: TokenType) -> bool:
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _consume(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        raise self._error(self._peek(), message)

    def _error(self, token: Token, message: str) -> FreshSyntaxError:
        return FreshSyntaxError(message=message, line=token.line,
                                column=token.column, filename=self.filename)
