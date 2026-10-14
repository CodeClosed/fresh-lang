"""Differential testing suite comparing Fresh VM execution vs C Native compiled execution."""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

from fresh.codegen.c_transpiler import CTranspiler
from fresh.lexer.scanner import Scanner
from fresh.parser.parser import Parser


def find_c_compiler() -> str | None:
    compiler = shutil.which("gcc") or shutil.which("clang") or shutil.which("cl")
    if compiler:
        return compiler
    if sys.platform.startswith("win"):
        for path in (
            r"C:\msys64\ucrt64\bin\gcc.exe",
            r"C:\msys64\mingw64\bin\gcc.exe",
            r"C:\MinGW\bin\gcc.exe",
        ):
            if Path(path).exists():
                return path
    return None


C_COMPILER = find_c_compiler()


def run_c_native(source: str) -> str:
    if not C_COMPILER:
        pytest.skip("No C compiler available for differential testing")

    tokens = Scanner(source).scan_tokens()
    ast = Parser(tokens).parse()
    c_code = CTranspiler().transpile(ast)

    with tempfile.TemporaryDirectory() as tmpdir:
        c_file = Path(tmpdir) / "prog.c"
        bin_suffix = ".exe" if sys.platform.startswith("win") else ""
        exe_file = Path(tmpdir) / f"prog{bin_suffix}"
        c_file.write_text(c_code, encoding="utf-8")

        compile_res = subprocess.run(
            [C_COMPILER, str(c_file), "-o", str(exe_file)],
            capture_output=True,
            text=True,
        )
        assert compile_res.returncode == 0, f"C Compilation failed:\n{compile_res.stderr}"

        exec_res = subprocess.run([str(exe_file)], capture_output=True, text=True, check=True)
        return exec_res.stdout


def run_vm(source: str, run_fresh) -> str:
    return run_fresh(source)


def assert_differential(source: str, run_fresh):
    vm_output = run_vm(source, run_fresh).strip()
    native_output = run_c_native(source).strip()
    assert vm_output == native_output, f"Differential mismatch!\nVM: {vm_output!r}\nNative: {native_output!r}"


def test_diff_arithmetic_and_types(run_fresh):
    source = """
    let i = 10 + 20 * 2;
    let f = 3.5 * 2.0;
    let b = i > 40;
    println(i);
    println(f);
    println(b);
    """
    assert_differential(source, run_fresh)


def test_diff_functions_and_recursion(run_fresh):
    source = """
    fn fib(n: int) -> int {
        if (n <= 1) { return n; }
        return fib(n - 1) + fib(n - 2);
    }
    println(fib(10));
    """
    assert_differential(source, run_fresh)


def test_diff_loops(run_fresh):
    source = """
    let sum = 0;
    for (let i = 1; i <= 5; i = i + 1) {
        sum = sum + i;
    }
    println(sum);
    """
    assert_differential(source, run_fresh)


def test_diff_while_break_continue(run_fresh):
    source = """
    let i = 0;
    let count = 0;
    while (i < 10) {
        i = i + 1;
        if (i == 3) {
            continue;
        }
        if (i == 7) {
            break;
        }
        count = count + i;
    }
    println(count);
    """
    assert_differential(source, run_fresh)


def test_diff_structs_nested(run_fresh):
    source = """
    struct Inner { val: int }
    struct Outer { in_obj: Inner, extra: int }
    let o = Outer { in_obj: Inner { val: 42 }, extra: 100 };
    println(o.in_obj.val);
    println(o.extra);
    """
    assert_differential(source, run_fresh)


def test_diff_strings_and_logic(run_fresh):
    source = """
    let s = "hello";
    let cond = true && !false;
    let cond2 = false || (10 > 5);
    println(s);
    println(cond);
    println(cond2);
    """
    assert_differential(source, run_fresh)


def test_diff_division_and_modulo(run_fresh):
    source = """
    let a = 17;
    let b = 5;
    println(a / b);
    println(a % b);
    """
    assert_differential(source, run_fresh)


def test_diff_nested_conditionals(run_fresh):
    source = """
    fn classify(x: int) -> int {
        if (x > 10) {
            if (x > 20) {
                return 3;
            } else {
                return 2;
            }
        }
        return 1;
    }
    println(classify(5));
    println(classify(15));
    println(classify(25));
    """
    assert_differential(source, run_fresh)


def test_diff_nested_scopes_and_shadowing(run_fresh):
    source = """
    let x = 100;
    let y = 50;
    {
        let x = 200;
        let z = x + y;
        println(z);
    }
    println(x);
    """
    assert_differential(source, run_fresh)


def test_diff_helper_functions_with_early_returns(run_fresh):
    source = """
    fn search(n: int) -> int {
        for (let i = 0; i < 10; i = i + 1) {
            if (i == n) {
                return i * 10;
            }
        }
        return -1;
    }
    println(search(3));
    println(search(20));
    """
    assert_differential(source, run_fresh)


def test_diff_struct_mutation_in_functions(run_fresh):
    source = """
    struct Counter { count: int }
    fn advance(c: Counter, amt: int) -> Counter {
        let next_c = Counter { count: c.count + amt };
        return next_c;
    }
    let c = Counter { count: 10 };
    let c2 = advance(c, 5);
    println(c2.count);
    println(c.count);
    """
    assert_differential(source, run_fresh)


def test_diff_arithmetic_precedence_and_negative(run_fresh):
    source = """
    let a = -10 + 5 * -2;
    let b = (100 - 20) / 4 + 3;
    let c = -(a + b);
    println(a);
    println(b);
    println(c);
    """
    assert_differential(source, run_fresh)


