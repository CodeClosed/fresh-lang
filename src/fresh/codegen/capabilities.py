"""Machine-readable backend capability matrix and AST validator for Fresh."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Any

from fresh.common.errors import FreshCodegenError
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
    LogicalExpr,
    MatchExpr,
    ReturnStmt,
    Stmt,
    StructDeclStmt,
    StructLiteralExpr,
    UnaryExpr,
    VarDeclStmt,
    VariableExpr,
    WhileStmt,
)

if TYPE_CHECKING:
    from typing import Type


class BackendStatus(str, Enum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    RESTRICTED = "restricted"


# Machine-readable AST node capability matrix
BACKEND_CAPABILITY_MATRIX: dict[Type[Stmt | Expr], dict[str, BackendStatus]] = {
    VarDeclStmt: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.SUPPORTED},
    FnDeclStmt: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.SUPPORTED},
    StructDeclStmt: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.SUPPORTED},
    ImportStmt: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.SUPPORTED},
    IfStmt: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.SUPPORTED},
    WhileStmt: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.SUPPORTED},
    ForStmt: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.SUPPORTED},
    ReturnStmt: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.SUPPORTED},
    BreakStmt: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.SUPPORTED},
    ContinueStmt: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.SUPPORTED},
    ExprStmt: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.SUPPORTED},
    BlockStmt: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.SUPPORTED},
    LiteralExpr: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.SUPPORTED},
    VariableExpr: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.SUPPORTED},
    AssignExpr: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.SUPPORTED},
    BinaryExpr: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.SUPPORTED},
    LogicalExpr: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.SUPPORTED},
    UnaryExpr: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.SUPPORTED},
    CallExpr: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.SUPPORTED},
    StructLiteralExpr: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.SUPPORTED},
    FieldAccessExpr: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.SUPPORTED},
    FieldSetExpr: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.SUPPORTED},
    IndexExpr: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.SUPPORTED},
    IndexSetExpr: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.SUPPORTED},
    ArrayExpr: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.RESTRICTED},
    MatchExpr: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.UNSUPPORTED},
    LambdaExpr: {"vm": BackendStatus.SUPPORTED, "native_c": BackendStatus.UNSUPPORTED},
}


def validate_ast_for_backend(statements: list[Stmt], backend: str = "native_c", filename: str = "<unknown>") -> None:
    """Validate all nodes in AST recursively against backend capability matrix before emission."""
    for stmt in statements:
        _check_node(stmt, backend, filename)


def _check_node(node: Any, backend: str, filename: str) -> None:
    if node is None:
        return

    node_type = type(node)
    caps = BACKEND_CAPABILITY_MATRIX.get(node_type)
    if caps and caps.get(backend) == BackendStatus.UNSUPPORTED:
        raise FreshCodegenError(
            message=f"[E3001] Native C backend does not support '{node_type.__name__}'.",
            line=getattr(node, "line", 0),
            filename=filename,
        )

    # Recursive inspection of child AST nodes
    if isinstance(node, BlockStmt):
        for s in node.statements:
            _check_node(s, backend, filename)
    elif isinstance(node, VarDeclStmt):
        if node.initializer:
            _check_node(node.initializer, backend, filename)
    elif isinstance(node, FnDeclStmt):
        for s in node.body:
            _check_node(s, backend, filename)
    elif isinstance(node, IfStmt):
        _check_node(node.condition, backend, filename)
        _check_node(node.then_branch, backend, filename)
        if node.else_branch:
            _check_node(node.else_branch, backend, filename)
    elif isinstance(node, WhileStmt):
        _check_node(node.condition, backend, filename)
        _check_node(node.body, backend, filename)
    elif isinstance(node, ForStmt):
        if node.initializer:
            _check_node(node.initializer, backend, filename)
        if node.condition:
            _check_node(node.condition, backend, filename)
        if node.increment:
            _check_node(node.increment, backend, filename)
        _check_node(node.body, backend, filename)
    elif isinstance(node, ReturnStmt):
        if node.value:
            _check_node(node.value, backend, filename)
    elif isinstance(node, ExprStmt):
        _check_node(node.expression, backend, filename)
    elif isinstance(node, BinaryExpr):
        _check_node(node.left, backend, filename)
        _check_node(node.right, backend, filename)
    elif isinstance(node, LogicalExpr):
        _check_node(node.left, backend, filename)
        _check_node(node.right, backend, filename)
    elif isinstance(node, UnaryExpr):
        _check_node(node.operand, backend, filename)
    elif isinstance(node, AssignExpr):
        _check_node(node.value, backend, filename)
    elif isinstance(node, CallExpr):
        _check_node(node.callee, backend, filename)
        for arg in node.arguments:
            _check_node(arg, backend, filename)
    elif isinstance(node, StructLiteralExpr):
        for _, val in getattr(node, "fields", []):
            _check_node(val, backend, filename)
    elif isinstance(node, FieldAccessExpr):
        _check_node(node.obj, backend, filename)
    elif isinstance(node, FieldSetExpr):
        _check_node(node.obj, backend, filename)
        _check_node(node.value, backend, filename)
    elif isinstance(node, IndexExpr):
        _check_node(node.obj, backend, filename)
        _check_node(node.index, backend, filename)
    elif isinstance(node, IndexSetExpr):
        _check_node(node.obj, backend, filename)
        _check_node(node.index, backend, filename)
        _check_node(node.value, backend, filename)
    elif isinstance(node, ArrayExpr):
        for el in node.elements:
            _check_node(el, backend, filename)
    elif isinstance(node, MatchExpr):
        _check_node(node.scrutinee, backend, filename)
        for arm in getattr(node, "arms", []):
            if getattr(arm, "guard", None):
                _check_node(arm.guard, backend, filename)
            _check_node(arm.body, backend, filename)
    elif isinstance(node, LambdaExpr):
        for s in getattr(node, "body", []):
            _check_node(s, backend, filename)
