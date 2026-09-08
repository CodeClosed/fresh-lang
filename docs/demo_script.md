# Fresh Language — Presentation Demo Guide

> **Starting point**: A brand new, empty folder. Nothing installed.
> **All commands use**: `python -m fresh` (works everywhere, no PATH issues)
> **Estimated time**: 15–20 minutes

---

## BEFORE YOU START

1. Open a **new empty folder** (e.g. `Desktop\test-lang`)
2. Open that folder in **VS Code**
3. Open the **Terminal** inside VS Code (`` Ctrl + ` ``)
4. Make sure you're in the right folder:

```powershell
pwd
# Should show: C:\Users\vihaa\OneDrive\Desktop\test-lang (or your folder)
```

---

---

## STEP 1 — Install Fresh (1 min)

### Command:

```powershell
pip install fresh-lang
```

Wait for it to finish. Then verify:

```powershell
python -m fresh --help
```

### Expected output:

```
usage: fresh [-h] [--debug] {run,check,fmt,init,build,test,repl} ...

Fresh Programming Language CLI

positional arguments:
  {run,check,fmt,init,build,test,repl}
    run               Execute a Fresh source file
    check             Type-check a Fresh source file
    fmt               Format a Fresh source file
    init              Initialize a new Fresh project
    build             Build a Fresh project
    test              Run automated test suite
    repl              Start interactive Fresh REPL

options:
  -h, --help          show this help message and exit
  --debug             Enable verbose internal traceback reporting
```

### What to say:

*"Fresh is published on PyPI. One `pip install` and you get the full compiler, virtual machine, type checker, code formatter, project manager, and REPL. No extra dependencies needed."*

---

---

## STEP 2 — Create and Run Your First Program (2 min)

### First, create the file:

In VS Code, create a new file called **`demo.fresh`** and paste this:

```fresh
fn greet(name: string) -> string {
    return "Hello, " + name + "!";
}

let message = greet("Professor");
println(message);
println("2 + 2 = " + to_string(2 + 2));
```

**Save the file** (Ctrl+S).

### Command:

```powershell
python -m fresh run demo.fresh
```

### Expected output:

```
Hello, Professor!
2 + 2 = 4
```

### What to say:

*"Clean, readable syntax. Functions have typed parameters and return types. The type system is static with inference — I didn't annotate `message`, but the compiler knows it's a `string`. This just ran on our custom bytecode Virtual Machine. But the VM is only one of two execution paths..."*

---

---

## STEP 2.5 — Show Advanced Syntax & Language Features (3 min) 🌟

> Here you show your professor the rich linguistic features that make Fresh modern and expressive!

Open and run **`showcase.fresh`** (already created in your folder):

### Command:
```powershell
python -m fresh run showcase.fresh
```

### Key Syntax Highlights to Point Out on Screen:

1. **Static Typing with Local Type Inference**:
   ```fresh
   let name = "Fresh";       // Inferred as string
   let version: int = 1;     // Explicit type annotation
   ```
2. **First-Class Closures & Captured Upvalues**:
   ```fresh
   fn make_counter(start: int) -> fn {
       let count = start;
       fn increment() -> int {
           count = count + 1;
           return count;
       }
       return increment;
   }
   ```
   *Explain: Functions can capture variables from enclosing lexical scopes; state persists across calls.*

3. **Lambdas & Higher-Order Functions (`map` & `filter`)**:
   ```fresh
   let square = fn(x: int) -> int { return x * x; };
   let big = filter_ints(squared, fn(x: int) -> bool { return x > 10; });
   ```

4. **Typed Struct Records with Mutable In-Place Fields**:
   ```fresh
   struct Vector3 { x: float, y: float, z: float }
   struct Player { name: string, pos: Vector3, health: int }
   
   let hero = Player { name: "Hero", pos: Vector3 { x: 0.0, y: 10.0, z: -5.0 }, health: 100 };
   hero.pos.x = 25.5; // Nested field mutation
   ```

5. **Dynamic Arrays & 2D Matrices**:
   ```fresh
   push(fruits, "cherry");
   let last = pop(fruits);
   let matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]];
   matrix[1][1] = 99; // 2D indexed mutation
   ```

6. **Pattern Matching (`match`) with Conditional `if` Guards**:
   ```fresh
   match code {
       200 if auth  => "200 OK (Authorized)",
       200 if !auth => "200 OK (Guest)",
       err if err >= 500 && err < 600 => "Server Error (" + to_string(err) + ")",
       _ => "Unknown"
   }
   ```
   *Explain: Much cleaner than verbose cascading if-else chains, matches values and guards simultaneously.*

### What to say:
*"Fresh gives you high-level functional and systems expressiveness: closures with upvalues, higher-order functions, structured records, 2D arrays, and Rust-style pattern matching with guards. All completely type-checked at compile time."*

---

---

## STEP 3 — Project Scaffolding + Native Binary (4 min) ⭐

> This is a **KEY demo**. It shows the dual execution model.

### Step 3a — Create a new project

#### Command:

```powershell
python -m fresh init my_app
```

#### Expected output:

```
Initialized new Fresh project 'my_app' in 'my_app'.
```

You'll see this structure appear in the VS Code sidebar:

```
my_app/
├── fresh.toml          ← project manifest
├── src/
│   └── main.fresh      ← entry point
└── tests/
    └── test_basic.fresh
