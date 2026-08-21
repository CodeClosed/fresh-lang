"""Fuzz testing suite for Fresh Lexer, Parser, Resolver, and TypeChecker."""

import random
import string

import pytest

from fresh.analyzer.resolver import Resolver
from fresh.analyzer.type_checker import TypeChecker
from fresh.common.errors import FreshError
from fresh.lexer.scanner import Scanner
from fresh.parser.parser import Parser


def generate_random_text(length: int = 100) -> str:
    chars = string.printable + "😀🚀🔥\x00\x01\x02\xFF"
    return "".join(random.choice(chars) for _ in range(length))


def test_fuzz_lexer():
    random.seed(42)
    for _ in range(200):
        source = generate_random_text(random.randint(1, 200))
        try:
            tokens = Scanner(source, filename="<fuzz>").scan_tokens()
            assert len(tokens) >= 1  # Always ends with EOF token
        except FreshError:
            pass  # Controlled scanner error is allowed
        except Exception as e:
            pytest.fail(f"Unhandled exception in lexer for input {source!r}: {e}")


def test_fuzz_parser():
    random.seed(42)
    sample_tokens = [
        "let", "fn", "struct", "if", "else", "while", "for", "return", "match",
        "x", "y", "42", "3.14", "\"hello\"", "true", "false", "=", "+", "-", "*", "/",
        "(", ")", "{", "}", "[", "]", ":", ";", ",", "=>", "_", "!", "&&", "||"
    ]

    for _ in range(200):
        tok_list = [random.choice(sample_tokens) for _ in range(random.randint(1, 50))]
        source = " ".join(tok_list)
        try:
            tokens = Scanner(source, filename="<fuzz>").scan_tokens()
            _ = Parser(tokens, filename="<fuzz>").parse()
        except FreshError:
            pass  # Controlled syntax error is allowed
        except Exception as e:
            pytest.fail(f"Unhandled exception in parser for input {source!r}: {e}")


def test_fuzz_semantic_pipeline():
    random.seed(42)
    sample_stmts = [
        "let x = 10;",
        "let y = x + 5;",
        "fn f(a: int) -> int { return a * 2; }",
        "let s = \"str\";",
        "let b = true;",
        "if (b) { let z = 1; }",
        "for (let i = 0; i < 5; i = i + 1) { let k = i; }",
        "struct Pt { x: int }",
    ]

    for _ in range(100):
        stmts = [random.choice(sample_stmts) for _ in range(random.randint(1, 10))]
        source = "\n".join(stmts)
        try:
            tokens = Scanner(source, filename="<fuzz>").scan_tokens()
            ast = Parser(tokens, filename="<fuzz>").parse()
            Resolver(filename="<fuzz>").resolve_program(ast)
            TypeChecker(filename="<fuzz>").check_program(ast)
        except FreshError:
            pass
        except Exception as e:
            pytest.fail(f"Unhandled exception in semantic pipeline for input {source!r}: {e}")
