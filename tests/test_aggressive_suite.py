"""Aggressive and comprehensive test suite for all Fresh language features and subsystem integrations."""

import os
import tempfile
import pytest
from pathlib import Path

from fresh.pipeline import run_source
from fresh.formatter import FreshFormatter
from fresh.analyzer.type_checker import TypeChecker
from fresh.analyzer.resolver import Resolver
from fresh.lexer.scanner import Scanner
from fresh.parser.parser import Parser
from fresh.codegen.c_transpiler import CTranspiler
from fresh.common.errors import FreshError


STRESS_PROGRAM = """
// =========================================================================
// 1. Primitive Arithmetic, Precedence & Logic
// =========================================================================
let a = 10;
let b = 25;
let c = -5;
let arith = (a * b + (100 / c) - (b % 4)) * -1;
if (arith != -229) {
    println("FAIL: Arithmetic mismatch " + to_string(arith));
}

let logic = (a < b && c < 0) || (a == b && false) || !(b > 100);
if (!logic) {
    println("FAIL: Logic expression failed");
}

// =========================================================================
// 2. Control Flow: Nested Loops, Breaks, Continues
// =========================================================================
let loop_sum = 0;
for (let i = 0; i < 15; i = i + 1) {
    if (i % 2 == 0) {
        continue;
    }
    if (i > 11) {
        break;
    }
    let j = 0;
    while (j < 3) {
        loop_sum = loop_sum + i * 10 + j;
        j = j + 1;
    }
}
// Odd i: 1, 3, 5, 7, 9, 11
// For each i: (i*10+0) + (i*10+1) + (i*10+2) = 30*i + 3
// Sum = (30*(1+3+5+7+9+11)) + (3 * 6) = 30 * 36 + 18 = 1080 + 18 = 1098
if (loop_sum != 1098) {
    println("FAIL: Loop sum mismatch " + to_string(loop_sum));
}

// =========================================================================
// 3. Closures, Upvalues & Independent Mutable State
// =========================================================================
fn make_accumulator(start: int) -> fn {
    let current = start;
    fn add_and_get(delta: int) -> int {
        current = current + delta;
        return current;
    }
    return add_and_get;
}

let acc1 = make_accumulator(100);
let acc2 = make_accumulator(500);

let a1_step1 = acc1(50);
let a2_step1 = acc2(25);
let a1_step2 = acc1(-30);
let a2_step2 = acc2(100);

if (a1_step1 != 150 || a2_step1 != 525 || a1_step2 != 120 || a2_step2 != 625) {
    println("FAIL: Closure accumulator state corrupted");
}

// =========================================================================
// 4. Higher-Order Functions: Custom Map & Filter with Closures
// =========================================================================
fn apply_map(arr: [int], transform: fn) -> [int] {
    let result: [int] = [];
    for (let i = 0; i < len(arr); i = i + 1) {
        push(result, transform(arr[i]));
    }
    return result;
}

fn apply_filter(arr: [int], predicate: fn) -> [int] {
    let result: [int] = [];
    for (let i = 0; i < len(arr); i = i + 1) {
        if (predicate(arr[i])) {
            push(result, arr[i]);
        }
    }
    return result;
}

let numbers: [int] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
let double_fn = fn(x: int) -> int { return x * 2; };
let is_even_fn = fn(x: int) -> bool { return x % 2 == 0; };

let evens = apply_filter(numbers, is_even_fn);
let doubled_evens = apply_map(evens, double_fn);

if (len(doubled_evens) != 5 || doubled_evens[0] != 4 || doubled_evens[4] != 20) {
    println("FAIL: Higher-order functions mismatch");
}

// =========================================================================
// 5. Deep Recursion: Ackermann & Factorial
// =========================================================================
fn factorial(n: int) -> int {
    if (n <= 1) { return 1; }
    return n * factorial(n - 1);
}

fn ackermann(m: int, n: int) -> int {
    if (m == 0) {
        return n + 1;
    } else {
        if (m > 0 && n == 0) {
            return ackermann(m - 1, 1);
        } else {
            return ackermann(m - 1, ackermann(m, n - 1));
        }
    }
}

if (factorial(6) != 720) {
    println("FAIL: Factorial(6) != 720");
}
if (ackermann(2, 3) != 9) {
    println("FAIL: Ackermann(2, 3) != 9");
}

// =========================================================================
// 6. Structs, Mutation & Nested Structures
// =========================================================================
struct Vec2 { x: float, y: float }
struct Particle { pos: Vec2, vel: Vec2, mass: float }

fn step_particle(p: Particle, dt: float) -> Particle {
    let new_x = p.pos.x + p.vel.x * dt;
    let new_y = p.pos.y + p.vel.y * dt;
    p.pos.x = new_x;
    p.pos.y = new_y;
    return p;
}

let p1 = Particle {
    pos: Vec2 { x: 0.0, y: 10.0 },
    vel: Vec2 { x: 5.0, y: -2.0 },
    mass: 1.5
};

step_particle(p1, 2.0);
if (p1.pos.x != 10.0 || p1.pos.y != 6.0) {
    println("FAIL: Struct mutation failed");
}

// =========================================================================
// 7. Dynamic Arrays, Matrices & Pop/Push Mechanics
// =========================================================================
let grid = [[1, 2, 3], [4, 5, 6], [7, 8, 9]];
grid[1][1] = 99;
let sum_diag = grid[0][0] + grid[1][1] + grid[2][2];
if (sum_diag != 109) {
    println("FAIL: Matrix access failed");
}

let stack: [int] = [];
for (let s = 0; s < 50; s = s + 1) {
    push(stack, s * 3);
}
if (len(stack) != 50) {
    println("FAIL: Stack length mismatch");
}

let popped_val = pop(stack);
if (popped_val != 147 || len(stack) != 49) {
    println("FAIL: Stack pop mismatch");
}

// =========================================================================
// 8. Pattern Matching with Expressions & Guards
// =========================================================================
fn classify_status(code: int, active: bool) -> string {
    return match code {
        200 if active => "ACTIVE_SUCCESS",
        200 if !active => "INACTIVE_SUCCESS",
        404 => "RESOURCE_MISSING",
        c if c >= 500 && c < 600 => "INTERNAL_SERVER_ERROR",
        _ => "OTHER"
    };
}

if (classify_status(200, true) != "ACTIVE_SUCCESS") {
    println("FAIL: Match 200 true");
}
if (classify_status(200, false) != "INACTIVE_SUCCESS") {
    println("FAIL: Match 200 false");
}
if (classify_status(404, true) != "RESOURCE_MISSING") {
    println("FAIL: Match 404");
}
if (classify_status(503, false) != "INTERNAL_SERVER_ERROR") {
    println("FAIL: Match 503 guard");
}
if (classify_status(100, true) != "OTHER") {
    println("FAIL: Match wildcard");
}

// =========================================================================
// 9. Standard Math Library & Builtins
// =========================================================================
let m_abs = abs(-42.7);
let m_sqrt = sqrt(16.0);
let m_pow = pow(2.0, 10.0);
let m_min = min(100, 25);
let m_max = max(100, 25);
let m_floor = floor(5.8);
let m_ceil = ceil(5.2);
let m_round = round(5.5);

if (m_abs != 42.7 || m_sqrt != 4.0 || m_pow != 1024.0 || m_min != 25 || m_max != 100) {
    println("FAIL: Math functions basic");
}
if (m_floor != 5.0 || m_ceil != 6.0 || m_round != 6.0) {
    println("FAIL: Math functions rounding");
}

// =========================================================================
// 10. Type Checking & to_string
// =========================================================================
if (type(10) != "int" || type(3.14) != "float" || type("str") != "string" || type(true) != "bool") {
    println("FAIL: Built-in type() inspector");
}

println("AGGRESSIVE_STRESS_TEST_ALL_PASSED");
"""


