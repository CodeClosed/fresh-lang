# 🏛 Fresh Compiler & VM Internal Architecture

This document provides a deep architectural walkthrough of the Fresh compiler, runtime, and dual-backend execution pipeline.

---

## 1. End-to-End Pipeline Overview

Fresh transforms human-readable source code through eight decoupled phases into either bytecode instructions executed by a custom Virtual Machine, or clean C99 code compiled to a native machine executable.

```
                  ┌──────────────────────┐
                  │ Source Code (.fresh) │
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Phase 1: Lexer       │ ──► Tokens (Line & Column)
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Phase 2: Pratt Parser│ ──► Abstract Syntax Tree (AST)
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Phase 3: Modules     │ ──► Dependency Graph & Cycle Check [E4001]
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Phase 4: Resolver    │ ──► Lexical Scopes & Upvalue Analysis
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Phase 5: TypeChecker │ ──► Static Type Validation [E3001]
                  └──────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Phase 6: Optimizer   │ ──► Constant Folding & Dead Code Elimination
                  └──────────┬───────────┘
                             │
               ┌─────────────┴─────────────┐
               ▼                           ▼
    ┌──────────────────────┐    ┌──────────────────────┐
    │ Phase 7: Compiler    │    │ Phase 8B: C Backend  │
    └──────────┬───────────┘    └──────────┬───────────┘
               │                           │
               ▼                           ▼
    ┌──────────────────────┐    ┌──────────────────────┐
    │ Phase 8A: Stack VM   │    │ Native C Executable  │
    │  & Mark-Sweep GC     │    │  (via GCC / Clang)   │
    └──────────────────────┘    └──────────────────────┘
```

---

## 2. Phase-by-Phase Architecture

### Phase 1: Lexical Analysis (`fresh.lexer.scanner`)
- **Responsibility**: Scans raw UTF-8 text into a linear stream of strongly-typed `Token` objects.
- **Key Features**:
  - Exact 1-indexed line and column tracking for every token.
  - Nested block comments (`/* ... /* ... */ ... */`).
  - Escape character parsing in strings (`\n`, `\t`, `\"`, `\\`, `\0`).
  - Strict numeric validation (distinguishing integers from IEEE 754 floats).

### Phase 2: Syntax Analysis (`fresh.parser.parser`)
- **Responsibility**: Converts the token stream into an Abstract Syntax Tree (AST).
- **Technique**: Top-Down Operator Precedence (**Pratt Parser**).
- **Advantages**:
  - Handles operator precedence and associativity without deep recursive call chains.
  - Clean separation between prefix operators (`!`, `-`), infix binary operators (`+`, `*`, `==`), and postfix operators (function calls `()`, field access `.`, array indexing `[]`).
  - Robust error recovery: synchronizes on statement boundaries (`;`, `}`) after syntax errors.

### Phase 3: Module Resolution (`fresh.modules`)
- **Responsibility**: Manages multi-file projects and resolves `import` statements.
- **Algorithm**:
  - Constructs a directed graph of file dependencies.
  - Performs depth-first search (DFS) topological sort.
  - Statically detects circular dependencies (e.g. `a.fresh -> b.fresh -> a.fresh`) and emits diagnostic `[E4001]`.
  - Caches parsed ASTs so shared modules are only analyzed once.

### Phase 4: Scope Resolution (`fresh.analyzer.resolver`)
- **Responsibility**: Resolves variable identifiers to specific lexical scopes before runtime.
- **Scope Tracking**:
  - Tracks variable declarations and initializations across block scopes.
  - Detects duplicate declarations in the same scope.
  - Identifies closure captures: variables declared in an outer function and accessed in an inner function are marked as captured **upvalues**.

### Phase 5: Semantic Analysis (`fresh.analyzer.type_checker`)
- **Responsibility**: Validates type safety across all AST expressions and statements.
- **Rules Enforced**:
  - Local type inference on `let` bindings without explicit annotations.
  - Function parameter and return type validation.
  - Struct field existence and type conformity on construction and property access.
  - Pattern match exhaustiveness and type compatibility across `match` arms and guards.
  - Emits formatted diagnostics with source code underlines on mismatches (`[E3001]`).

