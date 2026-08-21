# 🚀 Distributing Fresh Worldwide: Production Release Guide

This guide details the distribution channels, packaging steps, project initialization, and build workflows for the **Fresh Programming Language**.

---

## 📌 1. PyPI Package (`pip install fresh-lang`)

Publishing Fresh to **PyPI** (Python Package Index) allows anyone with Python installed to type `pip install fresh-lang` and immediately run `fresh run program.fresh`, `fresh check`, `fresh fmt`, and `fresh build`.

### Steps to Publish:

1. **Install Packaging Tools**:
   ```bash
   pip install build twine
   ```

2. **Build Source Distribution & Wheel**:
   Run in the root directory (`NEW_LANG`):
   ```bash
   python -m build
   ```
   This generates `.whl` and `.tar.gz` files inside the `dist/` folder.

3. **Upload to PyPI**:
   ```bash
   python -m twine upload dist/*
   ```

Once uploaded, anyone on **Windows, macOS, or Linux** can run:
```bash
pip install fresh-lang
fresh run my_script.fresh
```

---

## 📦 2. Project Packaging & Native Compilation (`fresh init` & `fresh build`)

Fresh includes first-class project management built into the CLI:

### Initialize a New Project:
```bash
fresh init myapp
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
   pyinstaller --onefile --name fresh src/fresh/__main__.py
   ```

3. **Output**:
   The standalone binary will be in `dist/fresh.exe` (Windows) or `dist/fresh` (Linux/macOS).

---

## 🌐 4. Automated CI/CD & Test Verification

Whenever changes are committed, automated workflows can execute the full 12-suite test framework:

```bash
python -m pytest
```

### Release Verification Checklist:
- [x] All 52 unit, integration, differential, GC stress, fuzzing, and package tests passing.
- [x] Formatter idempotence verified (`fresh fmt --check`).
- [x] Native C transpiler differential parity verified against GCC.
- [x] Module import cycle detection verified.
