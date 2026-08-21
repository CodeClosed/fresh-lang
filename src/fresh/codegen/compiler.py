"""AST to Bytecode Compiler for Fresh.

Transforms AST nodes into executable bytecode chunks. Handles scope allocation,
jump emission & backpatching, closures with upvalues, struct definitions,
array indexing, and pattern decision trees.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING, Any

from fresh.codegen.chunk import Chunk
from fresh.codegen.opcodes import Opcode
from fresh.common.errors import FreshSyntaxError
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
    """Function compilation type."""

    SCRIPT = auto()
    FUNCTION = auto()
    LAMBDA = auto()


@dataclass(slots=True)
class Local:
    """Represents a local variable in the compiler's stack frame."""

    name: str
    depth: int
    is_captured: bool = False


@dataclass(slots=True)
class Upvalue:
    """Represents a captured upvalue in a closure."""

    index: int
    is_local: bool


@dataclass(slots=True)
class LoopScope:
    """Tracks jump patch locations for break and continue statements in a loop."""

    start_offset: int
    break_jumps: list[int] = field(default_factory=list)
    continue_jumps: list[int] = field(default_factory=list)


class Compiler:
    """Compiles Fresh AST into executable Bytecode Chunks."""

    def __init__(
        self,
        filename: str = "<stdin>",
        func_type: FunctionType = FunctionType.SCRIPT,
        func_name: str = "<main>",
        enclosing: Compiler | None = None,
    ) -> None:
        self.filename = filename
        self.func_type = func_type
        self.func_name = func_name
        self.enclosing = enclosing

        self.chunk = Chunk()
        self.locals: list[Local] = []
        self.upvalues: list[Upvalue] = []
        self.scope_depth: int = 0
        self.loop_stack: list[LoopScope] = []
        self.current_line: int = 1

        # Claim stack slot 0 for function call frame self-reference
        self.locals.append(Local(name="", depth=0))

    def compile_program(self, statements: list[Stmt]) -> Chunk:
        """Compile a list of top-level statements into a Chunk."""
        for stmt in statements:
            self._compile_stmt(stmt)

        self._emit_opcode(Opcode.OP_NIL)
        self._emit_opcode(Opcode.OP_RETURN)
        return self.chunk

    # ── Emit Helpers ──────────────────────────────────────────

    def _emit_byte(self, byte: int) -> int:
        return self.chunk.write(byte, self.current_line)

    def _emit_opcode(self, opcode: Opcode) -> int:
        return self._emit_byte(int(opcode))

    def _emit_bytes(self, byte1: int, byte2: int) -> None:
        self._emit_byte(byte1)
        self._emit_byte(byte2)

    def _emit_constant(self, value: Any) -> None:
        idx = self.chunk.add_constant(value)
        self._emit_opcode(Opcode.OP_CONSTANT)
        self._emit_byte(idx)

    def _emit_jump(self, opcode: Opcode) -> int:
        self._emit_opcode(opcode)
        self._emit_byte(0xFF)  # Placeholder hi
        self._emit_byte(0xFF)  # Placeholder lo
        return len(self.chunk.code) - 2

    def _patch_jump(self, offset: int) -> None:
        jump = len(self.chunk.code) - offset - 2
        if jump > 0xFFFF:
            raise FreshSyntaxError(
                message="Too much code to jump over.",
                line=self.current_line,
                column=0,
                filename=self.filename,
            )
        self.chunk.code[offset] = (jump >> 8) & 0xFF
        self.chunk.code[offset + 1] = jump & 0xFF

    def _emit_loop(self, start_offset: int) -> None:
        self._emit_opcode(Opcode.OP_LOOP)
        jump = len(self.chunk.code) - start_offset + 2
        if jump > 0xFFFF:
            raise FreshSyntaxError(
                message="Loop body too large.",
                line=self.current_line,
                column=0,
                filename=self.filename,
            )
        self._emit_byte((jump >> 8) & 0xFF)
        self._emit_byte(jump & 0xFF)

    # ── Scope Management ──────────────────────────────────────

    def _begin_scope(self) -> None:
        self.scope_depth += 1

    def _end_scope(self) -> None:
        self.scope_depth -= 1
        while self.locals and self.locals[-1].depth > self.scope_depth:
            local = self.locals.pop()
            if local.is_captured:
                self._emit_opcode(Opcode.OP_CLOSE_UPVALUE)
            else:
                self._emit_opcode(Opcode.OP_POP)

    # ── Variable Resolution ───────────────────────────────────

    def _resolve_local(self, name: Token) -> int:
        for i in range(len(self.locals) - 1, -1, -1):
            if self.locals[i].name == name.lexeme:
                return i
        return -1

    def _resolve_upvalue(self, name: Token) -> int:
        if self.enclosing is None:
            return -1

        local = self.enclosing._resolve_local(name)
        if local != -1:
            self.enclosing.locals[local].is_captured = True
            return self._add_upvalue(local, is_local=True)

        upvalue = self.enclosing._resolve_upvalue(name)
        if upvalue != -1:
            return self._add_upvalue(upvalue, is_local=False)

        return -1

    def _add_upvalue(self, index: int, is_local: bool) -> int:
        for i, upval in enumerate(self.upvalues):
            if upval.index == index and upval.is_local == is_local:
                return i
        self.upvalues.append(Upvalue(index=index, is_local=is_local))
        return len(self.upvalues) - 1

    # ── Statement Compilation ─────────────────────────────────

    def _compile_stmt(self, stmt: Stmt) -> None:
        match stmt:
            case VarDeclStmt(name=name, initializer=init):
                self.current_line = name.line
                self._compile_expr(init)
                if self.scope_depth > 0:
                    self.locals.append(Local(name=name.lexeme, depth=self.scope_depth))
                else:
                    name_idx = self.chunk.add_constant(name.lexeme)
                    self._emit_opcode(Opcode.OP_DEFINE_GLOBAL)
                    self._emit_byte(name_idx)

            case FnDeclStmt(name=name, params=params, return_type=_, body=body):
                self.current_line = name.line
                compiler = Compiler(
                    filename=self.filename,
                    func_type=FunctionType.FUNCTION,
                    func_name=name.lexeme,
                    enclosing=self,
                )
                compiler._begin_scope()
                for p in params:
                    compiler.locals.append(Local(name=p.name.lexeme, depth=compiler.scope_depth))

                for s in body:
                    compiler._compile_stmt(s)

                compiler._emit_opcode(Opcode.OP_NIL)
                compiler._emit_opcode(Opcode.OP_RETURN)

                func_obj = CompiledFunction(
                    name=name.lexeme,
                    arity=len(params),
                    chunk=compiler.chunk,
                    upvalue_count=len(compiler.upvalues),
                )
                func_idx = self.chunk.add_constant(func_obj)
                self._emit_opcode(Opcode.OP_CLOSURE)
                self._emit_byte(func_idx)

                for upval in compiler.upvalues:
                    self._emit_byte(1 if upval.is_local else 0)
                    self._emit_byte(upval.index)

                if self.scope_depth > 0:
                    self.locals.append(Local(name=name.lexeme, depth=self.scope_depth))
                else:
                    name_idx = self.chunk.add_constant(name.lexeme)
                    self._emit_opcode(Opcode.OP_DEFINE_GLOBAL)
                    self._emit_byte(name_idx)

            case StructDeclStmt(name=name, fields=fields):
                self.current_line = name.line
                name_idx = self.chunk.add_constant(name.lexeme)
                field_names = [f.name.lexeme for f in fields]
                struct_def_idx = self.chunk.add_constant(field_names)
                self._emit_opcode(Opcode.OP_STRUCT_DEF)
                self._emit_byte(name_idx)
                self._emit_byte(struct_def_idx)

            case BlockStmt(statements=stmts):
                self._begin_scope()
                for s in stmts:
                    self._compile_stmt(s)
                self._end_scope()

            case ExprStmt(expression=expr):
                self._compile_expr(expr)
                self._emit_opcode(Opcode.OP_POP)

            case IfStmt(keyword=kw, condition=cond, then_branch=then_b, else_branch=else_b):
                self.current_line = kw.line
                self._compile_expr(cond)
                then_jump = self._emit_jump(Opcode.OP_JUMP_IF_FALSE)
                self._emit_opcode(Opcode.OP_POP)

                self._begin_scope()
                for s in then_b:
                    self._compile_stmt(s)
                self._end_scope()

                else_jump = self._emit_jump(Opcode.OP_JUMP)
                self._patch_jump(then_jump)
                self._emit_opcode(Opcode.OP_POP)

                if else_b:
                    self._begin_scope()
                    for s in else_b:
                        self._compile_stmt(s)
                    self._end_scope()

                self._patch_jump(else_jump)

            case WhileStmt(keyword=kw, condition=cond, body=body):
                self.current_line = kw.line
                loop_start = len(self.chunk.code)
                loop_scope = LoopScope(start_offset=loop_start)
                self.loop_stack.append(loop_scope)

                self._compile_expr(cond)
                exit_jump = self._emit_jump(Opcode.OP_JUMP_IF_FALSE)
                self._emit_opcode(Opcode.OP_POP)

                self._begin_scope()
                for s in body:
                    self._compile_stmt(s)
                self._end_scope()

                self._emit_loop(loop_start)
                self._patch_jump(exit_jump)
                self._emit_opcode(Opcode.OP_POP)

                for break_offset in loop_scope.break_jumps:
                    self._patch_jump(break_offset)

                self.loop_stack.pop()

            case ForStmt(keyword=kw, initializer=init, condition=cond, increment=inc, body=body):
                self.current_line = kw.line
                self._begin_scope()
                if init:
                    self._compile_stmt(init)

                loop_start = len(self.chunk.code)

                exit_jump = -1
                if cond:
                    self._compile_expr(cond)
                    exit_jump = self._emit_jump(Opcode.OP_JUMP_IF_FALSE)
                    self._emit_opcode(Opcode.OP_POP)

                if inc:
                    body_jump = self._emit_jump(Opcode.OP_JUMP)
                    increment_start = len(self.chunk.code)
                    self._compile_expr(inc)
                    self._emit_opcode(Opcode.OP_POP)
                    self._emit_loop(loop_start)
                    self._patch_jump(body_jump)
                    continue_target = increment_start
                else:
                    continue_target = loop_start

                loop_scope = LoopScope(start_offset=continue_target)
                self.loop_stack.append(loop_scope)

                self._begin_scope()
                for s in body:
                    self._compile_stmt(s)
                self._end_scope()

                self._emit_loop(continue_target)

                if exit_jump != -1:
                    self._patch_jump(exit_jump)
                    self._emit_opcode(Opcode.OP_POP)

                for break_offset in loop_scope.break_jumps:
                    self._patch_jump(break_offset)

                self.loop_stack.pop()
                self._end_scope()

            case ReturnStmt(keyword=kw, value=val):
                self.current_line = kw.line
                if val:
                    self._compile_expr(val)
                else:
                    self._emit_opcode(Opcode.OP_NIL)
                self._emit_opcode(Opcode.OP_RETURN)

            case BreakStmt(keyword=kw):
                self.current_line = kw.line
                jump_offset = self._emit_jump(Opcode.OP_JUMP)
                self.loop_stack[-1].break_jumps.append(jump_offset)

            case ContinueStmt(keyword=kw):
                self.current_line = kw.line
                self._emit_loop(self.loop_stack[-1].start_offset)

            case ImportStmt():
                pass


    # ── Expression Compilation ────────────────────────────────

    def _compile_expr(self, expr: Expr) -> None:
        match expr:
            case LiteralExpr(value=val, token=tok):
                self.current_line = tok.line
                if val is True:
                    self._emit_opcode(Opcode.OP_TRUE)
                elif val is False:
                    self._emit_opcode(Opcode.OP_FALSE)
                elif val is None:
                    self._emit_opcode(Opcode.OP_NIL)
                else:
                    self._emit_constant(val)

            case VariableExpr(name=name):
                self.current_line = name.line
                self._named_variable(name, can_assign=False)

            case AssignExpr(name=name, value=val):
                self.current_line = name.line
                self._compile_expr(val)
                self._named_variable(name, can_assign=True)

            case BinaryExpr(left=l, operator=op, right=r):
                self.current_line = op.line
                self._compile_expr(l)
                self._compile_expr(r)

                match op.lexeme:
                    case "+":
                        self._emit_opcode(Opcode.OP_ADD)
                    case "-":
                        self._emit_opcode(Opcode.OP_SUBTRACT)
                    case "*":
                        self._emit_opcode(Opcode.OP_MULTIPLY)
                    case "/":
                        self._emit_opcode(Opcode.OP_DIVIDE)
                    case "%":
                        self._emit_opcode(Opcode.OP_MODULO)
                    case "==":
                        self._emit_opcode(Opcode.OP_EQUAL)
                    case "!=":
                        self._emit_opcode(Opcode.OP_NOT_EQUAL)
                    case ">":
                        self._emit_opcode(Opcode.OP_GREATER)
                    case ">=":
                        self._emit_opcode(Opcode.OP_GREATER_EQUAL)
                    case "<":
                        self._emit_opcode(Opcode.OP_LESS)
                    case "<=":
                        self._emit_opcode(Opcode.OP_LESS_EQUAL)

            case LogicalExpr(left=l, operator=op, right=r):
                self.current_line = op.line
                self._compile_expr(l)
                if op.lexeme == "||":
                    else_jump = self._emit_jump(Opcode.OP_JUMP_IF_FALSE)
                    end_jump = self._emit_jump(Opcode.OP_JUMP)
                    self._patch_jump(else_jump)
                    self._emit_opcode(Opcode.OP_POP)
                    self._compile_expr(r)
                    self._patch_jump(end_jump)
                else:  # &&
                    end_jump = self._emit_jump(Opcode.OP_JUMP_IF_FALSE)
                    self._emit_opcode(Opcode.OP_POP)
                    self._compile_expr(r)
                    self._patch_jump(end_jump)

            case UnaryExpr(operator=op, operand=operand):
                self.current_line = op.line
                self._compile_expr(operand)
                if op.lexeme == "-":
                    self._emit_opcode(Opcode.OP_NEGATE)
                elif op.lexeme == "!":
                    self._emit_opcode(Opcode.OP_NOT)

            case CallExpr(callee=callee, paren=paren, arguments=args):
                self.current_line = paren.line
                self._compile_expr(callee)
                for arg in args:
                    self._compile_expr(arg)
                self._emit_opcode(Opcode.OP_CALL)
                self._emit_byte(len(args))

            case ArrayExpr(bracket=bracket, elements=elems):
                self.current_line = bracket.line
                for elem in elems:
                    self._compile_expr(elem)
                self._emit_opcode(Opcode.OP_BUILD_ARRAY)
                self._emit_byte(len(elems))

            case IndexExpr(obj=obj, bracket=bracket, index=idx):
                self.current_line = bracket.line
                self._compile_expr(obj)
                self._compile_expr(idx)
                self._emit_opcode(Opcode.OP_GET_INDEX)

            case IndexSetExpr(obj=obj, bracket=bracket, index=idx, value=val):
                self.current_line = bracket.line
                self._compile_expr(obj)
                self._compile_expr(idx)
                self._compile_expr(val)
                self._emit_opcode(Opcode.OP_SET_INDEX)

            case FieldAccessExpr(obj=obj, name=name):
                self.current_line = name.line
                self._compile_expr(obj)
                name_idx = self.chunk.add_constant(name.lexeme)
                self._emit_opcode(Opcode.OP_GET_FIELD)
                self._emit_byte(name_idx)

            case FieldSetExpr(obj=obj, name=name, value=val):
                self.current_line = name.line
                self._compile_expr(obj)
                self._compile_expr(val)
                name_idx = self.chunk.add_constant(name.lexeme)
                self._emit_opcode(Opcode.OP_SET_FIELD)
                self._emit_byte(name_idx)

            case StructLiteralExpr(name=name, fields=fields):
                self.current_line = name.line
                struct_name_idx = self.chunk.add_constant(name.lexeme)
                for _, fval in fields:
                    self._compile_expr(fval)
                self._emit_opcode(Opcode.OP_STRUCT_NEW)
                self._emit_byte(struct_name_idx)
                self._emit_byte(len(fields))

            case MatchExpr(keyword=kw, scrutinee=scr, arms=arms):
                self.current_line = kw.line
                self._compile_expr(scr)
                self._begin_scope()
                scr_slot = len(self.locals)
                self.locals.append(Local(name="<scrutinee>", depth=self.scope_depth))

                end_jumps: list[int] = []

                for arm in arms:
                    self._begin_scope()
                    next_arm_jumps: list[int] = []
                    is_var_pattern = isinstance(arm.pattern, VariablePattern)
                    var_slot: int | None = None

                    self._emit_opcode(Opcode.OP_GET_LOCAL)
                    self._emit_byte(scr_slot)

                    match arm.pattern:
                        case LiteralPattern(value=val):
                            self._emit_constant(val)
                            self._emit_opcode(Opcode.OP_EQUAL)
                            next_arm_jumps.append(self._emit_jump(Opcode.OP_JUMP_IF_FALSE))
                            self._emit_opcode(Opcode.OP_POP)
                        case VariablePattern(name=vname):
                            var_slot = len(self.locals)
                            self.locals.append(Local(name=vname.lexeme, depth=self.scope_depth))
                        case WildcardPattern():
                            self._emit_opcode(Opcode.OP_POP)
                        case _:
                            self._emit_opcode(Opcode.OP_POP)

                    if arm.guard:
                        self._compile_expr(arm.guard)
                        next_arm_jumps.append(self._emit_jump(Opcode.OP_JUMP_IF_FALSE))
                        self._emit_opcode(Opcode.OP_POP)

                    self._compile_expr(arm.body)

                    if is_var_pattern and var_slot is not None:
                        self._emit_opcode(Opcode.OP_SET_LOCAL)
                        self._emit_byte(var_slot)
                        self._emit_opcode(Opcode.OP_POP)

                    end_jumps.append(self._emit_jump(Opcode.OP_JUMP))

                    for j in next_arm_jumps:
                        self._patch_jump(j)
                    self._emit_opcode(Opcode.OP_POP)
                    if is_var_pattern:
                        self._emit_opcode(Opcode.OP_POP)

                    while self.locals and self.locals[-1].depth > self.scope_depth - 1:
                        self.locals.pop()
                    self.scope_depth -= 1

                self._emit_opcode(Opcode.OP_NIL)

                for j in end_jumps:
                    self._patch_jump(j)

                self._emit_opcode(Opcode.OP_SET_LOCAL)
                self._emit_byte(scr_slot)
                self._emit_opcode(Opcode.OP_POP)

                while self.locals and self.locals[-1].depth >= self.scope_depth:
                    self.locals.pop()
                self.scope_depth -= 1


            case LambdaExpr(keyword=kw, params=params, return_type=_, body=body):
                self.current_line = kw.line
                compiler = Compiler(
                    filename=self.filename,
                    func_type=FunctionType.LAMBDA,
                    func_name="<lambda>",
                    enclosing=self,
                )
                compiler._begin_scope()
                for p in params:
                    compiler.locals.append(Local(name=p.name.lexeme, depth=compiler.scope_depth))
                for s in body:
                    compiler._compile_stmt(s)
                compiler._emit_opcode(Opcode.OP_NIL)
                compiler._emit_opcode(Opcode.OP_RETURN)

                func_obj = CompiledFunction(
                    name="<lambda>",
                    arity=len(params),
                    chunk=compiler.chunk,
                    upvalue_count=len(compiler.upvalues),
                )
                func_idx = self.chunk.add_constant(func_obj)
                self._emit_opcode(Opcode.OP_CLOSURE)
                self._emit_byte(func_idx)

                for upval in compiler.upvalues:
                    self._emit_byte(1 if upval.is_local else 0)
                    self._emit_byte(upval.index)

    def _compile_pattern_test(self, pattern: object, fail_jumps: list[int]) -> None:
        match pattern:
            case LiteralPattern(value=val):
                self._emit_constant(val)
                self._emit_opcode(Opcode.OP_EQUAL)
                fail_jumps.append(self._emit_jump(Opcode.OP_JUMP_IF_FALSE))
            case VariablePattern(name=name):
                # Bind top-of-stack scrutinee duplicate to variable `name`
                if self.scope_depth > 0:
                    slot = self._resolve_local(name)
                    if slot == -1:
                        self.locals.append(Local(name=name.lexeme, depth=self.scope_depth))
                        slot = len(self.locals) - 1
                    self._emit_opcode(Opcode.OP_SET_LOCAL)
                    self._emit_byte(slot)
                else:
                    name_idx = self.chunk.add_constant(name.lexeme)
                    self._emit_opcode(Opcode.OP_SET_GLOBAL)
                    self._emit_byte(name_idx)
                    self._emit_opcode(Opcode.OP_POP)
            case WildcardPattern():
                pass
            case StructPattern():
                pass

    def _named_variable(self, name: Token, can_assign: bool) -> None:
        arg = self._resolve_local(name)
        if arg != -1:
            get_op = Opcode.OP_GET_LOCAL
            set_op = Opcode.OP_SET_LOCAL
        else:
            arg = self._resolve_upvalue(name)
            if arg != -1:
                get_op = Opcode.OP_GET_UPVALUE
                set_op = Opcode.OP_SET_UPVALUE
            else:
                arg = self.chunk.add_constant(name.lexeme)
                get_op = Opcode.OP_GET_GLOBAL
                set_op = Opcode.OP_SET_GLOBAL

        if can_assign:
            self._emit_opcode(set_op)
            self._emit_byte(arg)
        else:
            self._emit_opcode(get_op)
            self._emit_byte(arg)


@dataclass(slots=True)
class CompiledFunction:
    """Holds compiled bytecode for a function or closure."""

    name: str
    arity: int
    chunk: Chunk
    upvalue_count: int = 0
