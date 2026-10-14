"""Variable resolver and scope checker for Fresh.

Performs static analysis to:
  - Resolve variable binding scopes (global vs local vs upvalue)
  - Detect duplicate variable declarations in the same scope
  - Detect reading variables in their own initializers
  - Validate `break` and `continue` usage inside loop scopes
  - Track function scopes and nesting depth
"""

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

from fresh.common.errors import FreshNameError, FreshSyntaxError
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
    MatchExpr,
    ReturnStmt,
    Stmt,
    StructDeclStmt,
    StructLiteralExpr,
    StructPattern,
    SuperExpr,
    ThisExpr,
    UnaryExpr,
    VarDeclStmt,
    VariableExpr,
    VariablePattern,
    WhileStmt,
    WildcardPattern,
)

if TYPE_CHECKING:
    from fresh.lexer.tokens import Token


class FunctionType(Enum):
    """Tracks function nesting level for return statement validation."""

    NONE = auto()
    FUNCTION = auto()
    LAMBDA = auto()


class ClassType(Enum):
    """Tracks class nesting context for this/super validation."""

    NONE = auto()
    CLASS = auto()
    SUBCLASS = auto()


BUILTINS = {
    "print",
    "println",
    "input",
    "read_int",
    "len",
    "push",
    "pop",
    "clock",
    "type",
    "to_string",
    "to_int",
    "to_float",
    "read_file",
    "write_file",
    "file_exists",
    "abs",
    "sqrt",
    "pow",
    "min",
    "max",
    "floor",
    "ceil",
    "round",
}


