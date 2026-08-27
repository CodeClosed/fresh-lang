"""Mark-and-sweep garbage collector for the Fresh Virtual Machine."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from fresh.vm.objects import Obj

if TYPE_CHECKING:
    from fresh.vm.vm import VM


class GarbageCollector:
    """Manages heap memory and reclaims unreachable guest objects."""

    def __init__(
        self,
        vm: VM,
        initial_threshold_bytes: int = 1024 * 1024,
        stress_mode: bool = False,
    ) -> None:
        self.vm = vm
        self.bytes_allocated: int = 0
        self.next_gc: int = initial_threshold_bytes
        self.stress_mode: bool = stress_mode

    def allocate(self, obj: Obj, size_bytes: int = 64) -> Obj:
        """Register a new object on the VM heap and trigger GC if threshold exceeded or stress mode enabled."""
        self.bytes_allocated += size_bytes
        if (
            self.stress_mode
            or os.environ.get("FRESH_GC_STRESS") == "1"
            or self.bytes_allocated > self.next_gc
        ):

            self.collect_garbage()
        self.vm.objects.append(obj)
        return obj


    def collect_garbage(self) -> None:
        """Run full mark-and-sweep garbage collection pass."""
        worklist: list[Obj] = []

        # ── Phase 1: Mark Roots ───────────────────────────────

        # Stack roots
        for i in range(self.vm.stack_top):
            val = self.vm.stack[i]
            if isinstance(val, Obj):
                self._mark_object(val, worklist)

        # CallFrame roots (closures and constants)
        for frame in self.vm.frames:
            self._mark_object(frame.closure, worklist)
            if frame.closure and frame.closure.function and frame.closure.function.chunk:
                for constant in frame.closure.function.chunk.constants:
                    if isinstance(constant, Obj):
                        self._mark_object(constant, worklist)

        # Globals roots
        for val in self.vm.globals.values():
            if isinstance(val, Obj):
                self._mark_object(val, worklist)

        # Open Upvalues roots
        for upval in self.vm.open_upvalues:
            self._mark_object(upval, worklist)

        # Temp roots on VM if registered
        for troot in getattr(self.vm, "temp_roots", []):
            if isinstance(troot, Obj):
                self._mark_object(troot, worklist)

        # ── Phase 2: Transitive Blackening ────────────────────
        while worklist:
            obj = worklist.pop()
            obj.trace_references(worklist)

        # ── Phase 3: Sweep ────────────────────────────────────
        surviving_objects: list[Obj] = []
        for obj in self.vm.objects:
            if obj.is_marked:
                obj.is_marked = False  # Reset mark for next collection
                surviving_objects.append(obj)

        self.vm.objects = surviving_objects
        # Adaptive GC threshold
        self.next_gc = max(int(self.bytes_allocated * 1.5), 1024)

    def _mark_object(self, obj: Obj | None, worklist: list[Obj]) -> None:
        if obj is None or obj.is_marked:
            return
        obj.is_marked = True
        worklist.append(obj)
