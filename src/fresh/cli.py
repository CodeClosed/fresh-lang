"""Command Line Interface for the Fresh Programming Language."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from fresh.analyzer.resolver import Resolver
from fresh.analyzer.type_checker import TypeChecker
from fresh.formatter import FreshFormatter
from fresh.package import PackageManager
from fresh.pipeline import run_source
from fresh.stdlib.builtins import register_builtins
from fresh.stdlib.math_lib import register_math_lib
from fresh.vm.value import value_to_string
from fresh.vm.vm import VM

EXIT_SUCCESS = 0
EXIT_USER_ERROR = 1
EXIT_USAGE_ERROR = 2
EXIT_TOOLCHAIN_ERROR = 3
EXIT_ICE = 70


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="fresh",
        description="Fresh Programming Language - Compiler & Bytecode VM",
    )
    parser.add_argument("--debug", action="store_true", help="Enable verbose internal traceback reporting")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # `fresh run <file>`
    run_parser = subparsers.add_parser("run", help="Run a Fresh source file")
    run_parser.add_argument("file", type=str, help="Path to .fresh source file")
    run_parser.add_argument("--dump-tokens", action="store_true", help="Print token stream")
    run_parser.add_argument("--dump-ast", action="store_true", help="Print Abstract Syntax Tree")
    run_parser.add_argument("--disassemble", action="store_true", help="Print disassembled bytecode")
    run_parser.add_argument("--emit-c", action="store_true", help="Transpile Fresh source to C code")

    # `fresh check <file>`
    check_parser = subparsers.add_parser("check", help="Type check and analyze a Fresh source file without execution")
    check_parser.add_argument("file", type=str, help="Path to .fresh source file")

    # `fresh fmt <file>`
    fmt_parser = subparsers.add_parser("fmt", help="Format a Fresh source file")
    fmt_parser.add_argument("file", type=str, help="Path to .fresh source file")
    fmt_parser.add_argument("--check", action="store_true", help="Check if file is formatted without overwriting")

    # `fresh init <name>`
    init_parser = subparsers.add_parser("init", help="Initialize a new Fresh project")
    init_parser.add_argument("name", type=str, help="Project name")
    init_parser.add_argument("--dir", type=str, default=".", help="Target directory")

    # `fresh build [path]`
    build_parser = subparsers.add_parser("build", help="Build a Fresh project")
    build_parser.add_argument("path", type=str, nargs="?", default=".", help="Path to project root")

    # `fresh test [dir]`
    test_parser = subparsers.add_parser("test", help="Run automated test suite")
    test_parser.add_argument("path", type=str, nargs="?", default="tests", help="Path to test directory")

    # `fresh repl`
    subparsers.add_parser("repl", help="Start interactive Fresh REPL")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(EXIT_SUCCESS)

    try:
        if args.command == "run":
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"Error: File '{args.file}' not found.", file=sys.stderr)
                sys.exit(EXIT_USER_ERROR)

            source = file_path.read_text(encoding="utf-8")
            if args.emit_c:
                from fresh.codegen.c_transpiler import CTranspiler
                from fresh.modules import ModuleLoader

                ast = ModuleLoader(base_dir=file_path.parent).load_program_with_imports(
                    source, filename=str(file_path)
                )
                c_code = CTranspiler(filename=str(file_path)).transpile(ast)
                print(c_code)
                sys.exit(EXIT_SUCCESS)

            run_source(
                source,
                filename=str(file_path),
                dump_tokens=args.dump_tokens,
                dump_ast=args.dump_ast,
                disassemble=args.disassemble,
            )
            sys.exit(EXIT_SUCCESS)

        elif args.command == "check":
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"Error: File '{args.file}' not found.", file=sys.stderr)
                sys.exit(EXIT_USER_ERROR)

            source = file_path.read_text(encoding="utf-8")
            from fresh.modules import ModuleLoader

            ast = ModuleLoader(base_dir=file_path.parent).load_program_with_imports(
                source, filename=str(file_path)
            )
            Resolver(filename=str(file_path)).resolve_program(ast)
            TypeChecker(filename=str(file_path)).check_program(ast)
            print(f"Check passed for '{file_path}'.")
            sys.exit(EXIT_SUCCESS)

        elif args.command == "fmt":
            file_path = Path(args.file)
            if not file_path.exists():
                print(f"Error: File '{args.file}' not found.", file=sys.stderr)
                sys.exit(EXIT_USER_ERROR)

            source = file_path.read_text(encoding="utf-8")
            formatted = FreshFormatter().format_source(source)
            if args.check:
                if formatted != source:
                    print(f"Formatting needed for '{file_path}'.", file=sys.stderr)
                    sys.exit(EXIT_USER_ERROR)
                else:
                    print(f"File '{file_path}' is correctly formatted.")
                    sys.exit(EXIT_SUCCESS)
            else:
                file_path.write_text(formatted, encoding="utf-8")
                print(f"Formatted '{file_path}'.")
                sys.exit(EXIT_SUCCESS)

        elif args.command == "init":
            target_dir = Path(args.dir)
            created_dir = PackageManager.init_project(args.name, target_dir)
            print(f"Initialized new Fresh project '{args.name}' in '{created_dir}'.")
            sys.exit(EXIT_SUCCESS)

        elif args.command == "build":
            project_dir = Path(args.path)
            output_file = PackageManager.build_project(project_dir)
            print(f"Build succeeded: '{output_file}'.")
            sys.exit(EXIT_SUCCESS)

        elif args.command == "test":
            cmd = [sys.executable, "-m", "pytest", args.path]
            res = subprocess.run(cmd)
            sys.exit(res.returncode)

        elif args.command == "repl":
            start_repl()

    except SystemExit:
        raise
    except Exception as e:
        from fresh.common.errors import FreshError
        if isinstance(e, FreshError):
            print(e, file=sys.stderr)
            sys.exit(EXIT_USER_ERROR)
        elif isinstance(e, (FileNotFoundError, RuntimeError)):
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(EXIT_TOOLCHAIN_ERROR)
        else:
            if getattr(args, "debug", False):
                import traceback
                traceback.print_exc()
            else:
                print(f"internal compiler error (ICE): {e}\n(Run with --debug for stack traceback)", file=sys.stderr)
            sys.exit(EXIT_ICE)


def start_repl() -> None:
    """Interactive Read-Eval-Print Loop (REPL)."""
    print("Fresh Programming Language v0.1.0")
    print("Type 'exit()' or Ctrl+C to quit.\n")

    vm = VM()
    register_builtins(vm)
    register_math_lib(vm)

    while True:
        try:
            line = input("fresh> ")
            if line.strip() in ("exit()", "exit"):
                break
            if not line.strip():
                continue

            result = run_source(line, filename="<repl>", vm_instance=vm)
            if result is not None:
                print(value_to_string(result))

        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break
        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()
