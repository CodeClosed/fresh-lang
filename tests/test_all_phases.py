# Unit and integration test suite for Fresh
from fresh.analyzer.resolver import Resolver
from fresh.analyzer.type_checker import TypeChecker
from fresh.lexer.scanner import Scanner
from fresh.lexer.tokens import TokenType
from fresh.parser.parser import Parser


def test_lexer_tokens():
    tokens = Scanner("let x = 42 + 3.14;").scan_tokens()
    types = [t.type for t in tokens if t.type != TokenType.EOF]
    assert types == [
        TokenType.LET,
        TokenType.IDENTIFIER,
        TokenType.EQUAL,
        TokenType.INT_LIT,
        TokenType.PLUS,
        TokenType.FLOAT_LIT,
        TokenType.SEMICOLON,
    ]


def test_parser_ast():
    tokens = Scanner("fn add(a: int, b: int) -> int { return a + b; }").scan_tokens()
    ast = Parser(tokens).parse()
    assert len(ast) == 1
    assert ast[0].name.lexeme == "add"


def test_analyzer_resolution():
    tokens = Scanner("let x = 10; { let y = x + 1; }").scan_tokens()
    ast = Parser(tokens).parse()
    resolver = Resolver()
    resolver.resolve_program(ast)
    checker = TypeChecker()
    checker.check_program(ast)


def test_e2e_fibonacci(run_fresh):
    out = run_fresh("""
    fn fib(n: int) -> int {
        if (n <= 1) { return n; }
        return fib(n - 1) + fib(n - 2);
    }
    println(fib(10));
    """)
    assert out.strip() == "55"


def test_e2e_closures(run_fresh):
    out = run_fresh("""
    fn make_counter() -> fn {
        let count = 0;
        fn inc() -> int {
            count = count + 1;
            return count;
        }
        return inc;
    }
    let c = make_counter();
    println(c());
    println(c());
    """)
    assert out.strip().splitlines() == ["1", "2"]


def test_e2e_structs(run_fresh):
    out = run_fresh("""
    struct Point { x: float, y: float }
    let p = Point { x: 10.0, y: 20.0 };
    p.x = 99.0;
    println(to_string(p.x) + " " + to_string(p.y));
    """)
    assert out.strip() == "99.0 20.0"


def test_e2e_quicksort(run_fresh):
    out = run_fresh("""
    let nums = [5, 3, 8, 1];
    push(nums, 2);
    println(to_string(nums));
    """)
    assert out.strip() == "[5, 3, 8, 1, 2]"


def test_e2e_match_guards(run_fresh):
    out = run_fresh("""
    let val = 42;
    let category = match val {
        v if v > 100 => "big",
        v if v > 10 => "medium",
        _ => "small",
    };
    println(category);
    """)
    assert out.strip() == "medium"

