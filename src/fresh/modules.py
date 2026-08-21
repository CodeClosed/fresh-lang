"""Module Resolution and Dependency Loader for Fresh.

Handles module imports, relative file resolution, duplicate caching,
and circular dependency detection [E4001].
"""

from __future__ import annotations

from pathlib import Path

from fresh.common.errors import FreshSyntaxError
from fresh.lexer.scanner import Scanner
from fresh.parser.ast import ImportStmt, Stmt
from fresh.parser.parser import Parser


class ModuleLoader:
    """Resolves and loads module dependencies into a unified AST statement list."""

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir = base_dir or Path.cwd()
        self.loaded_modules: dict[str, list[Stmt]] = {}

    def load_program_with_imports(
        self,
        source: str,
        filename: str = "<stdin>",
        import_chain: list[str] | None = None,
    ) -> list[Stmt]:
        """Parse source and recursively resolve imported module statements."""
        if import_chain is None:
            import_chain = [filename]

        tokens = Scanner(source, filename).scan_tokens()
        statements = Parser(tokens, filename).parse()

        expanded_stmts: list[Stmt] = []

        for stmt in statements:
            if isinstance(stmt, ImportStmt):
                mod_name = str(stmt.module_token.value or stmt.module_token.lexeme)
                imported_path = self._resolve_module_path(mod_name, filename)

                canonical_path = str(imported_path.resolve())

                # Check for circular dependency
                if canonical_path in import_chain:
                    cycle_repr = " -> ".join(import_chain + [canonical_path])
                    raise FreshSyntaxError(
                        message=f"[E4001] Circular module dependency detected: {cycle_repr}",
                        line=stmt.keyword.line,
                        column=stmt.keyword.column,
                        filename=filename,
                    )

                # Use cached module if already loaded (do not re-expand identical module statements)
                if canonical_path in self.loaded_modules:
                    continue

                if not imported_path.exists():
                    raise FreshSyntaxError(
                        message=f"Cannot find module '{mod_name}' at path '{imported_path}'.",
                        line=stmt.keyword.line,
                        column=stmt.keyword.column,
                        filename=filename,
                    )

                mod_source = imported_path.read_text(encoding="utf-8")
                mod_stmts = self.load_program_with_imports(
                    mod_source,
                    filename=canonical_path,
                    import_chain=import_chain + [canonical_path],
                )

                self.loaded_modules[canonical_path] = mod_stmts
                expanded_stmts.extend(mod_stmts)
            else:
                expanded_stmts.append(stmt)

        return expanded_stmts

    def _resolve_module_path(self, mod_name: str, current_file: str) -> Path:
        """Resolve module name/path relative to current file or base dir."""
        current_dir = Path(current_file).parent if current_file != "<stdin>" else self.base_dir

        if mod_name.endswith(".fresh"):
            candidates = [current_dir / mod_name, self.base_dir / mod_name]
        else:
            candidates = [
                current_dir / f"{mod_name}.fresh",
                self.base_dir / f"{mod_name}.fresh",
                current_dir / mod_name,
                self.base_dir / mod_name,
            ]



        for cand in candidates:
            if cand.exists():
                return cand

        return candidates[0]

