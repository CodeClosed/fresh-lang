"""Adversarial and malformed source diagnostics test suite for Fresh."""

import pytest

from fresh.common.errors import (
    FreshError,
    FreshNameError,
    FreshRuntimeError,
    FreshSyntaxError,
    FreshTypeError,
)
from fresh.pipeline import run_source


def test_malformed_syntax_incomplete_let():
    source = "let x ="
    with pytest.raises(FreshSyntaxError) as excinfo:
        run_source(source, filename="incomplete_let.fresh")
    err = excinfo.value
    assert isinstance(err, FreshError)
    assert err.line > 0
    assert err.filename == "incomplete_let.fresh"


def test_malformed_syntax_unclosed_fn():
    source = "fn add(a: int, b: int -> int {"
    with pytest.raises(FreshSyntaxError) as excinfo:
        run_source(source, filename="unclosed_fn.fresh")
    err = excinfo.value
    assert isinstance(err, FreshError)
    assert err.line > 0


def test_type_error_mismatched_assignment():
    source = "let x: int = \"hello\";"
    with pytest.raises(FreshTypeError) as excinfo:
        run_source(source, filename="type_mismatch.fresh")
    err = excinfo.value
    assert isinstance(err, FreshError)
    assert err.line > 0
    assert "Cannot initialize variable 'x' of type 'int' with value of type 'string'" in str(err)


def test_name_error_undefined_variable():
    source = "println(undefined_var);"
    with pytest.raises((FreshNameError, FreshRuntimeError)) as excinfo:
        run_source(source, filename="undefined_var.fresh")
    err = excinfo.value
    assert isinstance(err, FreshError)
    assert err.line > 0 or "undefined_var" in str(err)


def test_type_error_invalid_binary_operator():
    source = "let x = true - false;"
    with pytest.raises(FreshTypeError) as excinfo:
        run_source(source, filename="invalid_op.fresh")
    err = excinfo.value
    assert isinstance(err, FreshError)
    assert err.line > 0
    assert "Operator '-' not supported" in str(err)


def test_type_error_invalid_if_condition():
    source = "if (42) { let a = 1; }"
    with pytest.raises(FreshTypeError) as excinfo:
        run_source(source, filename="if_cond.fresh")
    err = excinfo.value
    assert isinstance(err, FreshError)
    assert "If condition must be a boolean" in str(err)

