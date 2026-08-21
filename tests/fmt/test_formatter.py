"""Unit test suite for Fresh Code Formatter."""

from fresh.formatter import FreshFormatter


def format_and_check_idempotence(source: str) -> str:
    fmt = FreshFormatter()
    first = fmt.format_source(source)
    second = fmt.format_source(first)
    assert first == second, f"Formatting is not idempotent!\nFirst pass:\n{first}\nSecond pass:\n{second}"
    return first


def test_formatter_variable_declarations():
    source = "let    x :  int   = 42  ;"
    formatted = format_and_check_idempotence(source)
    assert formatted.strip() == "let x: int = 42;"


def test_formatter_functions():
    source = """
    fn  add ( a : int , b : int ) -> int {
    return   a  +  b ;
    }
    """
    formatted = format_and_check_idempotence(source)
    assert "fn add(a: int, b: int) -> int {" in formatted
    assert "    return a + b;" in formatted


def test_formatter_structs():
    source = "struct   Point  {   x : float ,  y : float  }"
    formatted = format_and_check_idempotence(source)
    assert formatted.strip() == "struct Point { x: float, y: float }"


def test_formatter_conditionals_and_loops():
    source = """
    if ( x > 0 ) {
    let y = x * 2 ;
    } else {
    let y = 0 ;
    }
    """
    formatted = format_and_check_idempotence(source)
    assert "if (x > 0) {" in formatted
    assert "    let y = x * 2;" in formatted
    assert "} else {" in formatted


def test_formatter_arrays_and_struct_literals():
    source = """
    let arr = [ 1 , 2 , 3 ] ;
    let p = Point { x : 1.0 , y : 2.0 } ;
    """
    formatted = format_and_check_idempotence(source)
    assert "let arr = [1, 2, 3];" in formatted
    assert "let p = Point { x: 1.0, y: 2.0 };" in formatted
