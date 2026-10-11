"""Type checker and local type inferrer for Fresh.

Validates semantic type rules:
  - Operands for binary/unary operations match
  - Variable initializers match declared/inferred type
  - Function parameters and return values match type annotations
  - Struct instantiation and field access match defined struct schemas
  - Array elements have homogenous types
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from fresh.analyzer.symbols import Scope, Symbol
from fresh.common.errors import FreshTypeError
from fresh.common.types import (
    FreshAny,
    FreshArray,
    FreshBool,
    FreshClass,
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
    Node,
    ReturnStmt,
    Stmt,
    StructDeclStmt,
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

if TYPE_CHECKING:
    pass


@dataclass(slots=True)
class TypedProgram:
    """Canonical Typed Intermediate Representation (IR) produced by TypeChecker."""

    statements: list[Stmt]
    node_types: dict[int, FreshType]
    struct_defs: dict[str, FreshStruct]
    class_defs: dict[str, FreshClass] = field(default_factory=dict)

    def get_type(self, node: Node) -> FreshType | None:
        return self.node_types.get(id(node))


class TypeChecker:
    """Passes over AST to enforce type rules and infer types."""

    def __init__(self, filename: str = "<stdin>") -> None:
        self.filename = filename
        self.current_scope: Scope = Scope(depth=0)
        self.struct_defs: dict[str, FreshStruct] = {}
        self.class_defs: dict[str, FreshClass] = {}
        self.current_class: FreshClass | None = None
        self.current_return_type: FreshType | None = None
        self.node_types: dict[int, FreshType] = {}
        self._init_builtins()

    def _init_builtins(self) -> None:
        """Register built-in function signatures in global scope."""
        builtins: dict[str, FreshFunction] = {
            "print": FreshFunction(param_types=None, return_type=FreshNil()),
            "println": FreshFunction(param_types=None, return_type=FreshNil()),
            "input": FreshFunction(param_types=None, return_type=FreshString()),
            "read_int": FreshFunction(param_types=[], return_type=FreshInt()),
            "len": FreshFunction(param_types=[FreshAny()], return_type=FreshInt()),
            "push": FreshFunction(param_types=[FreshAny(), FreshAny()], return_type=FreshNil()),
            "pop": FreshFunction(param_types=[FreshAny()], return_type=FreshAny()),
            "clock": FreshFunction(param_types=[], return_type=FreshFloat()),
            "type": FreshFunction(param_types=[FreshAny()], return_type=FreshString()),
            "to_string": FreshFunction(param_types=[FreshAny()], return_type=FreshString()),
            "to_int": FreshFunction(param_types=[FreshAny()], return_type=FreshInt()),
            "to_float": FreshFunction(param_types=[FreshAny()], return_type=FreshFloat()),
            "read_file": FreshFunction(param_types=[FreshString()], return_type=FreshString()),
            "write_file": FreshFunction(param_types=[FreshString(), FreshAny()], return_type=FreshBool()),
            "file_exists": FreshFunction(param_types=[FreshString()], return_type=FreshBool()),
            "abs": FreshFunction(param_types=[FreshAny()], return_type=FreshAny()),
            "sqrt": FreshFunction(param_types=[FreshFloat()], return_type=FreshFloat()),
            "pow": FreshFunction(param_types=[FreshFloat(), FreshFloat()], return_type=FreshFloat()),
            "min": FreshFunction(param_types=[FreshAny(), FreshAny()], return_type=FreshAny()),
            "max": FreshFunction(param_types=[FreshAny(), FreshAny()], return_type=FreshAny()),
            "floor": FreshFunction(param_types=[FreshFloat()], return_type=FreshInt()),
            "ceil": FreshFunction(param_types=[FreshFloat()], return_type=FreshInt()),
            "round": FreshFunction(param_types=[FreshFloat()], return_type=FreshInt()),
        }
        for name, fn_type in builtins.items():
            self.current_scope.define(name, Symbol(name=name, type=fn_type, is_defined=True))

    def check_program(self, statements: list[Stmt]) -> TypedProgram:
        """Type check a full program and return canonical TypedProgram IR."""
        self.node_types.clear()

        # Pass 1: Pre-register top-level struct declarations and function signatures
        for stmt in statements:
            match stmt:
                case StructDeclStmt(name=name, fields=fields):
                    field_dict: dict[str, FreshType] = {}
                    for f in fields:
                        field_dict[f.name.lexeme] = self._resolve_type_annotation(f.type_annotation)
                    struct_type = FreshStruct(name=name.lexeme, fields=field_dict)
                    self.struct_defs[name.lexeme] = struct_type
                    self.current_scope.define(name.lexeme, Symbol(name=name.lexeme, type=struct_type, is_defined=True))

                case FnDeclStmt(name=name, params=params, return_type=rt):
                    param_types = [self._resolve_type_annotation(p.type_annotation) for p in params]
                    ret_type = self._resolve_type_annotation(rt) if rt else FreshNil()
                    fn_type = FreshFunction(param_types=param_types, return_type=ret_type)
                    self.current_scope.define(name.lexeme, Symbol(name=name.lexeme, type=fn_type, is_defined=True))

                case ClassDeclStmt(name=name, parent_name=parent, fields=fields, constructor=ctor, methods=methods):
                    parent_class: FreshClass | None = None
                    if parent is not None:
                        parent_class = self.class_defs.get(parent.lexeme)
                    field_dict: dict[str, FreshType] = {}
                    for f in fields:
                        field_dict[f.name.lexeme] = self._resolve_type_annotation(f.type_annotation)
                    class_type = FreshClass(name=name.lexeme, fields=field_dict, parent=parent_class)
                    for m in methods:
                        m_param_types = [self._resolve_type_annotation(p.type_annotation) for p in m.params]
                        m_ret_type = self._resolve_type_annotation(m.return_type) if m.return_type else FreshNil()
                        class_type.methods[m.name.lexeme] = FreshFunction(param_types=m_param_types, return_type=m_ret_type)
                    if ctor is not None:
                        c_param_types = [self._resolve_type_annotation(p.type_annotation) for p in ctor.params]
                        ctor_fn = FreshFunction(param_types=c_param_types, return_type=class_type)
                        class_type.methods["constructor"] = ctor_fn
                        class_type.methods["init"] = ctor_fn
                    self.class_defs[name.lexeme] = class_type
                    self.current_scope.define(name.lexeme, Symbol(name=name.lexeme, type=class_type, is_defined=True))

                case _:
                    pass

        # Pass 2: Check all statements
        for stmt in statements:
            self._check_stmt(stmt)

        return TypedProgram(
            statements=statements,
            node_types=dict(self.node_types),
            struct_defs=dict(self.struct_defs),
            class_defs=dict(self.class_defs),
        )

    # ── Statement Type Checking ───────────────────────────────

    def _check_stmt(self, stmt: Stmt) -> None:
        match stmt:
            case VarDeclStmt(name=name, type_annotation=ta, initializer=init):
                init_type = self._check_expr(init) if init is not None else FreshNil()
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

            case ClassDeclStmt(name=name, parent_name=parent, fields=fields, constructor=ctor, methods=methods):
                class_type = self.class_defs[name.lexeme]
                if parent is not None and class_type.parent is None:
                    class_type.parent = self.class_defs.get(parent.lexeme)

                old_class = self.current_class
                self.current_class = class_type

                self._push_scope()
                self.current_scope.define("this", Symbol(name="this", type=class_type, is_defined=True))

                if ctor is not None:
                    if ctor.super_args is not None:
                        if class_type.parent is not None:
                            parent_ctor = class_type.parent.lookup_method("constructor")
                            if parent_ctor and parent_ctor.param_types is not None:
                                s_types = [self._check_expr(a) for a in ctor.super_args]
                                if len(s_types) != len(parent_ctor.param_types):
                                    raise FreshTypeError(
                                        message=f"Super constructor expected {len(parent_ctor.param_types)} arguments but got {len(s_types)}.",
                                        line=ctor.keyword.line,
                                        column=ctor.keyword.column,
                                        filename=self.filename,
                                    )
                                for i, (exp, act) in enumerate(zip(parent_ctor.param_types, s_types)):
                                    if not self._types_compatible(exp, act):
                                        raise FreshTypeError(
                                            message=f"Super argument {i+1} expected '{exp}', got '{act}'.",
                                            line=ctor.keyword.line,
                                            column=ctor.keyword.column,
                                            filename=self.filename,
                                        )

                    self._push_scope()
                    for p in ctor.params:
                        ptype = self._resolve_type_annotation(p.type_annotation)
                        self.current_scope.define(p.name.lexeme, Symbol(name=p.name.lexeme, type=ptype, is_defined=True))
                    old_ret = self.current_return_type
                    self.current_return_type = FreshNil()
                    for s in ctor.body:
                        self._check_stmt(s)
                    self.current_return_type = old_ret
                    self._pop_scope()

                for m in methods:
                    m_param_types = [self._resolve_type_annotation(p.type_annotation) for p in m.params]
                    m_ret_type = self._resolve_type_annotation(m.return_type) if m.return_type else FreshNil()

                    self._push_scope()
                    for p, ptype in zip(m.params, m_param_types):
                        self.current_scope.define(p.name.lexeme, Symbol(name=p.name.lexeme, type=ptype, is_defined=True))

                    old_ret = self.current_return_type
                    self.current_return_type = m_ret_type
                    for s in m.body:
                        self._check_stmt(s)
                    self.current_return_type = old_ret
                    self._pop_scope()

                self._pop_scope()
                self.current_class = old_class

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

            case IfStmt(keyword=keyword, condition=cond, then_branch=then_b, else_branch=else_b):
                self._check_expr(cond)
                self._push_scope()
                for s in then_b:
                    self._check_stmt(s)
                self._pop_scope()

                if else_b:
                    self._push_scope()
                    for s in else_b:
                        self._check_stmt(s)
                    self._pop_scope()

            case WhileStmt(keyword=keyword, condition=cond, body=body):
                self._check_expr(cond)
                self._push_scope()
                for s in body:
                    self._check_stmt(s)
                self._pop_scope()

            case ForStmt(initializer=init, condition=cond, increment=inc, body=body):
                self._push_scope()
                if init:
                    self._check_stmt(init)
                if cond:
                    self._check_expr(cond)
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
                    if isinstance(l_type, (FreshString, FreshAny)) and isinstance(r_type, (FreshString, FreshAny)):
                        return FreshBool()
                    raise FreshTypeError(
                        message=f"Comparison '{op.lexeme}' requires numeric or string types, got '{l_type}' and '{r_type}'.",
                        line=op.line,
                        column=op.column,
                        filename=self.filename,
                    )

                return FreshAny()

            case LogicalExpr(left=l, operator=op, right=r):
                self._check_expr(l)
                self._check_expr(r)
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
                    return FreshBool()
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

                if isinstance(callee_type, FreshClass):
                    ctor = callee_type.lookup_method("constructor")
                    if ctor is not None and ctor.param_types is not None:
                        if len(arg_types) != len(ctor.param_types):
                            raise FreshTypeError(
                                message=f"Constructor for '{callee_type.name}' expected {len(ctor.param_types)} arguments but got {len(arg_types)}.",
                                line=paren.line,
                                column=paren.column,
                                filename=self.filename,
                            )
                        for i, (expected, actual) in enumerate(zip(ctor.param_types, arg_types)):
                            if not self._types_compatible(expected, actual):
                                raise FreshTypeError(
                                    message=f"Argument {i+1} expected '{expected}', got '{actual}'.",
                                    line=paren.line,
                                    column=paren.column,
                                    filename=self.filename,
                                )
                    return callee_type

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
                elem_types = [self._check_expr(e) for e in elems]
                # Compute LUB for numbers
                has_float = any(isinstance(t, FreshFloat) for t in elem_types)
                if has_float and all(isinstance(t, (FreshInt, FreshFloat, FreshAny)) for t in elem_types):
                    target_type: FreshType = FreshFloat()
                else:
                    target_type = elem_types[0]

                for elem_t in elem_types:
                    if not self._types_compatible(target_type, elem_t):
                        raise FreshTypeError(
                            message=f"Array element type mismatch: expected '{target_type}', got '{elem_t}'.",
                            line=bracket.line,
                            column=bracket.column,
                            filename=self.filename,
                        )
                return FreshArray(element_type=target_type)

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

                if isinstance(obj_type, FreshAny):
                    return val_type

                raise FreshTypeError(
                    message=f"Cannot index non-array type '{obj_type}'.",
                    line=bracket.line,
                    column=bracket.column,
                    filename=self.filename,
                )

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
                if isinstance(obj_type, FreshClass):
                    field_type = obj_type.lookup_field(name.lexeme)
                    if field_type is not None:
                        return field_type
                    method = obj_type.lookup_method(name.lexeme)
                    if method is not None:
                        return method
                    raise FreshTypeError(
                        message=f"Class '{obj_type.name}' has no field or method '{name.lexeme}'.",
                        line=name.line,
                        column=name.column,
                        filename=self.filename,
                    )
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
                if isinstance(obj_type, FreshClass):
                    field_type = obj_type.lookup_field(name.lexeme)
                    if field_type is None:
                        raise FreshTypeError(
                            message=f"Class '{obj_type.name}' has no field '{name.lexeme}'.",
                            line=name.line,
                            column=name.column,
                            filename=self.filename,
                        )
                    if not self._types_compatible(field_type, val_type):
                        raise FreshTypeError(
                            message=f"Cannot assign '{val_type}' to field '{name.lexeme}' of type '{field_type}'.",
                            line=name.line,
                            column=name.column,
                            filename=self.filename,
                        )
                    return val_type
                if isinstance(obj_type, FreshAny):
                    return val_type
                raise FreshTypeError(
                    message=f"Type '{obj_type}' has no fields.",
                    line=name.line,
                    column=name.column,
                    filename=self.filename,
                )

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
                for fname in provided_fields:
                    if fname not in struct_def.fields:
                        raise FreshTypeError(
                            message=f"Unrecognized field '{fname}' in struct '{name.lexeme}'.",
                            line=name.line,
                            column=name.column,
                            filename=self.filename,
                        )
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

            case MatchExpr(keyword=keyword, scrutinee=scr, arms=arms):
                scr_type = self._check_expr(scr)
                body_types: list[FreshType] = []
                for arm in arms:
                    self._push_scope()
                    self._check_pattern(arm.pattern, scr_type)
                    if arm.guard:
                        self._check_expr(arm.guard)
                    body_types.append(self._check_expr(arm.body))
                    self._pop_scope()

                if not body_types:
                    return FreshNil()

                unified = body_types[0]
                for bt in body_types[1:]:
                    if not self._types_compatible(unified, bt):
                        if self._types_compatible(bt, unified):
                            unified = bt
                        else:
                            raise FreshTypeError(
                                message=f"Match arm return type mismatch: expected '{unified}', got '{bt}'.",
                                line=keyword.line,
                                column=keyword.column,
                                filename=self.filename,
                            )
                return unified

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

            case ThisExpr(keyword=keyword):
                if self.current_class is None:
                    raise FreshTypeError(
                        message="Cannot use 'this' outside of a class.",
                        line=keyword.line,
                        column=keyword.column,
                        filename=self.filename,
                    )
                return self.current_class

            case SuperExpr(keyword=keyword, method=method):
                if self.current_class is None or self.current_class.parent is None:
                    raise FreshTypeError(
                        message="Cannot use 'super' in a class without a superclass.",
                        line=keyword.line,
                        column=keyword.column,
                        filename=self.filename,
                    )
                lookup_name = "constructor" if method.lexeme == "init" else method.lexeme
                parent_method = self.current_class.parent.lookup_method(lookup_name)
                if parent_method is None:
                    parent_method = self.current_class.parent.lookup_method(method.lexeme)
                if parent_method is None:
                    raise FreshTypeError(
                        message=f"Superclass '{self.current_class.parent.name}' has no method '{method.lexeme}'.",
                        line=method.line,
                        column=method.column,
                        filename=self.filename,
                    )
                return parent_method

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

    def _resolve_type_annotation(self, ta: TypeAnnotation | None) -> FreshType:
        if ta is None:
            return FreshAny()
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
                if tname in self.class_defs:
                    return self.class_defs[tname]
                return FreshAny()

    def _types_compatible(self, expected: FreshType, actual: FreshType) -> bool:
        if isinstance(expected, FreshAny) or isinstance(actual, FreshAny):
            return True
        if isinstance(expected, FreshFloat) and isinstance(actual, FreshInt):
            return True  # Auto coercion int -> float
        if isinstance(expected, FreshClass) and isinstance(actual, FreshClass):
            return actual.is_subclass_of(expected)
        return expected == actual

    def _push_scope(self) -> None:
        self.current_scope = Scope(depth=self.current_scope.depth + 1, parent=self.current_scope)

    def _pop_scope(self) -> None:
        if self.current_scope.parent:
            self.current_scope = self.current_scope.parent
