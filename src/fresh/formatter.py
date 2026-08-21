"""Deterministic AST-based Code Formatter for Fresh.

Formats Fresh source code into standardized, readable syntax.
Ensures idempotence: format(format(code)) == format(code).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fresh.lexer.scanner import Scanner
from fresh.parser.ast import (
    ArrayExpr,
    AssignExpr,
    BinaryExpr,
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
    LiteralPattern,
    LogicalExpr,
    MatchExpr,
    ReturnStmt,
    Stmt,
    StructDeclStmt,
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
from fresh.parser.parser import Parser

if TYPE_CHECKING:
    from fresh.parser.ast import Pattern


class FreshFormatter:
    """Formats Fresh AST nodes into standard Fresh code strings."""

    def format_source(self, source: str) -> str:
        """Parse source code string and return formatted Fresh code."""
        tokens = Scanner(source).scan_tokens()
        statements = Parser(tokens).parse()
        return self.format_program(statements)

    def format_program(self, statements: list[Stmt]) -> str:
        """Format a list of top-level AST statements."""
        blocks: list[str] = []
        for stmt in statements:
            blocks.append(self._format_stmt(stmt, indent=0))
        return "\n\n".join(blocks) + "\n"

    def _format_stmt(self, stmt: Stmt, indent: int) -> str:
        pad = "    " * indent

        match stmt:
            case VarDeclStmt(name=name, type_annotation=ta, initializer=init):
                type_s = f": {self._format_type(ta)}" if ta else ""
                return f"{pad}let {name.lexeme}{type_s} = {self._format_expr(init)};"

            case FnDeclStmt(name=name, params=params, return_type=rt, body=body):
                param_strs = [
                    f"{p.name.lexeme}: {self._format_type(p.type_annotation)}"
                    for p in params
                ]
                params_s = ", ".join(param_strs)
                ret_s = f" -> {self._format_type(rt)}" if rt else ""
                header = f"{pad}fn {name.lexeme}({params_s}){ret_s} {{"
                if not body:
                    return f"{header} }}"
                body_lines = [self._format_stmt(s, indent + 1) for s in body]
                return header + "\n" + "\n".join(body_lines) + f"\n{pad}}}"

            case StructDeclStmt(name=name, fields=fields):
                field_strs = [
                    f"{f.name.lexeme}: {self._format_type(f.type_annotation)}"
                    for f in fields
                ]
                fields_s = ", ".join(field_strs)
                return f"{pad}struct {name.lexeme} {{ {fields_s} }}"

            case BlockStmt(statements=stmts):
                if not stmts:
                    return f"{pad}{{}}"
                lines = [self._format_stmt(s, indent + 1) for s in stmts]
                return f"{pad}{{\n" + "\n".join(lines) + f"\n{pad}}}"

            case ExprStmt(expression=expr):
                return f"{pad}{self._format_expr(expr)};"

            case IfStmt(condition=cond, then_branch=then_b, else_branch=else_b):
                res = f"{pad}if ({self._format_expr(cond)}) {{\n"
                res += "\n".join(self._format_stmt(s, indent + 1) for s in then_b)
                res += f"\n{pad}}}"
                if else_b:
                    res += " else {\n"
                    res += "\n".join(self._format_stmt(s, indent + 1) for s in else_b)
                    res += f"\n{pad}}}"
                return res

            case WhileStmt(condition=cond, body=body):
                res = f"{pad}while ({self._format_expr(cond)}) {{\n"
                res += "\n".join(self._format_stmt(s, indent + 1) for s in body)
                res += f"\n{pad}}}"
                return res

            case ForStmt(initializer=init, condition=cond, increment=inc, body=body):
                init_s = self._format_stmt(init, 0).rstrip(";") if init else ""
                cond_s = self._format_expr(cond) if cond else ""
                inc_s = self._format_expr(inc) if inc else ""
                res = f"{pad}for ({init_s}; {cond_s}; {inc_s}) {{\n"
                res += "\n".join(self._format_stmt(s, indent + 1) for s in body)
                res += f"\n{pad}}}"
                return res

            case ReturnStmt(value=val):
                val_s = f" {self._format_expr(val)}" if val else ""
                return f"{pad}return{val_s};"

            case BreakStmt():
                return f"{pad}break;"

            case ContinueStmt():
                return f"{pad}continue;"

            case ImportStmt(module_token=mod):
                return f"{pad}import {mod.lexeme};"

            case _:
                return f"{pad}/* unhandled stmt {type(stmt).__name__} */"


    def _format_expr(self, expr: Expr) -> str:
        match expr:
            case LiteralExpr(value=val):
                if val is True:
                    return "true"
                if val is False:
                    return "false"
                if val is None:
                    return "nil"
                if isinstance(val, str):
                    escaped = val.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
                    return f'"{escaped}"'
                return str(val)

            case VariableExpr(name=name):
                return name.lexeme

            case AssignExpr(name=name, value=val):
                return f"{name.lexeme} = {self._format_expr(val)}"

            case BinaryExpr(left=l, operator=op, right=r):
                return f"{self._format_expr(l)} {op.lexeme} {self._format_expr(r)}"

            case LogicalExpr(left=l, operator=op, right=r):
                return f"{self._format_expr(l)} {op.lexeme} {self._format_expr(r)}"

            case UnaryExpr(operator=op, operand=operand):
                return f"{op.lexeme}{self._format_expr(operand)}"

            case CallExpr(callee=callee, arguments=args):
                args_s = ", ".join(self._format_expr(a) for a in args)
                return f"{self._format_expr(callee)}({args_s})"

            case ArrayExpr(elements=elems):
                elems_s = ", ".join(self._format_expr(e) for e in elems)
                return f"[{elems_s}]"

            case IndexExpr(obj=obj, index=idx):
                return f"{self._format_expr(obj)}[{self._format_expr(idx)}]"

            case IndexSetExpr(obj=obj, index=idx, value=val):
                return f"{self._format_expr(obj)}[{self._format_expr(idx)}] = {self._format_expr(val)}"

            case FieldAccessExpr(obj=obj, name=name):
                return f"{self._format_expr(obj)}.{name.lexeme}"

            case FieldSetExpr(obj=obj, name=name, value=val):
                return f"{self._format_expr(obj)}.{name.lexeme} = {self._format_expr(val)}"

            case StructLiteralExpr(name=name, fields=fields):
                field_inits = ", ".join(
                    f"{f[0].lexeme}: {self._format_expr(f[1])}" for f in fields
                )
                return f"{name.lexeme} {{ {field_inits} }}"

            case MatchExpr(scrutinee=scr, arms=arms):
                arm_strs: list[str] = []
                for arm in arms:
                    pat_s = self._format_pattern(arm.pattern)
                    guard_s = f" if {self._format_expr(arm.guard)}" if arm.guard else ""
                    arm_strs.append(f"{pat_s}{guard_s} => {self._format_expr(arm.body)}")
                arms_s = ", ".join(arm_strs)
                return f"match {self._format_expr(scr)} {{ {arms_s} }}"

            case LambdaExpr(params=params, return_type=rt, body=body):
                param_strs = [
                    f"{p.name.lexeme}: {self._format_type(p.type_annotation)}"
                    for p in params
                ]
                params_s = ", ".join(param_strs)
                ret_s = f" -> {self._format_type(rt)}" if rt else ""
                header = f"fn({params_s}){ret_s} {{"
                body_lines = [self._format_stmt(s, indent=1) for s in body]
                return header + "\n" + "\n".join(body_lines) + "\n}"

            case _:
                return f"/* unhandled expr {type(expr).__name__} */"

    def _format_pattern(self, pattern: Pattern) -> str:
        match pattern:
            case LiteralPattern(value=val):
                if isinstance(val, str):
                    return f'"{val}"'
                if val is True:
                    return "true"
                if val is False:
                    return "false"
                return str(val)

            case VariablePattern(name=name):
                return name.lexeme

            case WildcardPattern():
                return "_"

            case StructPattern(name=name, field_patterns=fps):
                fp_strs = [f"{tok.lexeme}: {self._format_pattern(pat)}" for tok, pat in fps]
                return f"{name.lexeme} {{ {', '.join(fp_strs)} }}"

            case _:
                return "_"

    def _format_type(self, ta: TypeAnnotation) -> str:
        if ta.element_type is not None:
            return f"[{self._format_type(ta.element_type)}]"
        return ta.name.lexeme


FreshFormatter = FreshFormatter