class Resolver:
    """AST Visitor that resolves variable declarations and scopes."""

    def __init__(self, filename: str = "<stdin>") -> None:
        self.filename = filename
        # Global scope with standard library built-ins pre-populated
        global_scope = {name: True for name in BUILTINS}
        self.scopes: list[dict[str, bool]] = [global_scope]
        self.current_function: FunctionType = FunctionType.NONE
        self.current_class: ClassType = ClassType.NONE
        self.loop_depth: int = 0
        # Map AST node id to resolved scope distance / metadata
        self.locals: dict[int, int] = {}

    def resolve_program(self, statements: list[Stmt]) -> None:
        """Resolve all statements in a program with top-level declaration pre-pass."""
        # Pass 1: Pre-declare all top-level functions and structs
        for stmt in statements:
            match stmt:
                case FnDeclStmt(name=name):
                    self._declare(name)
                    self._define(name)
                case StructDeclStmt(name=name):
                    self._declare(name)
                    self._define(name)
                case ClassDeclStmt(name=name):
                    self._declare(name)
                    self._define(name)
                case _:
                    pass

        # Pass 2: Full resolution
        for stmt in statements:
            self._resolve_stmt(stmt)

    # ── Statement Resolution ──────────────────────────────────

    def _resolve_stmt(self, stmt: Stmt) -> None:
        match stmt:
            case VarDeclStmt(name=name, initializer=init):
                self._declare(name)
                if init is not None:
                    self._resolve_expr(init)
                self._define(name)

            case FnDeclStmt(name=name, params=params, body=body):
                if len(self.scopes) > 1:
                    self._declare(name)
                    self._define(name)
                self._resolve_function(params, body, FunctionType.FUNCTION)

            case StructDeclStmt():
                pass

            case ClassDeclStmt(name=name, parent_name=parent, fields=fields, constructor=ctor, methods=methods):
                enclosing_class = self.current_class
                self.current_class = ClassType.SUBCLASS if parent is not None else ClassType.CLASS

                if parent is not None:
                    if name.lexeme == parent.lexeme:
                        raise FreshSyntaxError(
                            message="A class cannot inherit from itself.",
                            line=parent.line,
                            column=parent.column,
                            filename=self.filename,
                        )
                    # Verify parent exists
                    for i in range(len(self.scopes) - 1, -1, -1):
                        if parent.lexeme in self.scopes[i]:
                            break
                    else:
                        raise FreshNameError(
                            message=f"Undefined class '{parent.lexeme}'.",
                            line=parent.line,
                            column=parent.column,
                            filename=self.filename,
                        )

                # Class scope for 'this' and 'super'
                self._begin_scope()
                self.scopes[-1]["this"] = True
                if parent is not None:
                    self.scopes[-1]["super"] = True

                if ctor is not None:
                    if ctor.super_args is not None:
                        if parent is None:
                            raise FreshSyntaxError(
                                message="Cannot call 'super' in a class with no superclass.",
                                line=ctor.keyword.line,
                                column=ctor.keyword.column,
                                filename=self.filename,
                            )
                        for s_arg in ctor.super_args:
                            self._resolve_expr(s_arg)
                    self._resolve_function(ctor.params, ctor.body, FunctionType.FUNCTION)

                for method in methods:
                    self._resolve_function(method.params, method.body, FunctionType.FUNCTION)

                self._end_scope()
                self.current_class = enclosing_class

            case BlockStmt(statements=stmts):
                self._begin_scope()
                for s in stmts:
                    self._resolve_stmt(s)
                self._end_scope()

            case ExprStmt(expression=expr):
                self._resolve_expr(expr)

            case IfStmt(condition=cond, then_branch=then_b, else_branch=else_b):
                self._resolve_expr(cond)
                self._begin_scope()
                for s in then_b:
                    self._resolve_stmt(s)
                self._end_scope()
                if else_b:
                    self._begin_scope()
                    for s in else_b:
                        self._resolve_stmt(s)
                    self._end_scope()

            case WhileStmt(condition=cond, body=body):
                self._resolve_expr(cond)
                self.loop_depth += 1
                self._begin_scope()
                for s in body:
                    self._resolve_stmt(s)
                self._end_scope()
                self.loop_depth -= 1

            case ForStmt(initializer=init, condition=cond, increment=inc, body=body):
                self._begin_scope()
                if init:
                    self._resolve_stmt(init)
                if cond:
                    self._resolve_expr(cond)
                if inc:
                    self._resolve_expr(inc)

                self.loop_depth += 1
                self._begin_scope()
                for s in body:
                    self._resolve_stmt(s)
                self._end_scope()
                self.loop_depth -= 1

                self._end_scope()

            case ReturnStmt(keyword=keyword, value=val):
                if self.current_function == FunctionType.NONE:
                    raise FreshSyntaxError(
                        message="Cannot return from top-level code.",
                        line=keyword.line,
                        column=keyword.column,
                        filename=self.filename,
                    )
                if val:
                    self._resolve_expr(val)

            case BreakStmt(keyword=keyword):
                if self.loop_depth == 0:
                    raise FreshSyntaxError(
                        message="Cannot use 'break' outside of a loop.",
                        line=keyword.line,
                        column=keyword.column,
                        filename=self.filename,
                    )

            case ContinueStmt(keyword=keyword):
                if self.loop_depth == 0:
                    raise FreshSyntaxError(
                        message="Cannot use 'continue' outside of a loop.",
                        line=keyword.line,
                        column=keyword.column,
                        filename=self.filename,
                    )

            case ImportStmt():
                pass


    # ── Expression Resolution ─────────────────────────────────

    def _resolve_expr(self, expr: Expr) -> None:
        match expr:
            case VariableExpr(name=name):
                if self.scopes and self.scopes[-1].get(name.lexeme) is False:
                    raise FreshNameError(
                        message=f"Cannot read local variable '{name.lexeme}' in its own initializer.",
                        line=name.line,
                        column=name.column,
                        filename=self.filename,
                    )
                self._resolve_local(expr, name)

            case AssignExpr(name=name, value=val):
                self._resolve_expr(val)
                self._resolve_local(expr, name)

            case BinaryExpr(left=l, right=r):
                self._resolve_expr(l)
                self._resolve_expr(r)

            case LogicalExpr(left=l, right=r):
                self._resolve_expr(l)
                self._resolve_expr(r)

            case UnaryExpr(operand=operand):
                self._resolve_expr(operand)

            case CallExpr(callee=callee, arguments=args):
                self._resolve_expr(callee)
                for arg in args:
                    self._resolve_expr(arg)

            case ArrayExpr(elements=elems):
                for elem in elems:
                    self._resolve_expr(elem)

            case IndexExpr(obj=obj, index=idx):
                self._resolve_expr(obj)
                self._resolve_expr(idx)

            case IndexSetExpr(obj=obj, index=idx, value=val):
                self._resolve_expr(obj)
                self._resolve_expr(idx)
                self._resolve_expr(val)

            case FieldAccessExpr(obj=obj):
                self._resolve_expr(obj)

            case FieldSetExpr(obj=obj, value=val):
                self._resolve_expr(obj)
                self._resolve_expr(val)

            case StructLiteralExpr(fields=fields):
                for _, fval in fields:
                    self._resolve_expr(fval)

            case MatchExpr(scrutinee=scr, arms=arms):
                self._resolve_expr(scr)
                for arm in arms:
                    self._begin_scope()
                    self._resolve_pattern(arm.pattern)
                    if arm.guard:
                        self._resolve_expr(arm.guard)
                    self._resolve_expr(arm.body)
                    self._end_scope()

            case LambdaExpr(params=params, body=body):
                self._resolve_function(params, body, FunctionType.LAMBDA)

            case LiteralExpr():
                pass

            case ThisExpr(keyword=keyword):
                if self.current_class == ClassType.NONE:
                    raise FreshSyntaxError(
                        message="Cannot use 'this' outside of a class.",
                        line=keyword.line,
                        column=keyword.column,
                        filename=self.filename,
                    )
                self._resolve_local(expr, keyword)

            case SuperExpr(keyword=keyword):
                if self.current_class == ClassType.NONE:
                    raise FreshSyntaxError(
                        message="Cannot use 'super' outside of a class.",
                        line=keyword.line,
                        column=keyword.column,
                        filename=self.filename,
                    )
                elif self.current_class != ClassType.SUBCLASS:
                    raise FreshSyntaxError(
                        message="Cannot use 'super' in a class with no superclass.",
                        line=keyword.line,
                        column=keyword.column,
                        filename=self.filename,
                    )
                self._resolve_local(expr, keyword)

    def _resolve_pattern(self, pattern: object) -> None:
        match pattern:
            case VariablePattern(name=name):
                self._declare(name)
                self._define(name)
            case StructPattern(field_patterns=fps):
                for _, pat in fps:
                    self._resolve_pattern(pat)
            case LiteralPattern() | WildcardPattern():
                pass

    # ── Helpers ───────────────────────────────────────────────

    def _resolve_function(
        self,
        params: list,
        body: list[Stmt],
        func_type: FunctionType,
    ) -> None:
        enclosing_func = self.current_function
        enclosing_loop_depth = self.loop_depth
        self.current_function = func_type
        self.loop_depth = 0

        self._begin_scope()
        for param in params:
            self._declare(param.name)
            self._define(param.name)

        for stmt in body:
            self._resolve_stmt(stmt)

        self._end_scope()
        self.loop_depth = enclosing_loop_depth
        self.current_function = enclosing_func

    def _begin_scope(self) -> None:
        self.scopes.append({})

    def _end_scope(self) -> None:
        self.scopes.pop()

    def _declare(self, name: Token) -> None:
        if not self.scopes:
            return
        scope = self.scopes[-1]
        if name.lexeme in scope:
            raise FreshNameError(
                message=f"Variable '{name.lexeme}' already declared in this scope.",
                line=name.line,
                column=name.column,
                filename=self.filename,
            )
        scope[name.lexeme] = False

    def _define(self, name: Token) -> None:
        if not self.scopes:
            return
        self.scopes[-1][name.lexeme] = True

    def _resolve_local(self, expr: Expr, name: Token) -> None:
        for i in range(len(self.scopes) - 1, -1, -1):
            if name.lexeme in self.scopes[i]:
                depth = len(self.scopes) - 1 - i
                self.locals[id(expr)] = depth
                return

        raise FreshNameError(
            message=f"Undefined variable '{name.lexeme}'.",
            line=name.line,
            column=name.column,
            filename=self.filename,
        )
