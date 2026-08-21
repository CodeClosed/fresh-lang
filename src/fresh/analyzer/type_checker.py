"""Type checker and local type inferrer for Fresh.

Validates semantic type rules:
  - Operands for binary/unary operations match
  - Variable initializers match declared/inferred type
  - Function parameters and return values match type annotations
  - Struct instantiation and field access match defined struct schemas
  - Array elements have homogenous types
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from fresh.analyzer.symbols import Scope, Symbol
from fresh.common.errors import FreshTypeError
from fresh.common.types import (
    FreshAny,
    FreshArray,
    FreshBool,
    FreshFloat,
    FreshFunction,
    FreshInt,
    FreshNil,
    FreshString,
    FreshStruct,
    FreshType,
)
from fresh.lexer.tokens import TokenType
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
    Node,
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

if TYPE_CHECKING:
    pass


@dataclass(slots=True)
class TypedProgram:
    """Canonical Typed Intermediate Representation (IR) produced by TypeChecker."""

    statements: list[Stmt]
    node_types: dict[int, FreshType]
    struct_defs: dict[str, FreshStruct]

    def get_type(self, node: Node) -> FreshType | None:
        return self.node_types.get(id(node))


class TypeChecker:
    """Passes over AST to enforce type rules and infer types."""

    def __init__(self, filename: str = "<stdin>") -> None:
        self.filename = filename
        self.current_scope: Scope = Scope(depth=0)
        self.struct_defs: dict[str, FreshStruct] = {}
        self.current_return_type: FreshType | None = None
        self.node_types: dict[int, FreshType] = {}

    def check_program(self, statements: list[Stmt]) -> TypedProgram:
        """Type check a full program and return canonical TypedProgram IR."""
        self.node_types.clear()
        for stmt in statements:
            self._check_stmt(stmt)

        return TypedProgram(
            statements=statements,
            node_types=dict(self.node_types),
            struct_defs=dict(self.struct_defs),
        )

    # ── Statement Type Checking ───────────────────────────────

    def _check_stmt(self, stmt: Stmt) -> None:
        match stmt:
            case VarDeclStmt(name=name, type_annotation=ta, initializer=init):
                init_type = self._check_expr(init)
                declared_type = self._resolve_type_annotation(ta) if ta else None

                if declared_type:
                    if not self._types_compatible(declared_type, init_type):
                        raise FreshTypeError(
                            message=f"Cannot initialize variable '{name.lexeme}' of type '{declared_type}' with value of type '{init_type}'.",
                            line=name.line,
                            column=name.column,
                            filename=self.filename,
                        )
                    final_type = declared_type
                else:
                    final_type = init_type

                symbol = Symbol(name=name.lexeme, type=final_type, is_defined=True)
                self.current_scope.define(name.lexeme, symbol)

            case StructDeclStmt(name=name, fields=fields):
                field_dict: dict[str, FreshType] = {}
                for f in fields:
                    field_dict[f.name.lexeme] = self._resolve_type_annotation(f.type_annotation)

                struct_type = FreshStruct(name=name.lexeme, fields=field_dict)
                self.struct_defs[name.lexeme] = struct_type
                symbol = Symbol(name=name.lexeme, type=struct_type, is_defined=True)
                self.current_scope.define(name.lexeme, symbol)

            case FnDeclStmt(name=name, params=params, return_type=rt, body=body):
                param_types = [self._resolve_type_annotation(p.type_annotation) for p in params]
                ret_type = self._resolve_type_annotation(rt) if rt else FreshNil()

                fn_type = FreshFunction(param_types=param_types, return_type=ret_type)
                self.current_scope.define(name.lexeme, Symbol(name=name.lexeme, type=fn_type, is_defined=True))

                self._push_scope()
                for p, ptype in zip(params, param_types):
                    self.current_scope.define(p.name.lexeme, Symbol(name=p.name.lexeme, type=ptype, is_defined=True))

                old_ret = self.current_return_type
                self.current_return_type = ret_type
                for s in body:
                    self._check_stmt(s)
                self.current_return_type = old_ret
                self._pop_scope()

            case BlockStmt(statements=stmts):
                self._push_scope()
                for s in stmts:
                    self._check_stmt(s)
                self._pop_scope()

            case ExprStmt(expression=expr):
                self._check_expr(expr)

            case IfStmt(condition=cond, then_branch=then_b, else_branch=else_b):
                cond_type = self._check_expr(cond)
                if not isinstance(cond_type, (FreshBool, FreshAny)):
                    raise FreshTypeError(
                        message=f"If condition must be a boolean, got '{cond_type}'.",
                        line=0,
                        column=0,
                        filename=self.filename,
                    )
                self._push_scope()
                for s in then_b:
                    self._check_stmt(s)
                self._pop_scope()

                if else_b:
                    self._push_scope()
                    for s in else_b:
                        self._check_stmt(s)
                    self._pop_scope()

            case WhileStmt(condition=cond, body=body):
                cond_type = self._check_expr(cond)
                if not isinstance(cond_type, (FreshBool, FreshAny)):
                    raise FreshTypeError(
                        message=f"While condition must be a boolean, got '{cond_type}'.",
                        line=0,
                        column=0,
                        filename=self.filename,
                    )
                self._push_scope()
                for s in body:
                    self._check_stmt(s)
                self._pop_scope()

            case ForStmt(initializer=init, condition=cond, increment=inc, body=body):
                self._push_scope()
                if init:
                    self._check_stmt(init)
                if cond:
                    cond_type = self._check_expr(cond)
                    if not isinstance(cond_type, (FreshBool, FreshAny)):
                        raise FreshTypeError(
                            message=f"For loop condition must be a boolean, got '{cond_type}'.",
                            line=0,
                            column=0,
                            filename=self.filename,
                        )
                if inc:
                    self._check_expr(inc)

                for s in body:
                    self._check_stmt(s)
                self._pop_scope()

            case ReturnStmt(keyword=keyword, value=val):
                val_type = self._check_expr(val) if val else FreshNil()
                if self.current_return_type:
                    if not self._types_compatible(self.current_return_type, val_type):
                        raise FreshTypeError(
                            message=f"Function expected return type '{self.current_return_type}', got '{val_type}'.",
                            line=keyword.line,
                            column=keyword.column,
                            filename=self.filename,
                        )

            case BreakStmt() | ContinueStmt() | ImportStmt():
                pass


    def _check_expr(self, expr: Expr) -> FreshType:
        res = self._check_expr_inner(expr)
        self.node_types[id(expr)] = res
        return res

    def _check_expr_inner(self, expr: Expr) -> FreshType:
        match expr:
            case LiteralExpr(value=val):
                if isinstance(val, int) and not isinstance(val, bool):
                    return FreshInt()
                if isinstance(val, float):
                    return FreshFloat()
                if isinstance(val, bool):
                    return FreshBool()
                if isinstance(val, str):
                    return FreshString()
                if val is None:
                    return FreshNil()
                return FreshAny()

            case VariableExpr(name=name):
                sym = self.current_scope.lookup_chain(name.lexeme)
                if sym and sym.type:
                    return sym.type
                return FreshAny()

            case AssignExpr(name=name, value=val):
                val_type = self._check_expr(val)
                sym = self.current_scope.lookup_chain(name.lexeme)
                if sym and sym.type:
                    if not self._types_compatible(sym.type, val_type):
                        raise FreshTypeError(
                            message=f"Cannot assign value of type '{val_type}' to variable '{name.lexeme}' of type '{sym.type}'.",
                            line=name.line,
                            column=name.column,
                            filename=self.filename,
                        )
                return val_type

            case BinaryExpr(left=l, operator=op, right=r):
                l_type = self._check_expr(l)
                r_type = self._check_expr(r)

                if op.type in (TokenType.PLUS, TokenType.MINUS, TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
                    if isinstance(l_type, FreshInt) and isinstance(r_type, FreshInt):
                        return FreshInt()
                    if isinstance(l_type, (FreshInt, FreshFloat)) and isinstance(r_type, (FreshInt, FreshFloat)):
                        return FreshFloat()
                    if op.type == TokenType.PLUS and isinstance(l_type, FreshString) and isinstance(r_type, FreshString):
                        return FreshString()
                    if isinstance(l_type, FreshAny) or isinstance(r_type, FreshAny):
                        return FreshAny()
                    raise FreshTypeError(
                        message=f"Operator '{op.lexeme}' not supported between '{l_type}' and '{r_type}'.",
                        line=op.line,
                        column=op.column,
                        filename=self.filename,
                    )

                if op.type in (TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL):
                    return FreshBool()

                if op.type in (TokenType.LESS, TokenType.LESS_EQUAL, TokenType.GREATER, TokenType.GREATER_EQUAL):
                    if isinstance(l_type, (FreshInt, FreshFloat, FreshAny)) and isinstance(r_type, (FreshInt, FreshFloat, FreshAny)):
                        return FreshBool()
                    raise FreshTypeError(
                        message=f"Comparison '{op.lexeme}' requires numeric types, got '{l_type}' and '{r_type}'.",
                        line=op.line,
                        column=op.column,
                        filename=self.filename,
                    )

                return FreshAny()

            case LogicalExpr(left=l, operator=op, right=r):
                l_type = self._check_expr(l)
                r_type = self._check_expr(r)
                if not isinstance(l_type, (FreshBool, FreshAny)) or not isinstance(r_type, (FreshBool, FreshAny)):
                    raise FreshTypeError(
                        message=f"Logical operator '{op.lexeme}' requires boolean operands.",
                        line=op.line,
                        column=op.column,
                        filename=self.filename,
                    )
                return FreshBool()

            case UnaryExpr(operator=op, operand=operand):
                op_type = self._check_expr(operand)
                if op.type == TokenType.MINUS:
                    if isinstance(op_type, FreshInt):
                        return FreshInt()
                    if isinstance(op_type, FreshFloat):
                        return FreshFloat()
                    if isinstance(op_type, FreshAny):
                        return FreshAny()
                    raise FreshTypeError(
                        message=f"Unary '-' requires numeric operand, got '{op_type}'.",
                        line=op.line,
                        column=op.column,
                        filename=self.filename,
                    )
                if op.type == TokenType.BANG:
                    if isinstance(op_type, (FreshBool, FreshAny)):
                        return FreshBool()
                    raise FreshTypeError(
                        message=f"Unary '!' requires boolean operand, got '{op_type}'.",
                        line=op.line,
                        column=op.column,
                        filename=self.filename,
                    )
                return FreshAny()

            case CallExpr(callee=callee, paren=paren, arguments=args):
                callee_type = self._check_expr(callee)
                arg_types = [self._check_expr(a) for a in args]

                if isinstance(callee_type, FreshFunction):
                    if callee_type.param_types is not None:
                        if len(arg_types) != len(callee_type.param_types):
                            raise FreshTypeError(
                                message=f"Expected {len(callee_type.param_types)} arguments but got {len(arg_types)}.",
                                line=paren.line,
                                column=paren.column,
                                filename=self.filename,
                            )
                        for i, (expected, actual) in enumerate(zip(callee_type.param_types, arg_types)):
                            if not self._types_compatible(expected, actual):
                                raise FreshTypeError(
                                    message=f"Argument {i+1} expected '{expected}', got '{actual}'.",
                                    line=paren.line,
                                    column=paren.column,
                                    filename=self.filename,
                                )
                    return callee_type.return_type or FreshAny()


                if isinstance(callee_type, FreshAny):
                    return FreshAny()

                raise FreshTypeError(
                    message=f"Cannot call non-function type '{callee_type}'.",
                    line=paren.line,
                    column=paren.column,
                    filename=self.filename,
                )

            case ArrayExpr(bracket=bracket, elements=elems):
                if not elems:
                    return FreshArray(element_type=FreshAny())
                first_type = self._check_expr(elems[0])
                for elem in elems[1:]:
                    etype = self._check_expr(elem)
                    if not self._types_compatible(first_type, etype):
                        raise FreshTypeError(
                            message=f"Array element type mismatch: expected '{first_type}', got '{etype}'.",
                            line=bracket.line,
                            column=bracket.column,
                            filename=self.filename,
                        )
                return FreshArray(element_type=first_type)

            case IndexExpr(obj=obj, bracket=bracket, index=idx):
                obj_type = self._check_expr(obj)
                idx_type = self._check_expr(idx)

                if not isinstance(idx_type, (FreshInt, FreshAny)):
                    raise FreshTypeError(
                        message=f"Array index must be an integer, got '{idx_type}'.",
                        line=bracket.line,
                        column=bracket.column,
                        filename=self.filename,
                    )

                if isinstance(obj_type, FreshArray):
                    return obj_type.element_type
                if isinstance(obj_type, FreshString):
                    return FreshString()
                if isinstance(obj_type, FreshAny):
                    return FreshAny()

                raise FreshTypeError(
                    message=f"Cannot index non-array/string type '{obj_type}'.",
                    line=bracket.line,
                    column=bracket.column,
                    filename=self.filename,
                )

            case IndexSetExpr(obj=obj, bracket=bracket, index=idx, value=val):
                obj_type = self._check_expr(obj)
                idx_type = self._check_expr(idx)
                val_type = self._check_expr(val)

                if not isinstance(idx_type, (FreshInt, FreshAny)):
                    raise FreshTypeError(
                        message=f"Array index must be an integer, got '{idx_type}'.",
                        line=bracket.line,
                        column=bracket.column,
                        filename=self.filename,
                    )

                if isinstance(obj_type, FreshArray):
                    if not self._types_compatible(obj_type.element_type, val_type):
                        raise FreshTypeError(
                            message=f"Cannot assign '{val_type}' to array of '{obj_type.element_type}'.",
                            line=bracket.line,
                            column=bracket.column,
                            filename=self.filename,
                        )
                    return val_type

                return FreshAny()

            case FieldAccessExpr(obj=obj, name=name):
                obj_type = self._check_expr(obj)
                if isinstance(obj_type, FreshStruct):
                    if name.lexeme not in obj_type.fields:
                        raise FreshTypeError(
                            message=f"Struct '{obj_type.name}' has no field '{name.lexeme}'.",
                            line=name.line,
                            column=name.column,
                            filename=self.filename,
                        )
                    return obj_type.fields[name.lexeme]
                if isinstance(obj_type, FreshAny):
                    return FreshAny()
                raise FreshTypeError(
                    message=f"Type '{obj_type}' has no fields.",
                    line=name.line,
                    column=name.column,
                    filename=self.filename,
                )

            case FieldSetExpr(obj=obj, name=name, value=val):
                obj_type = self._check_expr(obj)
                val_type = self._check_expr(val)
                if isinstance(obj_type, FreshStruct):
                    if name.lexeme not in obj_type.fields:
                        raise FreshTypeError(
                            message=f"Struct '{obj_type.name}' has no field '{name.lexeme}'.",
                            line=name.line,
                            column=name.column,
                            filename=self.filename,
                        )
                    field_type = obj_type.fields[name.lexeme]
                    if not self._types_compatible(field_type, val_type):
                        raise FreshTypeError(
                            message=f"Cannot assign '{val_type}' to field '{name.lexeme}' of type '{field_type}'.",
                            line=name.line,
                            column=name.column,
                            filename=self.filename,
                        )
                    return val_type
                return FreshAny()

            case StructLiteralExpr(name=name, fields=fields):
                struct_def = self.struct_defs.get(name.lexeme)
                if not struct_def:
                    raise FreshTypeError(
                        message=f"Undefined struct '{name.lexeme}'.",
                        line=name.line,
                        column=name.column,
                        filename=self.filename,
                    )
                provided_fields = {fname.lexeme: self._check_expr(fval) for fname, fval in fields}
                for fname, ftype in struct_def.fields.items():
                    if fname not in provided_fields:
                        raise FreshTypeError(
                            message=f"Missing field '{fname}' in struct '{name.lexeme}' instantiation.",
                            line=name.line,
                            column=name.column,
                            filename=self.filename,
                        )
                    provided_type = provided_fields[fname]
                    if not self._types_compatible(ftype, provided_type):
                        raise FreshTypeError(
                            message=f"Field '{fname}' expected '{ftype}', got '{provided_type}'.",
                            line=name.line,
                            column=name.column,
                            filename=self.filename,
                        )
                return struct_def

            case MatchExpr(scrutinee=scr, arms=arms):
                scr_type = self._check_expr(scr)
                body_types: list[FreshType] = []
                for arm in arms:
                    self._push_scope()
                    self._check_pattern(arm.pattern, scr_type)
                    if arm.guard:
                        gtype = self._check_expr(arm.guard)
                        if not isinstance(gtype, (FreshBool, FreshAny)):
                            raise FreshTypeError(
                                message=f"Match guard must be a boolean, got '{gtype}'.",
                                line=0,
                                column=0,
                                filename=self.filename,
                            )
                    body_types.append(self._check_expr(arm.body))
                    self._pop_scope()

                return body_types[0] if body_types else FreshNil()

            case LambdaExpr(params=params, return_type=rt, body=body):
                param_types = [self._resolve_type_annotation(p.type_annotation) for p in params]
                ret_type = self._resolve_type_annotation(rt) if rt else FreshNil()
                self._push_scope()
                for p, ptype in zip(params, param_types):
                    self.current_scope.define(p.name.lexeme, Symbol(name=p.name.lexeme, type=ptype, is_defined=True))

                old_ret = self.current_return_type
                self.current_return_type = ret_type
                for s in body:
                    self._check_stmt(s)
                self.current_return_type = old_ret
                self._pop_scope()
                return FreshFunction(param_types=param_types, return_type=ret_type)

            case _:
                return FreshAny()

    def _check_pattern(self, pattern: object, expected_type: FreshType) -> None:
        match pattern:
            case VariablePattern(name=name):
                self.current_scope.define(name.lexeme, Symbol(name=name.lexeme, type=expected_type, is_defined=True))
            case LiteralPattern():
                pass
            case StructPattern(name=name, field_patterns=fps):
                struct_def = self.struct_defs.get(name.lexeme)
                if struct_def:
                    for fname_tok, pat in fps:
                        ftype = struct_def.fields.get(fname_tok.lexeme, FreshAny())
                        self._check_pattern(pat, ftype)
            case WildcardPattern():
                pass

    # ── Helpers ───────────────────────────────────────────────

    def _resolve_type_annotation(self, ta: TypeAnnotation) -> FreshType:
        if ta.element_type is not None:
            return FreshArray(element_type=self._resolve_type_annotation(ta.element_type))

        tname = ta.name.lexeme
        match tname:
            case "int":
                return FreshInt()
            case "float":
                return FreshFloat()
            case "bool":
                return FreshBool()
            case "string":
                return FreshString()
            case "fn":
                return FreshFunction()
            case _:
                if tname in self.struct_defs:
                    return self.struct_defs[tname]
                return FreshAny()

    def _types_compatible(self, expected: FreshType, actual: FreshType) -> bool:
        if isinstance(expected, FreshAny) or isinstance(actual, FreshAny):
            return True
        if isinstance(expected, FreshFloat) and isinstance(actual, FreshInt):
            return True  # Auto coercion int -> float
        return expected == actual

    def _push_scope(self) -> None:
        self.current_scope = Scope(depth=self.current_scope.depth + 1, parent=self.current_scope)

    def _pop_scope(self) -> None:
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent
