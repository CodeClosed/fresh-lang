"""Bytecode instruction opcodes for the Fresh virtual machine.

Uses IntEnum for fast comparison and specialized match/case jump tables
in Python 3.11+.
"""

from enum import IntEnum, auto


class Opcode(IntEnum):
    """Virtual Machine Instruction Set Architecture (ISA)."""

    # ── Constants & Stack Operations ──────────────────────────
    OP_CONSTANT = auto()       # [const_idx] -> push constants[const_idx]
    OP_NIL = auto()            # -> push None
    OP_TRUE = auto()           # -> push True
    OP_FALSE = auto()          # -> push False
    OP_POP = auto()            # [val] -> (discard)
    OP_DUP = auto()            # [val] -> [val, val]

    # ── Arithmetic & Logical ──────────────────────────────────
    OP_ADD = auto()            # [a, b] -> [a + b]
    OP_SUBTRACT = auto()       # [a, b] -> [a - b]
    OP_MULTIPLY = auto()       # [a, b] -> [a * b]
    OP_DIVIDE = auto()         # [a, b] -> [a / b]
    OP_MODULO = auto()         # [a, b] -> [a % b]
    OP_NEGATE = auto()         # [a] -> [-a]
    OP_NOT = auto()            # [a] -> [not a]

    # ── Comparison ────────────────────────────────────────────
    OP_EQUAL = auto()          # [a, b] -> [a == b]
    OP_NOT_EQUAL = auto()      # [a, b] -> [a != b]
    OP_GREATER = auto()        # [a, b] -> [a > b]
    OP_GREATER_EQUAL = auto()  # [a, b] -> [a >= b]
    OP_LESS = auto()           # [a, b] -> [a < b]
    OP_LESS_EQUAL = auto()     # [a, b] -> [a <= b]

    # ── Variables & Scope Access ──────────────────────────────
    OP_GET_GLOBAL = auto()     # [name_idx] -> push globals[name]
    OP_SET_GLOBAL = auto()     # [name_idx] (val) -> globals[name] = val
    OP_DEFINE_GLOBAL = auto()  # [name_idx] (val) -> globals[name] = pop()
    OP_GET_LOCAL = auto()      # [slot_idx] -> push stack[base + slot]
    OP_SET_LOCAL = auto()      # [slot_idx] -> stack[base + slot] = peek()
    OP_GET_UPVALUE = auto()    # [upvalue_idx] -> push upvalues[idx].get()
    OP_SET_UPVALUE = auto()    # [upvalue_idx] -> upvalues[idx].set(peek())

    # ── Control Flow & Jumps ──────────────────────────────────
    OP_JUMP = auto()           # [offset_hi, offset_lo] -> ip += offset
    OP_JUMP_IF_FALSE = auto()  # [offset_hi, offset_lo] -> if not peek(): ip += offset
    OP_LOOP = auto()           # [offset_hi, offset_lo] -> ip -= offset

    # ── Functions & Closures ──────────────────────────────────
    OP_CALL = auto()           # [arg_count] -> invoke function with args
    OP_CLOSURE = auto()        # [func_const_idx, (is_local, idx)...] -> create ObjClosure
    OP_CLOSE_UPVALUE = auto()  # [slot] -> close upvalue pointing to slot
    OP_RETURN = auto()         # -> pop call frame, return value

    # ── Structs & Records ─────────────────────────────────────
    OP_STRUCT_DEF = auto()     # [name_idx, field_count] -> create ObjStructDef
    OP_STRUCT_NEW = auto()     # [struct_idx, field_count] -> instantiate ObjStructInstance
    OP_GET_FIELD = auto()      # [field_name_idx] -> push field value
    OP_SET_FIELD = auto()      # [field_name_idx] -> set field value

    # ── Arrays & Indexing ─────────────────────────────────────
    OP_BUILD_ARRAY = auto()    # [element_count] -> pop elements into ObjArray
    OP_GET_INDEX = auto()      # [obj, index] -> push obj[index]
    OP_SET_INDEX = auto()      # [obj, index, value] -> obj[index] = value

    # ── Pattern Matching & Runtime Errors ─────────────────────
    OP_MATCH_PATTERN = auto()  # Check pattern equality / shape
    OP_PANIC = auto()          # [msg_idx] -> raise runtime error