### Phase 6: AST Optimization (`fresh.codegen.optimizer`)
- **Responsibility**: Simplifies and transforms the AST prior to code generation.
- **Optimizations**:
  - **Constant Folding**: Precomputes compile-time arithmetic and boolean logic (e.g., `3 + 4 * 2` folds directly into `11`).
  - **Dead Code Elimination**: Removes unreachable branches (e.g., `if (false) { ... }`).
  - **Algebraic Identity Simplification**: Simplifies expressions such as `x + 0`, `x * 1`, `x * 0`.

### Phase 7: Bytecode Compilation (`fresh.codegen.compiler`)
- **Responsibility**: Translates the optimized AST into flat bytecode chunks for the VM.
- **Key Concepts**:
  - **Chunk**: Holds an array of byte instructions, a constant pool (`Value` objects), and debug line numbers.
  - **Jump Patching**: Emits placeholder backpatch offsets for conditional jumps (`OP_JUMP_IF_FALSE`, `OP_JUMP`) resolved once branch targets are compiled.
  - **Upvalue Descriptors**: Emits instructions indicating whether an upvalue captures a local stack slot or an enclosing upvalue.

### Phase 8A: Virtual Machine Execution & Garbage Collection (`fresh.vm`)
- **Architecture**: Stack-based execution engine.
- **Stack & CallFrames**:
  - Fixed-size operand stack for fast push/pop operations.
  - `CallFrame` structures hold the instruction pointer (`ip`), the running closure, and a pointer to the frame's base stack slot.
- **Garbage Collector (`fresh.vm.gc`)**:
  - Precise **Mark-and-Sweep** algorithm.
  - **Roots**: Current VM operand stack, all active call frames, globals dictionary, and open upvalues.
  - **Stress Mode**: Run with `--gc-stress` to force collection on every single allocation, ensuring zero memory leaks and verifying GC root completeness.

### Phase 8B: Native C Transpilation (`fresh.codegen.c_transpiler`)
- **Responsibility**: Transpiles Fresh ASTs into standalone C99 code (`--emit-c` / `fresh build`).
- **Features**:
  - Emits self-contained C files requiring no external libraries beyond the standard C runtime (`libc`).
  - Generates typed C structs, functions, loops, and math runtime helpers.
  - Compiles with GCC, Clang, or MSVC into bare-metal executables delivering up to **91x speedups** over interpreted execution.

---

## 3. Codebase Directory Layout

```
NEW_LANG/
├── src/fresh/
│   ├── analyzer/              # Semantic analysis & type checking
│   │   ├── resolver.py        # Lexical scope & upvalue resolution
│   │   └── type_checker.py    # Static type verification
│   ├── codegen/               # Bytecode and C code generators
│   │   ├── c_transpiler.py    # AST -> C99 transpiler
│   │   ├── compiler.py        # AST -> Bytecode compiler
│   │   ├── opcodes.py         # Bytecode instruction set definitions
│   │   └── optimizer.py       # Constant folding & AST optimizations
│   ├── common/                # Shared utilities & error types
│   │   ├── ast.py             # AST node dataclass definitions
│   │   ├── errors.py          # Fresh diagnostic error hierarchy
│   │   └── tokens.py          # Token types & Token dataclass
│   ├── lexer/                 # Lexical analysis
│   │   └── scanner.py         # Token scanner with line/col tracking
│   ├── parser/                # Syntactic analysis
│   │   └── parser.py          # Pratt parsing engine
│   ├── stdlib/                # Standard library implementations
│   │   ├── builtins.py        # Core built-ins (len, push, pop, clock, etc.)
│   │   └── math_lib.py        # Math functions (abs, sqrt, min, max, etc.)
│   ├── vm/                    # Runtime execution engine
│   │   ├── gc.py              # Mark-and-sweep garbage collector
│   │   ├── objects.py         # Heap objects (strings, structs, closures)
│   │   └── vm.py              # Stack-based virtual machine
│   ├── cli.py                 # Command-line interface driver
│   ├── formatter.py           # AST-based source code formatter
│   ├── modules.py             # Module loader & dependency graph
│   ├── package.py             # Project management (fresh init/build)
│   └── pipeline.py            # Phase orchestration facade
├── tests/                     # Automated test suites
├── docs/                      # Technical documentation suite
├── examples/                  # Reference Fresh source programs
└── pyproject.toml             # Project metadata & tool configuration
```
