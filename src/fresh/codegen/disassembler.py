"""Bytecode disassembler for human-readable bytecode inspection (--disassemble flag)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fresh.codegen.opcodes import Opcode

if TYPE_CHECKING:
    from fresh.codegen.chunk import Chunk


class Disassembler:
    """Pretty-prints bytecode instructions from a Chunk."""

    def disassemble_chunk(self, chunk: Chunk, name: str = "main") -> str:
        """Disassemble a chunk into a formatted instruction listing string."""
        lines = [f"=== {name} ==="]
        offset = 0
        while offset < len(chunk.code):
            line_str, offset = self.disassemble_instruction(chunk, offset)
            lines.append(line_str)
        return "\n".join(lines)

    def disassemble_instruction(self, chunk: Chunk, offset: int) -> tuple[str, int]:
        """Disassemble a single instruction at `offset`.

        Returns:
            Tuple of (formatted line string, next offset).
        """
        line_info = f"{chunk.lines[offset]:4d} "
        if offset > 0 and chunk.lines[offset] == chunk.lines[offset - 1]:
            line_info = "   | "

        offset_str = f"{offset:04d}"
        opcode_byte = chunk.code[offset]

        try:
            opcode = Opcode(opcode_byte)
        except ValueError:
            return f"{offset_str} {line_info} UNKNOWN_OPCODE ({opcode_byte})", offset + 1

        match opcode:
            case (
                Opcode.OP_NIL
                | Opcode.OP_TRUE
                | Opcode.OP_FALSE
                | Opcode.OP_POP
                | Opcode.OP_DUP
                | Opcode.OP_ADD
                | Opcode.OP_SUBTRACT
                | Opcode.OP_MULTIPLY
                | Opcode.OP_DIVIDE
                | Opcode.OP_MODULO
                | Opcode.OP_NEGATE
                | Opcode.OP_NOT
                | Opcode.OP_EQUAL
                | Opcode.OP_NOT_EQUAL
                | Opcode.OP_GREATER
                | Opcode.OP_GREATER_EQUAL
                | Opcode.OP_LESS
                | Opcode.OP_LESS_EQUAL
                | Opcode.OP_RETURN
                | Opcode.OP_GET_INDEX
                | Opcode.OP_SET_INDEX
            ):
                return f"{offset_str} {line_info} {opcode.name}", offset + 1

            case Opcode.OP_CONSTANT:
                const_idx = chunk.code[offset + 1]
                val = chunk.constants[const_idx]
                return f"{offset_str} {line_info} {opcode.name:<16s} {const_idx:4d} '{val}'", offset + 2

            case Opcode.OP_GET_GLOBAL | Opcode.OP_SET_GLOBAL | Opcode.OP_DEFINE_GLOBAL:
                name_idx = chunk.code[offset + 1]
                name = chunk.constants[name_idx]
                return f"{offset_str} {line_info} {opcode.name:<16s} {name_idx:4d} '{name}'", offset + 2

            case Opcode.OP_GET_LOCAL | Opcode.OP_SET_LOCAL | Opcode.OP_GET_UPVALUE | Opcode.OP_SET_UPVALUE:
                slot = chunk.code[offset + 1]
                return f"{offset_str} {line_info} {opcode.name:<16s} {slot:4d}", offset + 2

            case Opcode.OP_JUMP | Opcode.OP_JUMP_IF_FALSE:
                hi = chunk.code[offset + 1]
                lo = chunk.code[offset + 2]
                jump_offset = (hi << 8) | lo
                target = offset + 3 + jump_offset
                return f"{offset_str} {line_info} {opcode.name:<16s} {offset+3} -> {target}", offset + 3

            case Opcode.OP_LOOP:
                hi = chunk.code[offset + 1]
                lo = chunk.code[offset + 2]
                jump_offset = (hi << 8) | lo
                target = offset + 3 - jump_offset
                return f"{offset_str} {line_info} {opcode.name:<16s} {offset+3} -> {target}", offset + 3

            case Opcode.OP_CALL | Opcode.OP_BUILD_ARRAY:
                arg_count = chunk.code[offset + 1]
                return f"{offset_str} {line_info} {opcode.name:<16s} {arg_count:4d}", offset + 2

            case Opcode.OP_STRUCT_DEF | Opcode.OP_STRUCT_NEW:
                name_idx = chunk.code[offset + 1]
                fields_count = chunk.code[offset + 2]
                name = chunk.constants[name_idx]
                return f"{offset_str} {line_info} {opcode.name:<16s} {name} (fields: {fields_count})", offset + 3

            case Opcode.OP_GET_FIELD | Opcode.OP_SET_FIELD:
                field_idx = chunk.code[offset + 1]
                fname = chunk.constants[field_idx]
                return f"{offset_str} {line_info} {opcode.name:<16s} {field_idx:4d} '{fname}'", offset + 2

            case Opcode.OP_CLOSURE:
                func_idx = chunk.code[offset + 1]
                func = chunk.constants[func_idx]
                res = f"{offset_str} {line_info} {opcode.name:<16s} {func_idx:4d} <fn {getattr(func, 'name', 'lambda')}>"
                next_off = offset + 2
                upval_count = getattr(func, 'upvalue_count', 0)
                for _ in range(upval_count):
                    is_local = chunk.code[next_off]
                    idx = chunk.code[next_off + 1]
                    local_str = "local" if is_local else "upvalue"
                    res += f"\n     |                     {local_str} {idx}"
                    next_off += 2
                return res, next_off

            case _:
                return f"{offset_str} {line_info} {opcode.name}", offset + 1
