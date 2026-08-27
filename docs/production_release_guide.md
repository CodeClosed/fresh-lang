# 🚀 Distributing Fresh Worldwide: Production Release Guide

This guide details the distribution channels, packaging steps, project initialization, and build workflows for the **Fresh Programming Language**.

---

## 📌 1. PyPI Package (`pip install fresh-lang`)

Fresh is published on **PyPI**: [https://pypi.org/project/fresh-lang/](https://pypi.org/project/fresh-lang/).

Anyone on **Windows, macOS, or Linux** with Python 3.11+ installed can install and use Fresh globally:
```bash
pip install fresh-lang
```

### Steps to Release New Versions to PyPI:

1. **Install Packaging Tools**:
   ```bash
   pip install build twine
   ```

2. **Build Source Distribution & Wheel**:
   ```bash
   python -m build
   ```
   This generates `.whl` and `.tar.gz` files inside the `dist/` folder.

3. **Validate Package Metadata**:
   ```bash
   python -m twine check dist/*.whl dist/*.tar.gz
   ```

4. **Upload to PyPI**:
   ```bash
   python -m twine upload dist/fresh_lang-<version>*
   ```

---

## 📦 2. Project Packaging & Native Compilation (`fresh init` & `fresh build`)

Fresh includes first-class project management built into the CLI:

### Initialize a New Project:
```bash
fresh init myapp
# or: python -m fresh init myapp
```
Generates standard project structure:
```text
myapp/
├── fresh.toml          # Project configuration manifest
├── src/
│   └── main.fresh      # Entry point
└── tests/
    └── test_basic.fresh
```

### Build Native Binary:
```bash
fresh build myapp
# or: python -m fresh build myapp
```
Compiles `src/main.fresh` and all imported dependencies into optimized standalone C code (`build/main.c`) and native machine code binary (`build/myapp.exe` via GCC/Clang).

---

## 📦 3. Standalone Binary CLI Executable (Zero Dependencies)

To allow users to run the Fresh compiler without needing Python installed on their machine, you can package the Fresh CLI into standalone zero-dependency native executables (`fresh.exe` for Windows, `fresh` for Linux/macOS).

### Build Standalone Executable with PyInstaller:

1. **Install PyInstaller**:
   ```bash
   pip install pyinstaller
   ```

2. **Compile Single-File Executable**:
   ```bash
   python -m PyInstaller --onefile --noconfirm --name fresh src/fresh/__main__.py
   ```

3. **Output**:
   The standalone binary will be in `dist/fresh.exe` (Windows) or `dist/fresh` (Linux/macOS).

---

## 🌐 4. Automated 1-Click Release Pipeline & CI/CD

### All-in-One Automated Release Script:
To run tests, build wheels, validate with twine, and compile standalone binaries with a single command:
```bash
python scripts/build_release.py
```

### GitHub Actions CI/CD:
Configured in `.github/workflows/ci.yml` to automatically:
- Test on Ubuntu, Windows, and macOS across Python 3.11–3.13.
- Build and validate wheel/sdist packages.
- Compile native standalone binaries for all operating systems.

### Release Verification Checklist:
- [x] All 90 unit, integration, differential, GC stress, fuzzing, and package tests passing.
- [x] Formatter idempotence verified (`fresh fmt --check`).
- [x] Native C transpiler differential parity verified against GCC.
- [x] Module import cycle detection verified.
- [x] Wheel and tarball validated with `twine check`.
- [x] Live PyPI package published (`fresh-lang`).
