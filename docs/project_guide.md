# Building a Custom Programming Language: Compiler Design Guide & Roadmap

A comprehensive, production-grade guide designed for academic compiler design projects, semester capstones, and systems programming portfolios.

---

## 1. Project Scoping & Core Recommendations

When designing a programming language for a compiler design course or capstone project, the biggest trap is **scope creep**. A complete, robust compiler for a small, expressive language is infinitely better than an incomplete, buggy attempt at a massive language.

### Golden Rules for Compiler Projects
1. **Prioritize Soundness Over Breadth:** A language with integers, booleans, functions, lexical scoping, and arrays that compiles and runs correctly will score much higher than an object-oriented language with broken semantics.
2. **Decouple Front-End and Back-End:** Design clean, decoupled data structures between compilation phases (Lexer $\rightarrow$ Parser $\rightarrow$ AST $\rightarrow$ Module Resolver $\rightarrow$ Semantic Analyzer $\rightarrow$ Bytecode VM / C Transpiler).
3. **Write Tests Early:** Build an automated end-to-end regression test suite from Day 1. Every parser feature should come with positive and negative diagnostic test cases.
4. **Choose the Right Target:**
   - **Recommended Sweet Spot (High Marks, Production Grade):** Dual-Backend: Stack-based Bytecode Virtual Machine (with Mark-and-Sweep Garbage Collection) + C Transpiler for native binary generation.

---

## 2. Recommended Language Features (Feature Matrix)

Here is a recommended feature set categorized into **Tier 1 (Core MVP)**, **Tier 2 (Competitive / Advanced)**, and **Tier 3 (Stretch Goals)**.

### Feature Tier Breakdown

| Category | Tier 1: Minimum Viable Language (MVP) | Tier 2: Recommended Target (Capstone Standard) | Tier 3: Stretch Goals (Distinction Level) | Fresh Implementation Status |
| :--- | :--- | :--- | :--- | :---: |
| **Data Types** | `int`, `bool`, `string` | Arrays / Slices, Floating point (`float`) | User-defined Structs / Records | ✅ Full Tier 3 |
| **Type System** | Static Typing (basic checking) or Dynamic Typing | Static type inference (Local `let`/`auto`) | Strong Static Typing with local inference | ✅ Full Tier 3 |
| **Control Flow** | `if` / `else`, `while` loops | `for` loops, `break`, `continue`, early `return` | `match` / Pattern Matching with Guards | ✅ Full Tier 3 |
| **Functions** | First-class named functions, Call by Value | Recursion, Lexical Scoping, Closures | Higher-order functions, Lambdas, Upvalues | ✅ Full Tier 3 |
| **Memory Model** | Host runtime memory / Stack allocation | Dynamic array allocation | Mark-and-Sweep GC with Stress Mode | ✅ Full Tier 3 |
| **Modules** | Single file scripts | Multi-file concatenation | Recursive `import` + Circular Dependency Detection | ✅ Full Tier 3 |
| **Tooling** | Basic CLI runner | Inspection flags (`--dump-ast`, `--disassemble`) | `fresh check`, `fresh fmt`, `fresh init`, `fresh build`, `fresh test` | ✅ Full Tier 3 |

---

## 3. End-to-End Implementation Roadmap

A step-by-step 8-phase execution plan for building a complete compiler:

```
[Source Code (.fresh)]
        │
        ▼
[Phase 1: Lexical Analysis (Scanner)] ───► Token Stream (Exact Line & Column)
        │
        ▼
[Phase 2: Syntax Analysis (Pratt Parser)] ──► Abstract Syntax Tree (AST)
        │
        ▼
[Phase 3: Module Resolution]          ───► Dependency Graph & Cycle Detection
        │
        ▼
[Phase 4: Semantic Analysis]          ───► Scope Resolution & Static Type Checking
        │
        ▼
[Phase 5: Optimization Passes]        ───► Optimized AST & Constant Folding
        │
        ▼
┌───────┴────────────────────────────────┐
▼                                        ▼
[Phase 6A: Bytecode Compiler]            [Phase 6B: C Transpiler]
        │                                        │
        ▼                                        ▼
[Stack VM & Mark-and-Sweep GC]           [Standalone C & Native GCC Binary]
```

---

## 4. Testing, Evaluation & Presentation Strategy

To guarantee maximum score and demonstration appeal during your project evaluation:

1. **Self-Contained Demo Programs:**
   - `01_fibonacci.fresh` (Demonstrates recursion, timing, and integer arithmetic).
   - `02_matrix_multiply.fresh` (Demonstrates nested loops, 2D arrays, and performance).
   - `03_quicksort.fresh` (Demonstrates mutation, arrays, and recursive logic).
   - `04_closure_counter.fresh` (Demonstrates closures and lexical upvalue state).

2. **Visual AST & Bytecode Dumps:**
   - Add CLI flags `--dump-tokens`, `--dump-ast`, and `--disassemble` / `--emit-c`.
   - Demonstrating the compiler's intermediate representations during a demo leaves a strong impression on evaluators.

3. **Benchmarking & Differential Verification:**
   - Run differential VM vs Native GCC execution tests to prove 100% behavioral parity.
   - Run GC stress tests (`FRESH_GC_STRESS=1`) to prove memory reclamation soundness.
