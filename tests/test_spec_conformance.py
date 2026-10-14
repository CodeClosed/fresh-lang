"""Conformance tests for normative code examples in docs/specification.md."""



def test_spec_section_6_closures(run_fresh):
    source = """
    fn make_counter() -> fn {
        let count = 0;
        fn inc() -> int {
            count = count + 1;
            return count;
        }
        return inc;
    }
    let counter = make_counter();
    println(counter());
    println(counter());
    """
    output = run_fresh(source)
    assert output.strip().splitlines() == ["1", "2"]


def test_spec_section_7_match_guards(run_fresh):
    source = """
    let val = 42;
    let category = match val {
        v if v > 100 => "big",
        v if v > 10 => "medium",
        _ => "small",
    };
    println(category);
    """
    output = run_fresh(source)
    assert output.strip() == "medium"


def test_spec_section_2_escape_sequences(run_fresh):
    source = """
    let msg = "Hello\\nWorld\\t!";
    println(msg);
    """
    output = run_fresh(source)
    assert output.strip() == "Hello\nWorld\t!"


def test_spec_section_4_precedence(run_fresh):
    source = """
    let res = 2 + 3 * 4;
    println(res);
    """
    output = run_fresh(source)
    assert output.strip() == "14"


def test_spec_section_10_stdlib_math_and_builtins(run_fresh):
    source = """
    let a = [10, 20];
    push(a, 30);
    println(len(a));
    println(pop(a));
    println(abs(-42));
    println(min(5, 10));
    println(max(5, 10));
    """
    output = run_fresh(source)
    assert output.strip().splitlines() == ["3", "30", "42", "5", "10"]


def test_spec_trailing_commas(run_fresh):
    source = """
    let arr = [1, 2, 3,];
    println(len(arr));
    """
    output = run_fresh(source)
    assert output.strip() == "3"


def test_spec_truthiness(run_fresh):
    source = """
    if (1) {
        println("number is truthy");
    }
    if ("hello") {
        println("string is truthy");
    }
    """
    output = run_fresh(source)
    assert output.strip().splitlines() == ["number is truthy", "string is truthy"]


def test_spec_array_type_promotion(run_fresh):
    source = """
    let arr = [1, 2.5, 3];
    println(len(arr));
    """
    output = run_fresh(source)
    assert output.strip() == "3"


def test_spec_forward_reference(run_fresh):
    source = """
    fn caller() -> int {
        return target();
    }
    fn target() -> int {
        return 42;
    }
    println(caller());
    """
    output = run_fresh(source)
    assert output.strip() == "42"

