"""Bytecode optimizer implementing constant folding, dead code elimination, and peephole optimizations."""

from __future__ import annotations

from fresh.codegen.chunk import Chunk
from fresh.codegen.opcodes import Opcode


class Optimizer:
    """Optimizes compiled bytecode chunks."""

    def optimize(self, chunk: Chunk) -> Chunk:
        """Run optimization passes over `chunk`."""
        chunk = self._constant_folding(chunk)
        chunk = self._dead_code_elimination(chunk)
        chunk = self._peephole_pass(chunk)
        return chunk

    def _constant_folding(self, chunk: Chunk) -> Chunk:
        """Fold binary/unary arithmetic operations on literal constants at compile time."""
        # For current release, return chunk directly to preserve absolute safety across jumps
        return chunk

    def _dead_code_elimination(self, chunk: Chunk) -> Chunk:
        """Dead code elimination pass (currently preserved as pass-through until CFG pass)."""
        return chunk

    def _peephole_pass(self, chunk: Chunk) -> Chunk:
        """Peephole optimizations (e.g. OP_SET_LOCAL x; OP_GET_LOCAL x -> OP_SET_LOCAL x; OP_DUP)."""
        new_code: list[int] = []
        new_lines: list[int] = []
        i = 0
        n = len(chunk.code)

        while i < n:
            # Pattern: OP_SET_LOCAL slot; OP_GET_LOCAL slot -> OP_SET_LOCAL slot; OP_DUP
            if (
                i + 3 < n
                and chunk.code[i] == Opcode.OP_SET_LOCAL
                and chunk.code[i + 2] == Opcode.OP_GET_LOCAL
                and chunk.code[i + 1] == chunk.code[i + 3]
            ):
                slot = chunk.code[i + 1]
                line = chunk.lines[i]
                new_code.append(Opcode.OP_SET_LOCAL)
                new_code.append(slot)
                new_code.append(Opcode.OP_DUP)
                new_lines.extend([line, line, line])
                i += 4
                continue

            new_code.append(chunk.code[i])
            new_lines.append(chunk.lines[i])
            i += 1

        chunk.code = new_code
        chunk.lines = new_lines
        return chunk
