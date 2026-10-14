"""VM runtime safety and error handling test suite for Fresh."""

import pytest

from fresh.common.errors import FreshRuntimeError
from fresh.pipeline import run_source


def test_runtime_error_division_by_zero():
    source = "let x = 10 / 0;"
    with pytest.raises(FreshRuntimeError) as excinfo:
        run_source(source)
    assert "[E5001]" in str(excinfo.value)
    assert "Division by zero" in str(excinfo.value)


def test_runtime_error_modulo_by_zero():
    source = "let x = 10 % 0;"
    with pytest.raises(FreshRuntimeError) as excinfo:
        run_source(source)
    assert "[E5001]" in str(excinfo.value)
    assert "Modulo by zero" in str(excinfo.value)


def test_runtime_error_array_index_out_of_bounds():
    source = """
    let arr = [1, 2, 3];
    println(arr[10]);
    """
    with pytest.raises(FreshRuntimeError) as excinfo:
        run_source(source)
    assert "[E5002]" in str(excinfo.value)
    assert "Array index out of bounds" in str(excinfo.value)


def test_runtime_error_string_index_out_of_bounds():
    source = """
    let s = "hi";
    println(s[5]);
    """
    with pytest.raises(FreshRuntimeError) as excinfo:
        run_source(source)
    assert "[E5002]" in str(excinfo.value)
    assert "String index out of bounds" in str(excinfo.value)


def test_runtime_error_stack_overflow():
    source = """
    fn recurse() -> int {
        return recurse();
    }
    recurse();
    """
    with pytest.raises(FreshRuntimeError) as excinfo:
        run_source(source)
    assert "[E5003]" in str(excinfo.value)
    assert "Stack overflow" in str(excinfo.value)


def test_string_hex_and_unicode_escapes(run_fresh):
    source = """
    let a = "\\x41\\x42";
    let b = "\\u0048\\u0069";
    println(a);
    println(b);
    """
    out = run_fresh(source)
    assert out.strip().splitlines() == ["AB", "Hi"]


def test_adversarial_unknown_opcode():
    from fresh.codegen.chunk import Chunk
    from fresh.vm.objects import ObjFunction
    from fresh.vm.vm import VM

    chunk = Chunk()
    chunk.code.append(255)  # Invalid opcode byte
    chunk.lines.append(1)

    vm = VM()
    with pytest.raises(FreshRuntimeError) as excinfo:
        vm.interpret(ObjFunction("<test>", 0, chunk))
    assert "Unknown opcode '255'" in str(excinfo.value)


def test_adversarial_stack_underflow():
    from fresh.vm.vm import VM
    vm = VM()
    with pytest.raises(FreshRuntimeError) as excinfo:
        vm.pop()
    assert "Stack underflow" in str(excinfo.value)


def test_adversarial_constant_index_out_of_bounds():
    from fresh.codegen.chunk import Chunk
    from fresh.codegen.opcodes import Opcode
    from fresh.vm.objects import ObjFunction
    from fresh.vm.vm import VM

    chunk = Chunk()
    chunk.write(Opcode.OP_CONSTANT.value, 1)
    chunk.write(99, 1)  # Nonexistent constant index

    vm = VM()
    with pytest.raises(FreshRuntimeError) as excinfo:
        vm.interpret(ObjFunction("<test>", 0, chunk))
    assert "Constant index out of bounds: 99" in str(excinfo.value)


