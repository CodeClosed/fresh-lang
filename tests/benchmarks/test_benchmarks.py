"""Performance and regression benchmark suite for Fresh."""

import time

from fresh.analyzer.resolver import Resolver
from fresh.analyzer.type_checker import TypeChecker
from fresh.codegen.c_transpiler import CTranspiler
from fresh.lexer.scanner import Scanner
from fresh.parser.parser import Parser
from fresh.pipeline import run_source


def test_benchmark_lexer_throughput():
    source = "let x: int = 42 + 100 * 2;\n" * 500
    start = time.perf_counter()
    tokens = Scanner(source, filename="<bench>").scan_tokens()
    elapsed = time.perf_counter() - start
    assert len(tokens) > 5000
    assert elapsed < 1.0, f"Lexer throughput too slow: {elapsed:.3f}s"


def test_benchmark_parser_and_typechecker():
    source = "\n".join(f"fn compute_{i}(a: int, b: int) -> int {{ let c = a * b + 10; return c; }}" for i in range(100))
    start = time.perf_counter()
    tokens = Scanner(source, filename="<bench>").scan_tokens()
    ast = Parser(tokens, filename="<bench>").parse()
    Resolver(filename="<bench>").resolve_program(ast)
    checker = TypeChecker(filename="<bench>")
    checker.check_program(ast)
    elapsed = time.perf_counter() - start
    assert len(ast) == 100
    assert elapsed < 1.5, f"Parser/Typechecker too slow: {elapsed:.3f}s"


def test_benchmark_vm_execution():
    source = """
    fn fib(n: int) -> int {
        if (n <= 1) { return n; }
        return fib(n - 1) + fib(n - 2);
    }
    let res = fib(18);
    """
    start = time.perf_counter()
    run_source(source, filename="<bench>")
    elapsed = time.perf_counter() - start
    assert elapsed < 2.0, f"VM execution too slow: {elapsed:.3f}s"


def test_benchmark_c_transpilation():
    source = """
    struct Point { x: float, y: float }
    fn dist_sq(p: Point) -> float {
        return p.x * p.x + p.y * p.y;
    }
    let p = Point { x: 3.0, y: 4.0 };
    println(dist_sq(p));
    """
    tokens = Scanner(source).scan_tokens()
    ast = Parser(tokens).parse()
    start = time.perf_counter()
    c_code = CTranspiler().transpile(ast)
    elapsed = time.perf_counter() - start
    assert "typedef struct Point" in c_code
    assert elapsed < 0.5, f"Transpilation too slow: {elapsed:.3f}s"
