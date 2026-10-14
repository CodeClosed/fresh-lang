# 📦 Production Packaging, Distribution & CI/CD Guide

This guide details how Fresh is packaged, validated, distributed across global channels (PyPI and standalone binaries), and continuously integrated via GitHub Actions.

---

## 1. PyPI Distribution (`pip install fresh-lang`)

Fresh is published as an official package on **PyPI**: [https://pypi.org/project/fresh-lang/](https://pypi.org/project/fresh-lang/).

### User Installation:
Any developer on Windows, macOS, or Linux with Python 3.11+ can install Fresh globally with one command:
```bash
pip install fresh-lang
```

### Publishing New Releases to PyPI:
1. **Ensure Build Tools are Installed**:
   ```bash
   pip install build twine
   ```
2. **Build Source Distribution and Wheel**:
   ```bash
   python -m build
   ```
   This generates `.tar.gz` (sdist) and `.whl` (wheel) archives inside the `dist/` directory.
3. **Validate Package Metadata**:
   ```bash
   python -m twine check dist/*.whl dist/*.tar.gz
   ```
4. **Upload to PyPI**:
   ```bash
   python -m twine upload dist/fresh_lang-<version>*
   ```

---

## 2. Standalone Zero-Dependency Binaries (`fresh.exe` / `fresh`)

For environments where Python is not installed, Fresh can be compiled into a standalone, single-file binary using PyInstaller.

### Automated Release Script (`scripts/build_release.py`):
Fresh includes a release automation script that runs tests, builds wheels, compiles standalone binaries, and verifies them end-to-end:

```bash
python scripts/build_release.py
```

### Manual Compilation:
```bash
pyinstaller --onefile --clean --name fresh src/fresh/__main__.py
```
The resulting executable is placed in `dist/fresh.exe` (Windows) or `dist/fresh` (Linux/macOS) and requires zero host dependencies.

---

## 3. Continuous Integration & CD Pipeline (`.github/workflows/ci.yml`)

Every push and pull request to `main` triggers an automated GitHub Actions matrix pipeline:

### Workflow Matrix:
- **Operating Systems**: `ubuntu-latest`, `windows-latest`, `macos-latest`
- **Python Versions**: `3.11`, `3.12`, `3.13`
- **Steps Executed**:
  1. **Test Suite**: Runs `pytest` with coverage across all matrix configurations.
  2. **CLI Verification**: Runs `fresh run examples/01_fibonacci.fresh`, `fresh check`, and `fresh fmt --check`.
  3. **Package Validation**: Builds wheels and checks with `twine check`.
  4. **Binary Compilation**: Uses PyInstaller on all three OS targets to generate `fresh-linux`, `fresh-windows.exe`, and `fresh-macos` build artifacts.

---

## 4. Release Checklist

Before tagging and releasing a new version:

- [ ] Ensure all 97+ automated unit and integration tests pass: `python -m pytest`
- [ ] Run static type verification: `python -m mypy src`
- [ ] Run code quality linter: `python -m ruff check .`
- [ ] Verify examples run cleanly: `python -m fresh run examples/01_fibonacci.fresh`
- [ ] Increment version in `pyproject.toml` and `vscode-extension/package.json`
- [ ] Run automated build script: `python scripts/build_release.py`
- [ ] Push git tag: `git tag vX.Y.Z && git push origin vX.Y.Z`
