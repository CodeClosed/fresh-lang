# ⚡ The Fresh Programming Language

<p align="center">
  <img src="https://raw.githubusercontent.com/CodeClosed/fresh-lang/main/vscode-extension/icon.png" width="100" height="100" alt="Fresh Logo" />
</p>

<p align="center">
  <b>A modern, statically-typed compiled language featuring a Pratt parser, optimizing bytecode compiler, stack-based Virtual Machine with mark-and-sweep GC, native C transpilation, closures, pattern matching, and developer tooling.</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue?logo=python" alt="Python Versions" />
  <img src="https://img.shields.io/badge/Tests-93%20Passing-brightgreen?logo=pytest" alt="Test Status" />
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License" />
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey" alt="Platforms" />
</p>

---

## 📑 Table of Contents

- [🚀 Quickstart in 30 Seconds](#-quickstart-in-30-seconds)
- [🌟 Key Highlights & Language Design](#-key-highlights--language-design)
- [🏗 Architecture & Compiler Pipeline](#-architecture--compiler-pipeline)
- [💻 Command-Line Interface (CLI)](#-command-line-interface-cli)
- [🛠 VS Code Integration & 1-Click Execution](#-vs-code-integration--1-click-execution)
- [🧩 Feature Showcase & Code Examples](#-feature-showcase--code-examples)
- [📂 Project Directory Structure](#-project-directory-structure)
- [📚 Documentation Index](#-documentation-index)
- [🧪 Running the Test Suite](#-running-the-test-suite)
- [📄 License](#-license)

---

## 🚀 Quickstart in 30 Seconds

### 1. Installation
Clone the repository and install dependencies:

```bash
git clone https://github.com/CodeClosed/fresh-lang.git
cd fresh-lang
python -m pip install -e .
```

### 2. Write Your First Fresh Program
Create a file named `hello.fresh`:

```fresh
// hello.fresh
fn greet(name: string) -> string {
    return "Hello, " + name + "! Welcome to Fresh ⚡";
}

let message = greet("Developer");
println(message);
```

### 3. Run It!
```bash
fresh run hello.fresh
# Or via python module:
python -m fresh run hello.fresh
```

**Output:**
```text
Hello, Developer! Welcome to Fresh ⚡
```

---

## 🌟 Key Highlights & Language Design

Fresh merges the expressive readability of modern languages with the predictable performance of a bytecode VM and C native code generator:

- **Static Typing with Local Inference**: Strict compile-time type verification with automatic type inference on `let` bindings.
- **Top-Down Operator Precedence (Pratt Parser)**: Clean, robust expression parsing with exact precedence levels and recursion bounds.
- **Visual Rust-Style Diagnostics**: Clear underline markers and error codes (`[E1001]` to `[E4001]`) for syntax and type errors.
- **First-Class Closures & Upvalues**: Functions capture variables across scopes with state persistence.
- **Pattern Matching with Guards**: Powerful `match` expressions supporting values, wildcards (`_`), and conditional `if` guard clauses.
- **User-Defined Records & Structs**: Strongly typed struct records with in-place mutable fields.
- **Dynamic Arrays & Matrices**: Native `[T]` arrays with `push`, `pop`, `len`, and multi-dimensional indexing.
- **Mark-and-Sweep Garbage Collection**: Automatic memory management tracing stacks, upvalues, and globals with `FRESH_GC_STRESS=1` allocation mode.
- **Native C Transpiler**: Compiles Fresh code directly to readable C99 with 1:1 behavioral equivalence for native binary builds (`gcc`, `clang`, `msvc`).
- **Complete Developer Tooling**: Built-in formatter (`fresh fmt`), package manager (`fresh init`/`fresh build`), type checker (`fresh check`), and REPL (`fresh repl`).

---

## 🏗 Architecture & Compiler Pipeline

Fresh uses a unified multi-stage pipeline:

```mermaid
graph TD
    A["Source Code (.fresh)"] --> B["Scanner / Lexer"]
    B -->|"Token Stream"| C["Pratt Parser"]
    C -->|"Abstract Syntax Tree (AST)"| D["Module Loader & Cycle Checker"]
    D -->|"Expanded AST"| E["Resolver & Scope Checker"]
    E -->|"Scoped AST"| F["Type Checker & Inferrer"]
    
    F -->|"Typed AST"| G["Bytecode Compiler"]
    G -->|"Bytecode Chunk"| H["Peephole Optimizer"]
    H -->|"Optimized Bytecode"| I["Virtual Machine (VM + GC)"]
    I -->|"Runtime Output"| J["Program Result"]
    
    F -.->|"Typed AST"| K["C99 Transpiler"]
    K -.->|"Native C Source"| L["C Compiler (GCC / Clang)"]
    L -.->|"Native Binary"| M["Standalone Executable"]
```

---

## 💻 Command-Line Interface (CLI)

The `fresh` CLI provides an all-in-one developer toolkit:

| Command | Usage | Description |
| :--- | :--- | :--- |
| **`fresh run <file>`** | `fresh run main.fresh` | Compiles and executes a Fresh script on the Bytecode VM. |
| **`fresh check <file>`** | `fresh check main.fresh` | Static analysis: checks types and resolves names without running. |
| **`fresh fmt <file>`** | `fresh fmt main.fresh [--check]` | Formats source files idempotently according to standard Fresh style. |
| **`fresh init <name>`** | `fresh init my_app` | Scaffolds a new project with directory structure and `fresh.toml`. |
| **`fresh build [dir]`** | `fresh build .` | Builds the project entrypoint into a standalone native executable. |
| **`fresh test [dir]`** | `fresh test tests/` | Runs the automated pytest test suite. |
| **`fresh repl`** | `fresh repl` | Starts an interactive Read-Eval-Print-Loop session. |

### Compiler Inspection Flags

Inspect intermediate representations at any phase of compilation:

```bash
# Print token stream produced by lexical analysis
fresh run main.fresh --dump-tokens

# Print formatted Abstract Syntax Tree
fresh run main.fresh --dump-ast

# Print disassembled bytecode instructions & constant pool
fresh run main.fresh --disassemble

# Transpile Fresh AST directly into standalone C99 source code
fresh run main.fresh --emit-c
```

---

## 🛠 VS Code Integration & 1-Click Execution

The workspace includes ready-to-use VS Code configurations:

1. **Press `F5`**: Runs the currently active `.fresh` file in the integrated terminal.
2. **Press `Ctrl + Shift + B`**: Executes the default build task (`Fresh: Run Active File`).
3. **Command Palette (`Ctrl + Shift + P` -> `Tasks: Run Task`)**:
   - `Fresh: Run Active File`
   - `Fresh: Type Check Active File`
   - `Fresh: Format Active File`
   - `Fresh: Run Test Suite`
4. **Syntax Highlighting & File Icons**: Included in [`vscode-extension/`](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/vscode-extension/).

---

## 🧩 Feature Showcase & Code Examples

Explore ready-to-run examples in the [`examples/`](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/examples/) directory:

| Example File | Key Concept Demonstrated |
| :--- | :--- |
| [`all_features.fresh`](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/all_features.fresh) | **Complete Tour**: Primitives, closures, matrices, structs, pattern matching, stdlib, file I/O |
| [`01_fibonacci.fresh`](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/examples/01_fibonacci.fresh) | Recursive function calls, conditional returns, arithmetic |
| [`02_matrix_multiply.fresh`](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/examples/02_matrix_multiply.fresh) | 2D dynamic arrays, nested loops, matrix multiplication |
| [`03_quicksort.fresh`](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/examples/03_quicksort.fresh) | In-place array mutation, indexing, partition algorithm |
| [`04_closure_counter.fresh`](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/examples/04_closure_counter.fresh) | Lexical closures, upvalue mutation across multiple function calls |
| [`05_calculator.fresh`](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/examples/05_calculator.fresh) | First-class functions, higher-order function dispatch |
| [`06_inventory.fresh`](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/examples/06_inventory.fresh) | User-defined structs, field mutations, inventory calculations |
| [`07_stress_suite.fresh`](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/examples/07_stress_suite.fresh) | End-to-end stress test across all core language features |
| [`08_aggressive_suite.fresh`](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/examples/08_aggressive_suite.fresh) | Deep recursion (Ackermann), map/filter higher-order lambdas, pattern guards |

---

## 📂 Project Directory Structure

```text
NEW_LANG/
├── all_features.fresh         # Complete feature showcase script
├── LANGUAGE_GUIDE.md          # Comprehensive language tutorial and handbook
├── README.md                  # Main project documentation (this file)
├── pyproject.toml             # Python build metadata & tool configuration
├── docs/                      # In-depth architectural documentation
│   ├── FRESH_SPECIFICATION.md # Formal EBNF grammar & normative specification
│   ├── project_guide.md       # Architecture & contributor implementation guide
│   ├── COMPARISON.md          # Academic comparison vs Rust, Go, Python, Lua, C
│   ├── PROS.md                # Language design rationale and benefits
│   ├── COMPATIBILITY_AND_VERSIONING.md # Versioning & SemVer policy
│   └── production_release_guide.md     # Packaging and release workflow
├── examples/                  # Official runnable example programs
├── src/fresh/                 # Fresh compiler & runtime core package
│   ├── analyzer/              # Semantic analysis (Resolver, Type Checker)
│   ├── codegen/               # Bytecode compiler, optimizer, and C transpiler
│   ├── common/                # Shared AST tokens, type definitions, error types
│   ├── lexer/                 # Scanner and token definitions
│   ├── parser/                # Pratt expression parser and statement AST
│   ├── stdlib/                # Built-in functions and math library
│   ├── vm/                    # Virtual machine, CallFrame, and Mark-and-Sweep GC
│   ├── cli.py                 # Command-line interface driver
│   ├── formatter.py           # Canonical source code formatter
│   ├── modules.py             # Multi-file module loader and cycle detector
│   ├── package.py             # Package manager (init & build)
│   └── pipeline.py            # Unified end-to-end execution pipeline
├── tests/                     # 93 automated tests across all subsystems
└── vscode-extension/          # Official VS Code syntax highlighter & icons
```

---

## 📚 Documentation Index

For in-depth guides, check the dedicated documents:

- 📘 [**Language Guide (`LANGUAGE_GUIDE.md`)**](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/LANGUAGE_GUIDE.md): Complete language tutorial from variables to closures and pattern matching.
- 📐 [**Formal Specification (`docs/FRESH_SPECIFICATION.md`)**](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/docs/FRESH_SPECIFICATION.md): EBNF grammar, typing rules, and operational semantics.
- 🏛 [**Architecture & Contributor Guide (`docs/project_guide.md`)**](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/docs/project_guide.md): Deep-dive into compiler internals, AST structures, and VM bytecode engine.
- ⚖️ [**Comparative Analysis (`docs/COMPARISON.md`)**](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/docs/COMPARISON.md): Architectural comparison against Rust, Go, Python, Lua, and C.
- 💡 [**Project Advantages & Design Rationale (`docs/PROS.md`)**](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/docs/PROS.md): Why Fresh was built and key architectural strengths.
- 🚀 [**Production & Release Guide (`docs/production_release_guide.md`)**](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/docs/production_release_guide.md): Wheel packaging, release checklist, and distribution.

---

## 🧪 Running the Test Suite

Run the full automated test suite containing unit, integration, differential, safety, and GC stress tests:

```bash
# Run all tests
pytest -v

# Run with test coverage report
pytest --cov=fresh --cov-report=term-missing
```

---

## 📄 License

Fresh is open-source software distributed under the terms of the **[MIT License](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/LICENSE)**.
