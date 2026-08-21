"""Unit and integration test suite for Fresh C Transpiler."""

import pytest

from fresh.codegen.c_transpiler import CTranspiler
from fresh.common.errors import FreshCodegenError
from fresh.lexer.scanner import Scanner
from fresh.parser.parser import Parser


def transpile_source(source: str) -> str:
    tokens = Scanner(source).scan_tokens()
    ast = Parser(tokens).parse()
    return CTranspiler().transpile(ast)


def test_transpile_basic_types_and_println():
    code = transpile_source("""
    let i = 42;
    let f = 3.14;
    let s = "hello";
    let b = true;
    println(i);
    println(f);
    println(s);
    println(b);
    """)
    assert "long long i = 42;" in code
    assert "double f = 3.14;" in code
    assert 'const char* s = "hello";' in code
    assert "bool b = true;" in code
    assert "println_int(i)" in code
    assert "println_float(f)" in code
    assert "println_str(s)" in code
    assert "println_bool(b)" in code


def test_transpile_struct():
    code = transpile_source("""
    struct Point { x: float, y: float }
    let p = Point { x: 1.0, y: 2.0 };
    """)
    assert "typedef struct Point {" in code
    assert "double x;" in code
    assert "double y;" in code
    assert "} Point;" in code
    assert "(Point){ .x = 1.0, .y = 2.0 }" in code


def test_rejects_unsupported_match_expr():
    source = """
    fn check_val(val: int) -> string {
        let category = match val {
            _ => "small",
        };
        return category;
    }
    """
    tokens = Scanner(source).scan_tokens()
    ast = Parser(tokens).parse()

    with pytest.raises(FreshCodegenError) as excinfo:
        CTranspiler().transpile(ast)

    assert "MatchExpr" in str(excinfo.value)
    assert "[E3001]" in str(excinfo.value)


def test_rejects_unsupported_lambda_expr():
    source = """
    fn run() {
        let f = fn(x: int) -> int { return x + 1; };
    }
    """
    tokens = Scanner(source).scan_tokens()
    ast = Parser(tokens).parse()

    with pytest.raises(FreshCodegenError) as excinfo:
        CTranspiler().transpile(ast)

    assert "LambdaExpr" in str(excinfo.value)
    assert "[E3001]" in str(excinfo.value)


def test_transpile_safe_division_and_modulo():
    code = transpile_source("""
    let a = 10;
    let b = 2;
    let c = a / b;
    let d = a % b;
    println(c);
    println(d);
    """)
    assert "fresh_div_int(a, b)" in code
    assert "fresh_mod_int(a, b)" in code


def test_transpile_typed_ir_nested_scopes_and_shadowing():
    code = transpile_source("""
    let x = 10;
    {
        let x = 3.14;
        println(x);
    }
    println(x);
    """)
    assert "println_float(x)" in code
    assert "println_int(x)" in code


def test_transpile_c_keyword_mangling():
    code = transpile_source("""
    let auto = 10;
    let register = 20;
    let volatile = auto + register;
    println(volatile);
    """)
    assert "long long f_auto = 10;" in code
    assert "long long f_register = 20;" in code
    assert "long long f_volatile = (f_auto + f_register);" in code
    assert "println_int(f_volatile)" in code



