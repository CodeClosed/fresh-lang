"""Virtual Machine execution engine for Fresh bytecode."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fresh.codegen.opcodes import Opcode
from fresh.common.errors import FreshRuntimeError
from fresh.vm.frame import CallFrame
from fresh.vm.gc import GarbageCollector
from fresh.vm.objects import (
    Obj,
    ObjArray,
    ObjClosure,
    ObjFunction,
    ObjNativeFunction,
    ObjStructDef,
    ObjStructInstance,
    ObjUpvalue,
)
from fresh.vm.value import is_falsey, value_to_string

if TYPE_CHECKING:
    pass

STACK_MAX = 2048
FRAMES_MAX = 256


class VM:
    """Stack-based Virtual Machine execution engine."""

    def __init__(self, gc_stress: bool = False) -> None:
        self.stack: list[Any] = [None] * STACK_MAX
        self.stack_top: int = 0
        self.frames: list[CallFrame] = []
        self.globals: dict[str, Any] = {}
        self.struct_defs: dict[str, ObjStructDef] = {}
        self.open_upvalues: list[ObjUpvalue] = []
        self.objects: list[Obj] = []

        self.gc = GarbageCollector(self, stress_mode=gc_stress)


    # ── Stack Operations ──────────────────────────────────────

    def push(self, value: Any) -> None:
        """Push a value onto the evaluation stack."""
        if self.stack_top >= STACK_MAX:
            raise FreshRuntimeError("Stack overflow.")
        self.stack[self.stack_top] = value
        self.stack_top += 1

    def pop(self) -> Any:
        """Pop a value off the evaluation stack."""
        if self.stack_top <= 0:
            raise FreshRuntimeError("Stack underflow.")
        self.stack_top -= 1
        return self.stack[self.stack_top]

    def peek(self, distance: int = 0) -> Any:
        """Peek at a value on the stack `distance` items from the top."""
        idx = self.stack_top - 1 - distance
        if idx < 0 or idx >= self.stack_top:
            raise FreshRuntimeError("Stack underflow on peek.")
        return self.stack[idx]

    # ── Upvalue Operations ────────────────────────────────────

    def capture_upvalue(self, slot: int) -> ObjUpvalue:
        """Capture a stack slot into an open upvalue (or reuse existing)."""
        for upval in self.open_upvalues:
            if upval.location == slot:
                return upval

        created = ObjUpvalue(slot)
        self.gc.allocate(created)
        self.open_upvalues.append(created)
        return created

    def close_upvalues(self, last_slot: int) -> None:
        """Close upvalues pointing to `last_slot` or higher."""
        remaining: list[ObjUpvalue] = []
        for upval in self.open_upvalues:
            if upval.location is not None and upval.location >= last_slot:
                upval.closed_value = self.stack[upval.location]
                upval.location = None
            else:
                remaining.append(upval)
        self.open_upvalues = remaining

    # ── Execution Loop ────────────────────────────────────────

    def interpret(self, function: ObjFunction) -> Any:
        """Execute a compiled top-level ObjFunction in the VM."""
        main_closure = ObjClosure(function)
        self.gc.allocate(main_closure)
        self.push(main_closure)
        self._call_value(main_closure, 0)
        return self.run()

    def run(self) -> Any:
        """Main VM opcode dispatch loop."""
        frame = self.frames[-1]

        while True:
            chunk = frame.closure.function.chunk
            code = chunk.code
            if frame.ip >= len(code):
                raise FreshRuntimeError("Instruction pointer out of bounds.")

            opcode_byte = code[frame.ip]
            frame.ip += 1

            try:
                opcode = Opcode(opcode_byte)
            except ValueError:
                raise FreshRuntimeError(f"Unknown opcode '{opcode_byte}'.")

            match opcode:
                # ── Constants & Stack ─────────────────────────
                case Opcode.OP_CONSTANT:
                    if frame.ip >= len(code):
                        raise FreshRuntimeError("Truncated OP_CONSTANT instruction.")
                    idx = code[frame.ip]
                    frame.ip += 1
                    if idx >= len(chunk.constants):
                        raise FreshRuntimeError(f"Constant index out of bounds: {idx}")
                    self.push(chunk.constants[idx])

                case Opcode.OP_NIL:
                    self.push(None)

                case Opcode.OP_TRUE:
                    self.push(True)

                case Opcode.OP_FALSE:
                    self.push(False)

                case Opcode.OP_POP:
                    self.pop()

                case Opcode.OP_DUP:
                    self.push(self.peek())

                # ── Arithmetic & Logic ────────────────────────
                case Opcode.OP_ADD:
                    b = self.pop()
                    a = self.pop()
                    if isinstance(a, str) or isinstance(b, str):
                        self.push(value_to_string(a) + value_to_string(b))
                    elif isinstance(a, (int, float)) and isinstance(b, (int, float)):
                        self.push(a + b)
                    else:
                        raise FreshRuntimeError(f"Operands to '+' must be numbers or strings, got {type(a)} and {type(b)}.")

                case Opcode.OP_SUBTRACT:
                    b = self.pop()
                    a = self.pop()
                    self.push(a - b)

                case Opcode.OP_MULTIPLY:
                    b = self.pop()
                    a = self.pop()
                    self.push(a * b)

                case Opcode.OP_DIVIDE:
                    b = self.pop()
                    a = self.pop()
                    if b == 0:
                        raise FreshRuntimeError("[E5001] Division by zero.")
                    if isinstance(a, int) and isinstance(b, int) and not isinstance(a, bool) and not isinstance(b, bool):
                        self.push(a // b)
                    else:
                        self.push(a / b)

                case Opcode.OP_MODULO:
                    b = self.pop()
                    a = self.pop()
                    if b == 0:
                        raise FreshRuntimeError("[E5001] Modulo by zero.")
                    self.push(a % b)

                case Opcode.OP_NEGATE:
                    a = self.pop()
                    self.push(-a)

                case Opcode.OP_NOT:
                    a = self.pop()
                    self.push(is_falsey(a))

                # ── Comparisons ───────────────────────────────
                case Opcode.OP_EQUAL:
                    b = self.pop()
                    a = self.pop()
                    self.push(a == b)

                case Opcode.OP_NOT_EQUAL:
                    b = self.pop()
                    a = self.pop()
                    self.push(a != b)

                case Opcode.OP_GREATER:
                    b = self.pop()
                    a = self.pop()
                    self.push(a > b)

                case Opcode.OP_GREATER_EQUAL:
                    b = self.pop()
                    a = self.pop()
                    self.push(a >= b)

                case Opcode.OP_LESS:
                    b = self.pop()
                    a = self.pop()
                    self.push(a < b)

                case Opcode.OP_LESS_EQUAL:
                    b = self.pop()
                    a = self.pop()
                    self.push(a <= b)

                # ── Variables & Scope ─────────────────────────
                case Opcode.OP_GET_GLOBAL:
                    name_idx = code[frame.ip]
                    frame.ip += 1
                    name = chunk.constants[name_idx]
                    if name not in self.globals:
                        raise FreshRuntimeError(f"Undefined variable '{name}'.")
                    self.push(self.globals[name])

                case Opcode.OP_SET_GLOBAL:
                    name_idx = code[frame.ip]
                    frame.ip += 1
                    name = chunk.constants[name_idx]
                    self.globals[name] = self.peek()

                case Opcode.OP_DEFINE_GLOBAL:
                    name_idx = code[frame.ip]
                    frame.ip += 1
                    name = chunk.constants[name_idx]
                    self.globals[name] = self.pop()

                case Opcode.OP_GET_LOCAL:
                    slot = code[frame.ip]
                    frame.ip += 1
                    self.push(self.stack[frame.stack_base + slot])

                case Opcode.OP_SET_LOCAL:
                    slot = code[frame.ip]
                    frame.ip += 1
                    self.stack[frame.stack_base + slot] = self.peek()

                case Opcode.OP_GET_UPVALUE:
                    idx = code[frame.ip]
                    frame.ip += 1
                    self.push(frame.closure.upvalues[idx].get(self.stack))

                case Opcode.OP_SET_UPVALUE:
                    idx = code[frame.ip]
                    frame.ip += 1
                    frame.closure.upvalues[idx].set(self.stack, self.peek())

                # ── Control Flow ──────────────────────────────
                case Opcode.OP_JUMP:
                    hi = code[frame.ip]
                    lo = code[frame.ip + 1]
                    offset = (hi << 8) | lo
                    frame.ip += 2 + offset

                case Opcode.OP_JUMP_IF_FALSE:
                    hi = code[frame.ip]
                    lo = code[frame.ip + 1]
                    offset = (hi << 8) | lo
                    frame.ip += 2
                    if is_falsey(self.peek()):
                        frame.ip += offset

                case Opcode.OP_LOOP:
                    hi = code[frame.ip]
                    lo = code[frame.ip + 1]
                    offset = (hi << 8) | lo
                    frame.ip += 2
                    frame.ip -= offset

                # ── Function Calls & Closures ─────────────────
                case Opcode.OP_CALL:
                    arg_count = code[frame.ip]
                    frame.ip += 1
                    callee = self.peek(arg_count)
                    self._call_value(callee, arg_count)
                    frame = self.frames[-1]

                case Opcode.OP_CLOSURE:
                    func_idx = code[frame.ip]
                    frame.ip += 1
                    compiled_func = chunk.constants[func_idx]

                    # Convert CompiledFunction to ObjFunction
                    obj_func = ObjFunction(
                        name=compiled_func.name,
                        arity=compiled_func.arity,
                        chunk=compiled_func.chunk,
                        upvalue_count=compiled_func.upvalue_count,
                    )
                    self.gc.allocate(obj_func)
                    self.push(obj_func)  # Root obj_func on stack during closure allocation

                    closure = ObjClosure(obj_func)
                    self.gc.allocate(closure)
                    self.pop()  # Pop temporary obj_func root

                    for _ in range(compiled_func.upvalue_count):
                        is_local = bool(code[frame.ip])
                        idx = code[frame.ip + 1]
                        frame.ip += 2

                        if is_local:
                            closure.upvalues.append(self.capture_upvalue(frame.stack_base + idx))
                        else:
                            closure.upvalues.append(frame.closure.upvalues[idx])

                    self.push(closure)

                case Opcode.OP_CLOSE_UPVALUE:
                    self.close_upvalues(self.stack_top - 1)
                    self.pop()

                case Opcode.OP_RETURN:
                    result = self.pop()
                    self.close_upvalues(frame.stack_base)
                    self.frames.pop()

                    if not self.frames:
                        return result

                    self.stack_top = frame.stack_base
                    self.push(result)
                    frame = self.frames[-1]

                # ── Structs ───────────────────────────────────
                case Opcode.OP_STRUCT_DEF:
                    name_idx = code[frame.ip]
                    fields_idx = code[frame.ip + 1]
                    frame.ip += 2
                    name = chunk.constants[name_idx]
                    field_names = chunk.constants[fields_idx]

                    sdef = ObjStructDef(name, field_names)
                    self.gc.allocate(sdef)
                    self.struct_defs[name] = sdef
                    self.globals[name] = sdef

                case Opcode.OP_STRUCT_NEW:
                    name_idx = code[frame.ip]
                    arg_count = code[frame.ip + 1]
                    frame.ip += 2
                    name = chunk.constants[name_idx]
                    if name not in self.struct_defs:
                        raise FreshRuntimeError(f"Undefined struct '{name}'.")
                    sdef = self.struct_defs[name]

                    instance = ObjStructInstance(sdef)
                    for i in reversed(range(arg_count)):
                        instance.fields[i] = self.pop()

                    self.push(instance)  # Root instance on stack
                    self.gc.allocate(instance)

                case Opcode.OP_GET_FIELD:
                    field_idx = code[frame.ip]
                    frame.ip += 1
                    field_name = chunk.constants[field_idx]

                    instance = self.pop()
                    if not isinstance(instance, ObjStructInstance):
                        raise FreshRuntimeError("Only struct instances have fields.")

                    if field_name not in instance.struct_def.field_indices:
                        raise FreshRuntimeError(f"Undefined field '{field_name}' on struct '{instance.struct_def.name}'.")
                    slot = instance.struct_def.field_indices[field_name]
                    self.push(instance.fields[slot])

                case Opcode.OP_SET_FIELD:
                    field_idx = code[frame.ip]
                    frame.ip += 1
                    field_name = chunk.constants[field_idx]

                    value = self.pop()
                    instance = self.pop()
                    if not isinstance(instance, ObjStructInstance):
                        raise FreshRuntimeError("Only struct instances have fields.")

                    if field_name not in instance.struct_def.field_indices:
                        raise FreshRuntimeError(f"Undefined field '{field_name}' on struct '{instance.struct_def.name}'.")
                    slot = instance.struct_def.field_indices[field_name]
                    instance.fields[slot] = value
                    self.push(value)

                # ── Arrays ────────────────────────────────────
                case Opcode.OP_BUILD_ARRAY:
                    count = code[frame.ip]
                    frame.ip += 1
                    elements = [None] * count
                    for i in reversed(range(count)):
                        elements[i] = self.pop()

                    arr = ObjArray(elements)
                    self.push(arr)  # Root arr on stack before allocating
                    self.gc.allocate(arr)

                case Opcode.OP_GET_INDEX:
                    index = self.pop()
                    target = self.pop()

                    if isinstance(target, ObjArray):
                        if not isinstance(index, int):
                            raise FreshRuntimeError("[E5002] Array index must be an integer.")
                        if index < 0 or index >= len(target.elements):
                            raise FreshRuntimeError(f"[E5002] Array index out of bounds: index {index}, length {len(target.elements)}.")
                        self.push(target.elements[index])
                    elif isinstance(target, str):
                        if not isinstance(index, int):
                            raise FreshRuntimeError("[E5002] String index must be an integer.")
                        if index < 0 or index >= len(target):
                            raise FreshRuntimeError(f"[E5002] String index out of bounds: index {index}, length {len(target)}.")
                        self.push(target[index])
                    else:
                        raise FreshRuntimeError("[E5002] Cannot index non-array/string value.")

                case Opcode.OP_SET_INDEX:
                    value = self.pop()
                    index = self.pop()
                    target = self.pop()

                    if not isinstance(target, ObjArray):
                        raise FreshRuntimeError("[E5002] Only arrays can be assigned by index.")
                    if not isinstance(index, int):
                        raise FreshRuntimeError("[E5002] Array index must be an integer.")
                    if index < 0 or index >= len(target.elements):
                        raise FreshRuntimeError(f"[E5002] Array index out of bounds: index {index}, length {len(target.elements)}.")

                    target.elements[index] = value
                    self.push(value)

    def _call_value(self, callee: Any, arg_count: int) -> None:
        """Invoke a closure or native function."""
        if isinstance(callee, ObjClosure):
            if arg_count != callee.function.arity:
                raise FreshRuntimeError(
                    f"Expected {callee.function.arity} arguments but got {arg_count}."
                )
            if len(self.frames) >= FRAMES_MAX:
                raise FreshRuntimeError("[E5003] Stack overflow: Maximum recursion depth / call frames exceeded.")

            frame = CallFrame(
                closure=callee,
                ip=0,
                stack_base=self.stack_top - arg_count - 1,
            )
            self.frames.append(frame)

        elif isinstance(callee, ObjNativeFunction):
            if arg_count != callee.arity and callee.arity != -1:
                raise FreshRuntimeError(
                    f"Native function '{callee.name}' expected {callee.arity} arguments but got {arg_count}."
                )
            args = [self.pop() for _ in range(arg_count)][::-1]
            self.pop()  # Pop the native function object
            result = callee.function(*args)
            self.push(result)

        else:
            raise FreshRuntimeError(f"Cannot call non-callable type '{type(callee).__name__}'.")
