"""Package and Project Management for Fresh.

Handles project initialization (fresh init), manifest loading (fresh.toml / fresh.toml),
and project building (fresh build).
"""

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

from fresh.codegen.c_transpiler import CTranspiler
from fresh.common.errors import FreshError
from fresh.modules import ModuleLoader


@dataclass
class ProjectManifest:
    """Authoritative validated representation of fresh.toml project manifest."""

    name: str
    version: str = "0.1.0"
    entry: str = "src/main.fresh"
    description: str = ""
    dependencies: dict[str, str | dict[str, str]] = field(default_factory=dict)

    @classmethod
    def load(cls, project_dir: Path) -> "ProjectManifest":
        manifest_file = project_dir / "fresh.toml"

        if not manifest_file.exists():
            return cls(name=project_dir.name)

        try:
            data = tomllib.loads(manifest_file.read_text(encoding="utf-8"))
        except Exception as err:
            raise FreshError(f"Failed to parse fresh.toml: {err}")

        pkg = data.get("package", {})
        name = pkg.get("name", project_dir.name)
        version = pkg.get("version", "0.1.0")
        entry_val = pkg.get("entry", "src/main.fresh")
        description = pkg.get("description", "")
        dependencies = data.get("dependencies", {})

        # Security check: disallow path traversal outside project root
        norm_path = Path(entry_val)
        if norm_path.is_absolute() or ".." in norm_path.parts:
            raise FreshError(f"Security error: Invalid manifest entry path '{entry_val}' cannot escape project root.")

        return cls(
            name=name,
            version=version,
            entry=entry_val,
            description=description,
            dependencies=dependencies,
        )


def find_c_compiler() -> str | None:
    """Detect available C host compiler across environments."""
    for env_var in ("FRESH_CC", "CC"):
        val = os.environ.get(env_var)
        if val and shutil.which(val):
            return shutil.which(val)

    for cc in ("gcc", "clang", "cl"):
        found = shutil.which(cc)
        if found:
            return found

    # Windows fallback locations (MSYS2 / MinGW)
    if sys.platform.startswith("win"):
        for win_path in (
            r"C:\msys64\ucrt64\bin\gcc.exe",
            r"C:\msys64\mingw64\bin\gcc.exe",
            r"C:\MinGW\bin\gcc.exe",
        ):
            if Path(win_path).exists():
                return win_path

    return None


class PackageManager:
    """Manages Fresh project lifecycle: init, config, and build."""

    @staticmethod
    def init_project(name: str, destination: Path) -> Path:
        """Create a new standard Fresh project structure."""
        project_dir = destination / name if destination.name != name else destination
        project_dir.mkdir(parents=True, exist_ok=True)

        src_dir = project_dir / "src"
        src_dir.mkdir(exist_ok=True)

        tests_dir = project_dir / "tests"
        tests_dir.mkdir(exist_ok=True)

        # 1. Manifest: fresh.toml
        manifest_content = f"""[package]
name = "{name}"
version = "0.1.0"
description = "A Fresh project"
entry = "src/main.fresh"

# Third-party package registry dependencies (roadmap)
[dependencies]
"""
        (project_dir / "fresh.toml").write_text(manifest_content, encoding="utf-8")

        # 2. Source: src/main.fresh
        main_content = f"""fn main() {{
    println("Hello from {name}!");
}}

main();
"""
        (src_dir / "main.fresh").write_text(main_content, encoding="utf-8")

        # 3. Test: tests/test_basic.fresh
        test_content = """fn test_add() -> int {
    return 2 + 2;
}

println(test_add());
"""
        (tests_dir / "test_basic.fresh").write_text(test_content, encoding="utf-8")

        return project_dir

    @staticmethod
    def build_project(project_dir: Path, output_dir: Path | None = None) -> Path:
        """Build the Fresh project specified by project_dir into C/binary artifacts."""
        manifest = ProjectManifest.load(project_dir)
        entry_file = project_dir / manifest.entry

        if not entry_file.exists():
            # Fallback checks
            for fallback in ("src/main.fresh",):
                if (project_dir / fallback).exists():
                    entry_file = project_dir / fallback
                    break

        if not entry_file.exists():
            raise FileNotFoundError(f"Entry file '{manifest.entry}' not found in project '{project_dir}'.")

        out_dir = output_dir or (project_dir / "build")
        out_dir.mkdir(parents=True, exist_ok=True)

        source = entry_file.read_text(encoding="utf-8")
        ast = ModuleLoader(base_dir=entry_file.parent).load_program_with_imports(
            source, filename=str(entry_file)
        )

        c_code = CTranspiler(filename=str(entry_file)).transpile(ast)
        c_output = out_dir / "main.c"
        c_output.write_text(c_code, encoding="utf-8")

        # Compile with host C compiler if available
        compiler = find_c_compiler()
        if compiler:
            bin_suffix = ".exe" if sys.platform.startswith("win") else ""
            exe_output = out_dir / f"{manifest.name}{bin_suffix}"
            res = subprocess.run(
                [compiler, str(c_output), "-o", str(exe_output)],
                capture_output=True,
                text=True,
            )
            if res.returncode != 0:
                raise RuntimeError(f"C host compilation failed:\n{res.stderr}")
            return exe_output

        return c_output


