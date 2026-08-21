"""Abstract Syntax Tree node definitions for the Fresh language.

All AST nodes use @dataclass(slots=True) for minimal memory footprint.
Nodes are divided into three families:

  - **Expressions** (subclass Expr): produce values
  - **Statements** (subclass Stmt): perform actions
  - **Patterns** (subclass Pattern): used in match expressions

An ASTPrinter utility is included for the --dump-ast CLI flag.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fresh.lexer.tokens import Token


# ── Base Classes ──────────────────────────────────────────────


class Node:
    """Base class for all AST nodes."""

    pass


class Expr(Node):
    """Base class for expression nodes (produce values)."""

    pass


class Stmt(Node):
    """Base class for statement nodes (perform actions)."""

    pass


class Pattern(Node):
    """Base class for pattern nodes (used in match expressions)."""

    pass


# ── Type Annotations ─────────────────────────────────────────


@dataclass(slots=True)
class TypeAnnotation:
    """A type annotation in source code.

    Basic types:  int, float, bool, string
    Array types:  [int], [string], [[int]]
    Custom types: Point, Node, etc.
    """

    name: "Token"
    element_type: TypeAnnotation | None = None  # For array types: [element_type]


# ── Helper Types ──────────────────────────────────────────────


@dataclass(slots=True)
class Parameter:
    """A function parameter declaration: name: type."""

    name: "Token"
    type_annotation: TypeAnnotation


@dataclass(slots=True)
class StructField:
    """A struct field declaration: name: type."""

    name: "Token"
    type_annotation: TypeAnnotation


# ── Expression Nodes ──────────────────────────────────────────


@dataclass(slots=True)
class LiteralExpr(Expr):
    """A literal value: 42, 3.14, "hello", true, false, nil."""

    value: object
    token: "Token"


@dataclass(slots=True)
class VariableExpr(Expr):
    """A variable reference: foo, bar, my_var."""

    name: "Token"


@dataclass(slots=True)
class AssignExpr(Expr):
    """Variable assignment: x = expr."""

    name: "Token"
    value: Expr


@dataclass(slots=True)
class BinaryExpr(Expr):
    """Binary operation: left op right."""

    left: Expr
    operator: "Token"
    right: Expr


@dataclass(slots=True)
class LogicalExpr(Expr):
    """Logical operation with short-circuit: left && right, left || right."""

    left: Expr
    operator: "Token"
    right: Expr


@dataclass(slots=True)
class UnaryExpr(Expr):
    """Unary operation: -expr, !expr."""

    operator: "Token"
    operand: Expr


@dataclass(slots=True)
class CallExpr(Expr):
    """Function call: callee(arg1, arg2, ...)."""

    callee: Expr
    paren: "Token"  # The '(' token, for error location
    arguments: list[Expr]


@dataclass(slots=True)
class ArrayExpr(Expr):
    """Array literal: [1, 2, 3]."""

    bracket: "Token"
    elements: list[Expr]


@dataclass(slots=True)
class IndexExpr(Expr):
    """Array/string index access: obj[index]."""

    obj: Expr
    bracket: "Token"
    index: Expr


@dataclass(slots=True)
class IndexSetExpr(Expr):
    """Array index assignment: obj[index] = value."""

    obj: Expr
    bracket: "Token"
    index: Expr
    value: Expr


@dataclass(slots=True)
class FieldAccessExpr(Expr):
    """Struct field access: obj.field."""

    obj: Expr
    name: "Token"


@dataclass(slots=True)
class FieldSetExpr(Expr):
    """Struct field assignment: obj.field = value."""

    obj: Expr
    name: "Token"
    value: Expr


@dataclass(slots=True)
class StructLiteralExpr(Expr):
    """Struct instantiation: Point { x: 1.0, y: 2.0 }."""

    name: "Token"
    fields: list[tuple["Token", Expr]]


@dataclass(slots=True)
class MatchExpr(Expr):
    """Match expression: match scrutinee { pattern => body, ... }."""

    keyword: "Token"
    scrutinee: Expr
    arms: list["MatchArm"]


@dataclass(slots=True)
class LambdaExpr(Expr):
    """Anonymous function: fn(x: int, y: int) -> int { return x + y; }."""

    keyword: "Token"
    params: list[Parameter]
    return_type: TypeAnnotation | None
    body: list[Stmt]


# ── Statement Nodes ───────────────────────────────────────────


@dataclass(slots=True)
class ExprStmt(Stmt):
    """Expression used as a statement: expr;"""

    expression: Expr


@dataclass(slots=True)
class VarDeclStmt(Stmt):
    """Variable declaration: let name [: type] = expr;"""

    name: "Token"
    type_annotation: TypeAnnotation | None
    initializer: Expr


@dataclass(slots=True)
class FnDeclStmt(Stmt):
    """Function declaration: fn name(params) [-> type] { body }."""

    name: "Token"
    params: list[Parameter]
    return_type: TypeAnnotation | None
    body: list[Stmt]


@dataclass(slots=True)
class StructDeclStmt(Stmt):
    """Struct declaration: struct Name { field: type, ... }."""

    name: "Token"
    fields: list[StructField]


@dataclass(slots=True)
class IfStmt(Stmt):
    """If statement: if (condition) { ... } [else { ... }]."""

    keyword: "Token"
    condition: Expr
    then_branch: list[Stmt]
    else_branch: list[Stmt] | None  # None = no else; [IfStmt] = else-if chain


@dataclass(slots=True)
class WhileStmt(Stmt):
    """While loop: while (condition) { body }."""

    keyword: "Token"
    condition: Expr
    body: list[Stmt]


@dataclass(slots=True)
class ForStmt(Stmt):
    """C-style for loop: for (init; condition; increment) { body }."""

    keyword: "Token"
    initializer: Stmt | None
    condition: Expr | None
    increment: Expr | None
    body: list[Stmt]


@dataclass(slots=True)
class ReturnStmt(Stmt):
    """Return statement: return [expr];"""

    keyword: "Token"
    value: Expr | None


@dataclass(slots=True)
class BreakStmt(Stmt):
    """Break statement: break;"""

    keyword: "Token"


@dataclass(slots=True)
class ContinueStmt(Stmt):
    """Continue statement: continue;"""

    keyword: "Token"


@dataclass(slots=True)
class BlockStmt(Stmt):
    """Block of statements: { stmt1; stmt2; ... }."""

    statements: list[Stmt]


@dataclass(slots=True)
class ImportStmt(Stmt):
    """Import statement: import math; or import "path.fresh";"""

    keyword: "Token"
    module_token: "Token"


# ── Pattern Nodes ─────────────────────────────────────────────



@dataclass(slots=True)
class LiteralPattern(Pattern):
    """Match against a literal value: 0, "hello", true."""

    value: object
    token: "Token"


@dataclass(slots=True)
class VariablePattern(Pattern):
    """Bind the matched value to a variable: x."""

    name: "Token"


@dataclass(slots=True)
class WildcardPattern(Pattern):
    """Match anything and discard: _."""

    token: "Token"


@dataclass(slots=True)
class StructPattern(Pattern):
    """Match a struct: Point { x: px, y: py }."""

    name: "Token"
    field_patterns: list[tuple["Token", Pattern]]


# ── Match Arm ─────────────────────────────────────────────────


@dataclass(slots=True)
class MatchArm:
    """A single arm in a match expression: pattern [if guard] => body."""

    pattern: Pattern
    guard: Expr | None
    body: Expr


# ── AST Pretty Printer ───────────────────────────────────────


class ASTPrinter:
    """Pretty-prints an AST tree for debugging (--dump-ast flag).

    Usage:
        printer = ASTPrinter()
        print(printer.print_program(statements))
    """

    def print_program(self, statements: list[Stmt]) -> str:
        """Format a complete program as a readable tree."""
        lines: list[str] = []
        for stmt in statements:
            lines.append(self._stmt(stmt, indent=0))
        return "\n".join(lines)

    # ── Statement Formatting ──────────────────────────────────

    def _stmt(self, stmt: Stmt, indent: int) -> str:
        pad = "  " * indent

        match stmt:
            case VarDeclStmt(name=name, type_annotation=ta, initializer=init):
                type_str = f": {self._type(ta)}" if ta else ""
                return f"{pad}VarDecl {name.lexeme}{type_str} = {self._expr(init)}"

            case FnDeclStmt(name=name, params=params, return_type=rt, body=body):
                params_str = ", ".join(
                    f"{p.name.lexeme}: {self._type(p.type_annotation)}"
                    for p in params
                )
                ret = f" -> {self._type(rt)}" if rt else ""
                header = f"{pad}FnDecl {name.lexeme}({params_str}){ret}"
                body_lines = [self._stmt(s, indent + 1) for s in body]
                return header + "\n" + "\n".join(body_lines) if body_lines else header

            case StructDeclStmt(name=name, fields=fields):
                flds = ", ".join(
                    f"{f.name.lexeme}: {self._type(f.type_annotation)}"
                    for f in fields
                )
                return f"{pad}StructDecl {name.lexeme} {{ {flds} }}"

            case IfStmt(condition=cond, then_branch=then_b, else_branch=else_b):
                result = f"{pad}If ({self._expr(cond)})\n"
                result += "\n".join(self._stmt(s, indent + 1) for s in then_b)
                if else_b is not None:
                    result += f"\n{pad}Else\n"
                    result += "\n".join(self._stmt(s, indent + 1) for s in else_b)
                return result

            case WhileStmt(condition=cond, body=body):
                result = f"{pad}While ({self._expr(cond)})\n"
                result += "\n".join(self._stmt(s, indent + 1) for s in body)
                return result

            case ForStmt(initializer=init, condition=cond, increment=inc, body=body):
                init_s = self._stmt(init, 0).strip() if init else ""
                cond_s = self._expr(cond) if cond else ""
                inc_s = self._expr(inc) if inc else ""
                result = f"{pad}For ({init_s}; {cond_s}; {inc_s})\n"
                result += "\n".join(self._stmt(s, indent + 1) for s in body)
                return result

            case ReturnStmt(value=val):
                val_s = f" {self._expr(val)}" if val else ""
                return f"{pad}Return{val_s}"

            case BreakStmt():
                return f"{pad}Break"

            case ContinueStmt():
                return f"{pad}Continue"

            case BlockStmt(statements=stmts):
                lines = [self._stmt(s, indent + 1) for s in stmts]
                return f"{pad}Block\n" + "\n".join(lines)

            case ExprStmt(expression=expr):
                return f"{pad}ExprStmt {self._expr(expr)}"

            case ImportStmt(module_token=mod_tok):
                return f"{pad}Import {mod_tok.lexeme}"

            case _:
                return f"{pad}<unknown stmt: {type(stmt).__name__}>"


    # ── Expression Formatting ─────────────────────────────────

    def _expr(self, expr: Expr) -> str:
        match expr:
            case LiteralExpr(value=val):
                return repr(val)

            case VariableExpr(name=name):
                return name.lexeme

            case AssignExpr(name=name, value=val):
                return f"({name.lexeme} = {self._expr(val)})"

            case BinaryExpr(left=l, operator=op, right=r):
                return f"({self._expr(l)} {op.lexeme} {self._expr(r)})"

            case LogicalExpr(left=l, operator=op, right=r):
                return f"({self._expr(l)} {op.lexeme} {self._expr(r)})"

            case UnaryExpr(operator=op, operand=operand):
                return f"({op.lexeme}{self._expr(operand)})"

            case CallExpr(callee=callee, arguments=args):
                args_s = ", ".join(self._expr(a) for a in args)
                return f"{self._expr(callee)}({args_s})"

            case ArrayExpr(elements=elems):
                return f"[{', '.join(self._expr(e) for e in elems)}]"

            case IndexExpr(obj=obj, index=idx):
                return f"{self._expr(obj)}[{self._expr(idx)}]"

            case IndexSetExpr(obj=obj, index=idx, value=val):
                return f"({self._expr(obj)}[{self._expr(idx)}] = {self._expr(val)})"

            case FieldAccessExpr(obj=obj, name=name):
                return f"{self._expr(obj)}.{name.lexeme}"

            case FieldSetExpr(obj=obj, name=name, value=val):
                return f"({self._expr(obj)}.{name.lexeme} = {self._expr(val)})"

            case StructLiteralExpr(name=name, fields=fields):
                flds = ", ".join(
                    f"{f[0].lexeme}: {self._expr(f[1])}" for f in fields
                )
                return f"{name.lexeme} {{ {flds} }}"

            case MatchExpr(scrutinee=scr, arms=arms):
                arm_strs: list[str] = []
                for a in arms:
                    s = self._pattern(a.pattern)
                    if a.guard is not None:
                        s += f" if {self._expr(a.guard)}"
                    s += f" => {self._expr(a.body)}"
                    arm_strs.append(s)
                return f"match {self._expr(scr)} {{ {', '.join(arm_strs)} }}"

            case LambdaExpr(params=params):
                ps = ", ".join(p.name.lexeme for p in params)
                return f"fn({ps}) {{ ... }}"

            case _:
                return f"<unknown expr: {type(expr).__name__}>"

    # ── Pattern Formatting ────────────────────────────────────

    def _pattern(self, pattern: Pattern) -> str:
        match pattern:
            case LiteralPattern(value=val):
                return repr(val)

            case VariablePattern(name=name):
                return name.lexeme

            case WildcardPattern():
                return "_"

            case StructPattern(name=name, field_patterns=fps):
                fps_s = ", ".join(
                    f"{fp[0].lexeme}: {self._pattern(fp[1])}" for fp in fps
                )
                return f"{name.lexeme} {{ {fps_s} }}"

            case _:
                return f"<unknown pattern: {type(pattern).__name__}>"

    # ── Type Formatting ───────────────────────────────────────

    def _type(self, ta: TypeAnnotation) -> str:
        if ta.element_type is not None:
            return f"[{self._type(ta.element_type)}]"
        return ta.name.lexeme
