"""Unified compilation and execution pipeline for Fresh."""

from __future__ import annotations

from typing import Any

from fresh.analyzer.resolver import Resolver
from fresh.analyzer.type_checker import TypeChecker
from fresh.codegen.compiler import Compiler
from fresh.codegen.disassembler import Disassembler
from fresh.codegen.optimizer import Optimizer
from fresh.lexer.scanner import Scanner
from fresh.modules import ModuleLoader
from fresh.parser.ast import ASTPrinter
from fresh.stdlib.builtins import register_builtins
from fresh.stdlib.math_lib import register_math_lib
from fresh.vm.objects import ObjFunction
from fresh.vm.vm import VM


def run_source(
    source: str,
    filename: str = "<stdin>",
    dump_tokens: bool = False,
    dump_ast: bool = False,
    disassemble: bool = False,
    vm_instance: VM | None = None,
    gc_stress: bool = False,
) -> Any:
    """Run a Fresh source string end-to-end through all compilation & execution passes.

    Args:
        source:       Raw Fresh source code text.
        filename:     Source filename for error diagnostics.
        dump_tokens:  If True, print token stream to stdout.
        dump_ast:     If True, print AST tree to stdout.
        disassemble:  If True, print disassembled bytecode to stdout.
        vm_instance:  Optional existing VM (for REPL state persistence).
        gc_stress:    If True, trigger garbage collection on every allocation.

    Returns:
        Result of evaluation.
    """
    # ── Phase 1: Lexical Analysis (Optional Token Dump) ──────
    if dump_tokens:
        scanner = Scanner(source, filename)
        tokens = scanner.scan_tokens()
        print(f"=== TOKENS ({filename}) ===")
        for tok in tokens:
            print(f"  {tok}")
        print()

    # ── Phase 2: Syntax Analysis & Module Resolution ──────────
    ast = ModuleLoader().load_program_with_imports(source, filename)

    if dump_ast:
        print(f"=== AST ({filename}) ===")
        print(ASTPrinter().print_program(ast))
        print()


    # ── Phase 3: Semantic Analysis ────────────────────────────
    resolver = Resolver(filename)
    resolver.resolve_program(ast)

    type_checker = TypeChecker(filename)
    type_checker.check_program(ast)

    # ── Phase 4: Bytecode Compilation & Optimization ──────────
    compiler = Compiler(filename)
    chunk = compiler.compile_program(ast)

    optimizer = Optimizer()
    optimized_chunk = optimizer.optimize(chunk)

    if disassemble:
        print(f"=== DISASSEMBLY ({filename}) ===")
        dis = Disassembler()
        print(dis.disassemble_chunk(optimized_chunk))
        print()

    # ── Phase 5: Virtual Machine Execution ────────────────────
    vm = vm_instance if vm_instance is not None else VM(gc_stress=gc_stress)
    if vm_instance is None:
        register_builtins(vm)
        register_math_lib(vm)


    top_function = ObjFunction("<main>", 0, optimized_chunk)
    return vm.interpret(top_function)