def test_aggressive_full_language_execution(capsys):
    """Test entire language suite end-to-end through pipeline."""
    run_source(STRESS_PROGRAM, filename="stress.fresh", gc_stress=False)
    out = capsys.readouterr().out
    assert "FAIL" not in out
    assert "AGGRESSIVE_STRESS_TEST_ALL_PASSED" in out


def test_aggressive_gc_stress_mode(capsys):
    """Test full execution with GC forced on EVERY single allocation."""
    run_source(STRESS_PROGRAM, filename="stress_gc.fresh", gc_stress=True)
    out = capsys.readouterr().out
    assert "FAIL" not in out
    assert "AGGRESSIVE_STRESS_TEST_ALL_PASSED" in out


def test_formatter_idempotency():
    """Verify that formatting is completely idempotent on stress code."""
    formatter = FreshFormatter()
    pass1 = formatter.format_source(STRESS_PROGRAM)
    pass2 = formatter.format_source(pass1)
    assert pass1 == pass2, "Formatter must produce stable idempotent output"


C_STRESS_PROGRAM = """
struct Vec2 { x: float, y: float }
struct Particle { pos: Vec2, mass: float }

fn factorial(n: int) -> int {
    if (n <= 1) { return 1; }
    return n * factorial(n - 1);
}

fn compute() -> int {
    let sum = 0;
    for (let i = 0; i < 10; i = i + 1) {
        if (i == 2) { continue; }
        if (i == 8) { break; }
        sum = sum + i;
    }
    return sum;
}

let f = factorial(5);
let s = compute();
let p = Particle { pos: Vec2 { x: 1.0, y: 2.0 }, mass: 5.5 };
p.pos.x = 10.5;
println(f);
println(s);
println(p.pos.x);
println("C_CODEGEN_STRESS_PASSED");
"""