```

#### What to say:

*"Like `cargo init` in Rust or `npm init` in Node.js — Fresh has built-in project scaffolding with a manifest file."*

---

### Step 3b — Run on the Bytecode VM

#### Command:

```powershell
python -m fresh run my_app/src/main.fresh
```

> ⚠️ **Note the path**: it's `my_app/src/main.fresh`, NOT `my_app/main.fresh`

#### Expected output:

```
Hello from my_app!
```

#### What to say:

*"Execution Path 1: This ran on our custom stack-based bytecode VM with automatic mark-and-sweep garbage collection. Fast iteration, great for development."*

---

### Step 3c — Compile to a Native Binary

#### Command:

```powershell
python -m fresh build my_app
```

#### Expected output:

```
Build succeeded: 'my_app\build\my_app.exe'.
```

You'll see `my_app/build/` appear in the sidebar with `main.c` and `my_app.exe`.

---

### Step 3d — Run the Native Executable

#### Command:

```powershell
.\my_app\build\my_app.exe
```

> ⚠️ **Run the .exe directly** — do NOT put `python -m` in front of it

#### Expected output:

```
Hello from my_app!
```

#### What to say:

*"Execution Path 2: The SAME source code was transpiled into C99, then compiled with GCC into a standalone native executable. That .exe has ZERO dependencies — no Python, no runtime, no VM. It's bare-metal machine code. In our benchmarks, this path runs 91 times faster than CPython for recursive fibonacci. No other educational language offers both a bytecode VM AND a native C backend from the same AST."*

---

---

## STEP 4 — Compiler Pipeline Inspection (4 min) ⭐

> This is the **MOST impressive demo** for a professor. It proves you understand every phase of the compiler.

We'll use `demo.fresh` (the file you created in Step 2).

---

### Step 4a — Token Stream (Lexer Output)

#### Command:

```powershell
python -m fresh run demo.fresh --dump-tokens
```

#### What you'll see:

A list of tokens like `TOKEN_FN`, `TOKEN_IDENTIFIER("greet")`, `TOKEN_LEFT_PAREN`, `TOKEN_STRING("Professor")`, etc. Each with line and column numbers.

#### What to say:

*"Phase 1 — Lexical Analysis. The scanner reads source code character by character and outputs a stream of tokens. Each token records its exact line and column for error reporting."*

---

### Step 4b — Abstract Syntax Tree (Parser Output)

#### Command:

```powershell
python -m fresh run demo.fresh --dump-ast
```

#### What you'll see:

A tree structure showing `FnDecl`, `CallExpr`, `BinaryExpr`, `VarDecl`, etc.

#### What to say:

*"Phase 2 — Parsing. Our Pratt parser converts the token stream into an Abstract Syntax Tree. We use Top-Down Operator Precedence parsing, which handles operator precedence in linear O(N) time — about 80% fewer stack frames than traditional recursive descent."*

---

### Step 4c — Bytecode Disassembly (Compiler Output)

#### Command:

```powershell
python -m fresh run demo.fresh --disassemble
```

#### What you'll see:

Bytecode instructions like `OP_CONSTANT`, `OP_GET_GLOBAL`, `OP_ADD`, `OP_CALL`, `OP_RETURN`, along with a constant pool.

#### What to say:

*"Phases 4-5 — Bytecode Compilation and Optimization. The typed AST is compiled into flat bytecode opcodes. Then a peephole optimizer eliminates redundant instructions. This is what our stack-based VM actually executes."*

---

### Step 4d — C99 Transpilation (Native Backend Output)

#### Command:

```powershell
python -m fresh run demo.fresh --emit-c
```

#### What you'll see:

Clean, readable C code with `#include <stdio.h>`, variable declarations, function definitions, and `printf` calls.

#### What to say:

*"Phase 6B — C Transpilation. Instead of the VM, the exact same AST can generate clean C99 source code. This is what `fresh build` uses under the hood. The C output has verified 1:1 behavioral parity with the VM — every program produces identical results on both backends."*

---

---

## STEP 5 — Static Type Checker (2 min)

### Step 5a — Check a correct file

#### Command:

```powershell
python -m fresh check demo.fresh
```

#### Expected output:

```
Check passed for 'demo.fresh'.
```

#### What to say:

*"The `check` command runs all frontend passes — scanning, parsing, scope resolution, and type checking — WITHOUT executing anything."*

---

### Step 5b — Catch a type error

Create a new file called **`broken.fresh`** with this content:

```fresh
let x: int = 42;
x = "hello";
```

**Save it.** Then run:

#### Command:

