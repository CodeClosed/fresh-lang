"""Optimizer equivalence test suite for Fresh."""

from fresh.analyzer.resolver import Resolver
from fresh.analyzer.type_checker import TypeChecker
from fresh.codegen.compiler import Compiler
from fresh.lexer.scanner import Scanner
from fresh.parser.parser import Parser
from fresh.stdlib.builtins import register_builtins
from fresh.stdlib.math_lib import register_math_lib
from fresh.vm.objects import ObjFunction
from fresh.vm.vm import VM


def execute_unoptimized(source: str, run_fresh) -> str:
    tokens = Scanner(source).scan_tokens()
    ast = Parser(tokens).parse()
    Resolver().resolve_program(ast)
    checker = TypeChecker()
    checker.check_program(ast)
    unoptimized_chunk = Compiler().compile_program(ast)

    vm = VM()
    register_builtins(vm)
    register_math_lib(vm)

    # Capture stdout
    import io
    import sys
    buf = io.StringIO()
    old_stdout = sys.stdout
    try:
        sys.stdout = buf
        vm.interpret(ObjFunction("<main>", 0, unoptimized_chunk))
    finally:
        sys.stdout = old_stdout

    return buf.getvalue()


def test_optimizer_constant_folding(run_fresh):
    source = """
    let val = (10 + 20) * 3 - (100 / 2);
    println(val);
    """
    unopt_output = execute_unoptimized(source, run_fresh)
    opt_output = run_fresh(source)
    assert unopt_output == opt_output


def test_optimizer_loops_and_conditionals(run_fresh):
    source = """
    let sum = 0;
    for (let i = 1; i <= 10; i = i + 1) {
        if (i % 2 == 0) {
            sum = sum + i;
        }
    }
    println(sum);
    """
    unopt_output = execute_unoptimized(source, run_fresh)
    opt_output = run_fresh(source)
    assert unopt_output == opt_output


def test_optimizer_functions_equivalence(run_fresh):
    source = """
    fn fact(n: int) -> int {
        if (n <= 1) { return 1; }
        return n * fact(n - 1);
    }
    println(fact(6));
    """
    unopt_output = execute_unoptimized(source, run_fresh)
    opt_output = run_fresh(source)
    assert unopt_output == opt_output
