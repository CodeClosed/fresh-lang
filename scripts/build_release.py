"""Production Release & Packaging Automation Script for Fresh."""

import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def run_step(description: str, cmd: list[str]) -> None:
    print(f"\n===> {description}")
    print(f"$ {' '.join(cmd)}")
    res = subprocess.run(cmd, cwd=ROOT_DIR)
    if res.returncode != 0:
        print(f"Error: Step failed with exit code {res.returncode}", file=sys.stderr)
        sys.exit(res.returncode)


def main() -> None:
    print("========================================")
    print(" Fresh Production Release Build Pipeline")
    print("========================================")

    # 1. Run full test suite
    run_step("1. Running pytest test suite", [sys.executable, "-m", "pytest"])

    # 2. Build Python wheels and source distribution
    run_step("2. Building sdist and wheel packages", [sys.executable, "-m", "build"])

    # 3. Validate packages with twine
    packages = list((ROOT_DIR / "dist").glob("*.whl")) + list((ROOT_DIR / "dist").glob("*.tar.gz"))
    if packages:
        run_step("3. Validating package metadata with twine", [sys.executable, "-m", "twine", "check"] + [str(p) for p in packages])

    # 4. Compile Standalone Zero-Dependency Executable
    pyinstaller_build_dir = ROOT_DIR / "build" / "fresh"
    if pyinstaller_build_dir.exists():
        import shutil
        shutil.rmtree(pyinstaller_build_dir, ignore_errors=True)

    run_step(
        "4. Compiling standalone zero-dependency executable via PyInstaller",
        [sys.executable, "-m", "PyInstaller", "--onefile", "--noconfirm", "--name", "fresh", "src/fresh/__main__.py"],
    )

    # 5. Verify the built standalone binary
    binary_name = "fresh.exe" if sys.platform.startswith("win") else "fresh"
    binary_path = ROOT_DIR / "dist" / binary_name
    if binary_path.exists():
        run_step("5. Verifying standalone binary execution", [str(binary_path), "--help"])
        run_step("6. Running sample Fresh program with standalone binary", [str(binary_path), "run", "examples/01_fibonacci.fresh"])

    print("\n========================================")
    print(" [SUCCESS] Release build completed!")
    print(f" Artifacts available in: {ROOT_DIR / 'dist'}")
    print("========================================")


if __name__ == "__main__":
    main()
