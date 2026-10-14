"""Call Frame for function execution inside the Fresh VM."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fresh.vm.objects import ObjClosure


@dataclass(slots=True)
class CallFrame:
    """Represents an active function call frame on the VM call stack.

    Attributes:
        closure:    The closure currently executing.
        ip:         Instruction pointer index within the closure's bytecode chunk.
        stack_base: Base stack index where local variables for this call begin.
    """

    closure: ObjClosure
    ip: int = 0
    stack_base: int = 0
