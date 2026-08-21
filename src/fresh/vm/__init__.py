"""Fresh Virtual Machine runtime, call frames, heap objects, and garbage collector."""

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
from fresh.vm.value import Value
from fresh.vm.vm import VM

__all__ = [
    "VM",
    "CallFrame",
    "GarbageCollector",
    "Value",
    "Obj",
    "ObjFunction",
    "ObjClosure",
    "ObjUpvalue",
    "ObjStructDef",
    "ObjStructInstance",
    "ObjArray",
    "ObjNativeFunction",
]
