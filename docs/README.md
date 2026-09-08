# ⚡ Fresh Language Documentation Hub

Welcome to the official documentation for the **Fresh Programming Language** (v0.1.0) — a modern, statically-typed compiled language with a Pratt parser, optimizing bytecode compiler, stack-based VM with mark-and-sweep garbage collection, C transpiler, closures, and pattern matching.

---

## 📑 Documentation Index

| Document | Purpose | Target Audience |
|:---|:---|:---|
| 📐 [**Formal Specification**](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/docs/specification.md) | Normative grammar (EBNF), lexical tokens, type system rules, and operational semantics. | Language implementers, compiler engineers |
| 🏛 [**Compiler & VM Architecture**](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/docs/architecture.md) | End-to-end walkthrough of the 8-phase pipeline from scanner to VM and C backend. | Contributors, systems programmers |
| 🔬 [**Comparative Analysis**](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/docs/comparison.md) | Academic architectural comparison against Python, C, Rust, and Lox with benchmark metrics. | Evaluators, researchers, academics |
| 📚 [**Standard Library Reference**](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/docs/standard_library.md) | Complete API reference for core built-ins, I/O, collections, and the math library. | Application developers, learners |
| 💻 [**CLI & Developer Tooling**](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/docs/cli_and_tooling.md) | CLI subcommands (`run`, `check`, `fmt`, `build`, etc.), `fresh.toml`, and VS Code extension. | Developers, toolchain users |
| 📦 [**Release & Packaging Guide**](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/docs/release_and_packaging.md) | PyPI distribution, standalone executable compilation, and GitHub Actions CI/CD. | Package maintainers, DevOps |
| 🛡 [**Compatibility & Diagnostics**](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/docs/compatibility.md) | SemVer 2.0 stability guarantees, deprecation lifecycle, and error code catalog (`[E1001]`–`[E5001]`). | Production teams, integrators |
| 🎤 [**Presentation & Demo Guide**](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/docs/presentation_guide.md) | 15-minute live demonstration script with exact commands, code snippets, and talking points. | Presenters, speakers, instructors |

---

## 🗺️ Reading Paths by Role

### 1. Learning to Write Fresh Code
1. Start with the root [**LANGUAGE_GUIDE.md**](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/LANGUAGE_GUIDE.md) for syntax, control flow, functions, structs, and pattern matching.
2. Check the [**Standard Library Reference**](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/docs/standard_library.md) for available built-in functions.
3. Review [**CLI & Developer Tooling**](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/docs/cli_and_tooling.md) to learn project management (`fresh init`, `fresh build`, `fresh test`).

### 2. Contributing to the Compiler or VM
1. Read the [**Formal Specification**](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/docs/specification.md) to understand normative behavior.
2. Study the [**Compiler & VM Architecture**](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/docs/architecture.md) for the dataflow and AST structure.
3. Check [**Compatibility & Diagnostics**](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/docs/compatibility.md) for error diagnostic conventions.

### 3. Evaluating Language Design & Performance
1. Read the [**Comparative Analysis**](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/docs/comparison.md) for architectural trade-offs and quantitative benchmarks.
2. Explore the [**Architecture Guide**](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/docs/architecture.md) for memory management and dual-backend execution.

### 4. Deploying or Packaging Fresh
1. Read the [**Release & Packaging Guide**](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/docs/release_and_packaging.md) for wheel generation and standalone binary compilation.