```powershell
python -m fresh check broken.fresh
```

#### Expected output:

An error message with **underlined diagnostics** showing you can't assign a `string` to an `int` variable.

#### What to say:

*"In Python, `x = 42; x = 'hello'` runs fine until something breaks at runtime deep in production. In Fresh, the type checker catches this at compile time before ANY code executes. We have Rust-style error diagnostics with exact line numbers, column underlines, and error codes from E1001 through E4001."*

---

---

## STEP 6 — Built-in Code Formatter (1 min)

Create a new file called **`messy.fresh`** with this intentionally ugly code:

```fresh
let     x=10;if(x>5){println("big");}else{println("small");}
```

**Save it.** Then:

#### Command:

```powershell
python -m fresh fmt messy.fresh
```

Now **open `messy.fresh` again** — it will be perfectly formatted with proper indentation.

#### What to say:

*"Like Go's `gofmt` or Rust's `rustfmt`, Fresh has a built-in deterministic code formatter. It's idempotent — running it twice gives the same result. We also have a `--check` flag for CI pipelines that returns exit code 1 if code isn't formatted."*

---

---

## STEP 7 — Interactive REPL (1 min)

#### Command:

```powershell
python -m fresh repl
```

#### Then type these lines one at a time:

```
fresh> 2 + 3 * 4
```
Output: `14`

```
fresh> fn square(x: int) -> int { return x * x; }
```

```
fresh> square(9)
```
Output: `81`

```
fresh> let name = "Professor";
```

```
fresh> "Hello, " + name
```
Output: `Hello, Professor`

```
fresh> exit()
```

#### What to say:

*"The REPL maintains state across lines. Variables and functions you define persist for the entire session. It's like Python's interactive mode, but with static type checking."*

---

---

## STEP 8 — Full Feature Showcase (2 min)

> For this step, you need the `all_features.fresh` file from the project repo.
> Copy it into your demo folder, or navigate to the project folder.

#### Command:

```powershell
python -m fresh run all_features.fresh
```

#### Expected output:

It runs through 8 sections:
1. Primitive types & operators
2. Control flow & loops
3. Functions, closures & higher-order functions (map/filter)
4. Structs with nested field mutation
5. Dynamic arrays & 2D matrices
6. Pattern matching with guards
7. Math library (abs, sqrt, pow, min, max, floor, ceil, round)
8. File I/O (write_file, read_file, file_exists)

Ends with:

```
================================================================
         [SUCCESS] ALL FRESH LANGUAGE FEATURES PASSED!
================================================================
```

#### What to say:

*"This single file exercises every major feature of the language end-to-end. It's our integration test — if this passes, the entire pipeline is working: scanner, Pratt parser, module loader, scope resolver, type checker, bytecode compiler, peephole optimizer, and the VM with garbage collection."*

---

---

## QUICK REFERENCE — Demo Order

| Step | Demo | Time | Command |
|:--|:--|:--|:--|
| 1 | Install from PyPI | 1 min | `pip install fresh-lang` |
| 2 | Create & run demo.fresh | 2 min | `python -m fresh run demo.fresh` |
| **3** | **Init + VM + Native .exe** | **4 min** | **`init` → `run` → `build` → `.exe`** |
| **4** | **Pipeline: tokens/AST/bytecode/C** | **4 min** | **`--dump-tokens` / `--dump-ast` / `--disassemble` / `--emit-c`** |
| 5 | Type checker catches errors | 2 min | `python -m fresh check broken.fresh` |
| 6 | Built-in formatter | 1 min | `python -m fresh fmt messy.fresh` |
| 7 | REPL | 1 min | `python -m fresh repl` |
| 8 | Full feature showcase | 2 min | `python -m fresh run all_features.fresh` |

---

## COMMON PITFALLS TO AVOID

| Mistake | Fix |
|:--|:--|
| `fresh run ...` doesn't work | Use `python -m fresh run ...` instead |
| `python -m fresh run my_app/main.fresh` | Wrong path! It's `my_app/src/main.fresh` |
| `python -m .\my_app\build\my_app.exe` | Don't use `python -m` for the .exe! Just run `.\my_app\build\my_app.exe` directly |
| `python -m fresh run demo.fresh --dump-tokens` file not found | Make sure you created and saved `demo.fresh` first |
| `python -m fresh innit my_app` | It's `init`, not `innit` 😄 |

---

## FILES YOU NEED TO CREATE DURING THE DEMO

Create these **before** the demo or during it:

### 1. `demo.fresh`
```fresh
fn greet(name: string) -> string {
    return "Hello, " + name + "!";
}

let message = greet("Professor");
println(message);
println("2 + 2 = " + to_string(2 + 2));
```

### 2. `broken.fresh`
```fresh
let x: int = 42;
x = "hello";
```

### 3. `messy.fresh`
```fresh
let     x=10;if(x>5){println("big");}else{println("small");}
```

> **Tip**: Create all 3 files before the demo starts so you don't waste time typing during the presentation.
