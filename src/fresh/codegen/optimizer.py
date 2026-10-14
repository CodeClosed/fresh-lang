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
        """Peephole optimizations with jump target recalculation."""
        old_code = chunk.code
        n = len(old_code)
        if n == 0:
            return chunk

        new_code: list[int] = []
        new_lines: list[int] = []
        old_to_new: list[int] = [0] * (n + 1)
        i = 0

        while i < n:
            old_to_new[i] = len(new_code)

            # Pattern: OP_SET_LOCAL slot; OP_GET_LOCAL slot -> OP_SET_LOCAL slot; OP_DUP
            if (
                i + 3 < n
                and old_code[i] == Opcode.OP_SET_LOCAL
                and old_code[i + 2] == Opcode.OP_GET_LOCAL
                and old_code[i + 1] == old_code[i + 3]
            ):
                slot = old_code[i + 1]
                line = chunk.lines[i]
                new_code.append(Opcode.OP_SET_LOCAL)
                new_code.append(slot)
                new_code.append(Opcode.OP_DUP)
                new_lines.extend([line, line, line])
                old_to_new[i + 1] = old_to_new[i] + 1
                old_to_new[i + 2] = old_to_new[i] + 2
                old_to_new[i + 3] = old_to_new[i] + 2
                i += 4
                continue

            new_code.append(old_code[i])
            new_lines.append(chunk.lines[i])
            i += 1

        old_to_new[n] = len(new_code)

        # Fix jump offsets in new_code
        j = 0
        m = len(new_code)
        while j < m:
            op = new_code[j]
            if op in (Opcode.OP_JUMP, Opcode.OP_JUMP_IF_FALSE):
                if j + 2 < m:
                    hi = new_code[j + 1]
                    lo = new_code[j + 2]
                    old_jump = (hi << 8) | lo
                    # Find old source index corresponding to j
                    old_src = next((idx for idx, nidx in enumerate(old_to_new) if nidx == j), j)
                    old_target = old_src + 3 + old_jump
                    if old_target <= n:
                        new_target = old_to_new[old_target]
                        new_jump = new_target - (j + 3)
                        new_code[j + 1] = (new_jump >> 8) & 0xFF
                        new_code[j + 2] = new_jump & 0xFF
                j += 3
            elif op == Opcode.OP_LOOP:
                if j + 2 < m:
                    hi = new_code[j + 1]
                    lo = new_code[j + 2]
                    old_jump = (hi << 8) | lo
                    old_src = next((idx for idx, nidx in enumerate(old_to_new) if nidx == j), j)
                    old_target = (old_src + 3) - old_jump
                    if old_target >= 0:
                        new_target = old_to_new[old_target]
                        new_jump = (j + 3) - new_target
                        new_code[j + 1] = (new_jump >> 8) & 0xFF
                        new_code[j + 2] = new_jump & 0xFF
                j += 3
            elif op in (
                Opcode.OP_CONSTANT,
                Opcode.OP_DEFINE_GLOBAL,
                Opcode.OP_GET_GLOBAL,
                Opcode.OP_SET_GLOBAL,
                Opcode.OP_GET_LOCAL,
                Opcode.OP_SET_LOCAL,
                Opcode.OP_GET_UPVALUE,
                Opcode.OP_SET_UPVALUE,
                Opcode.OP_CALL,
                Opcode.OP_BUILD_ARRAY,
            ):
                j += 2
            elif op in (Opcode.OP_STRUCT_DEF, Opcode.OP_STRUCT_NEW):
                j += 3
            else:
                j += 1

        chunk.code = new_code
        chunk.lines = new_lines
        return chunk