def test_transpiler_c_codegen_validity():
    """Ensure transpiler converts supported stress code to syntactically valid C."""
    tokens = Scanner(C_STRESS_PROGRAM, "stress_c.fresh").scan_tokens()
    ast = Parser(tokens, "stress_c.fresh").parse()
    Resolver("stress_c.fresh").resolve_program(ast)
    TypeChecker("stress_c.fresh").check_program(ast)
    c_code = CTranspiler("stress_c.fresh").transpile(ast)
    assert "int main(" in c_code
    assert "C_CODEGEN_STRESS_PASSED" in c_code


def test_negative_type_checker_scenarios():
    """Aggressively verify type safety and diagnostics for invalid cases."""
    invalid_cases = [
        ('let x: int = "hello";', "Cannot initialize variable"),
        ('fn foo(a: int) -> int { return true; }', "expected return type"),
        ('let arr: [int] = [1, 2, "bad"];', "Array element type mismatch"),
        ('struct Point { x: int } let p = Point { x: 10 }; p.unknown = 5;', "has no field"),
        ('let c = 10; c();', "Cannot call non-function type"),
        ('let a = 10 + "foo";', "Operator '+' not supported"),
    ]



    for code, expected_error in invalid_cases:
        tokens = Scanner(code, "<test>").scan_tokens()
        ast = Parser(tokens, "<test>").parse()
        Resolver("<test>").resolve_program(ast)
        checker = TypeChecker("<test>")
        with pytest.raises(FreshError) as exc_info:
            checker.check_program(ast)
        assert expected_error.lower() in str(exc_info.value).lower(), (
            f"Expected error {expected_error!r} for code {code!r}, got: {exc_info.value}"
        )



def test_file_io_system_builtins(capsys):
    """Aggressively test file I/O builtins with read/write/exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = os.path.join(tmpdir, "test_file.txt").replace("\\", "/")
        source = f'''
        let path = "{test_path}";
        if (file_exists(path)) {{
            println("FAIL: File should not exist yet");
        }}
        write_file(path, "Hello Fresh IO!\\nLine 2");
        if (!file_exists(path)) {{
            println("FAIL: File should exist after write");
        }}
        let content = read_file(path);
        if (len(content) < 10) {{
            println("FAIL: File content too short");
        }}
        println("FILE_IO_PASSED");
        '''
        run_source(source, filename="io_test.fresh")
        out = capsys.readouterr().out
        assert "FAIL" not in out
        assert "FILE_IO_PASSED" in out

