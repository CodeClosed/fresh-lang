# 🎬 Fresh Language Complete Live Demonstration Script
## Step-by-Step Presentation Guide: Install ➔ Build ➔ Run ➔ Dual Modes ➔ Tokens ➔ C Code

Use this exact script and sequence of commands to demonstrate the Fresh Programming Language to professors, evaluators, or audiences.

---

## 📋 Quick Demonstration Cheat Sheet

| Step | What You Demonstrate | Terminal Command |
|:---:|:---|:---|
| **1** | **Package Installation** | `pip install fresh-lang` *(or `pip install -e .`)* |
| **2** | **CLI Verification** | `python -m fresh --help` |
| **3** | **Project Scaffolding** | `python -m fresh init my_app` |
| **4** | **Native C Build** | `python -m fresh build my_app` |
| **5** | **Run Native Binary** | `.\my_app\build\my_app.exe` *(Windows)* or `./my_app/build/my_app` *(Linux/macOS)* |
| **6** | **Run on Bytecode VM** | `python -m fresh run demo/quick_demo.fresh` |
| **7** | **Two Types / Dual-Execution** | Explain **VM Mode** (instant execution) vs **Native C Mode** (92x speedup) |
| **8** | **Inspect Lexer Tokens** | `python -m fresh run demo/quick_demo.fresh --dump-tokens` |
| **9** | **Inspect Abstract Syntax Tree** | `python -m fresh run demo/quick_demo.fresh --dump-ast` |
| **10** | **Inspect VM Bytecode** | `python -m fresh run demo/quick_demo.fresh --disassemble` |
| **11** | **Transpile to C99 Code** | `python -m fresh run demo/quick_demo.fresh --emit-c` |
| **12** | **Static Type Checker** | `python -m fresh check demo/quick_demo.fresh` |

---

## 📝 The Demonstration Source File (`demo/quick_demo.fresh`)

```fresh
// quick_demo.fresh - Quick Demonstration Script for Fresh Language

fn fibonacci(n: int) -> int {
    if (n <= 1) {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}

fn compute_stats(name: string, count: int) {
    println("Processing:", name);
    let result = fibonacci(count);
    println("Fibonacci(", count, ") =", result);
}

let user = "Professor";
let terms = 10;

compute_stats(user, terms);
```

---

## 🎯 Step-by-Step Live Presentation Guide

### Step 1: Install the Package
> **What to say**: *"Fresh is packaged and distributed globally on PyPI. Anyone on Windows, macOS, or Linux can install it with a single command."*

```bash
# Global installation from PyPI:
pip install fresh-lang

# Or local editable installation from repository:
pip install -e .
```

Verify the CLI is ready:
```bash
python -m fresh --help
```
*Expected Output: Shows the unified subcommands: `run`, `check`, `fmt`, `init`, `build`, `test`, `repl`.*

---

### Step 2: Initialize & Build a Native Project (`init` ➔ `build`)
> **What to say**: *"Fresh is not just a scripting toy. It includes a complete package manager and build system. With `fresh init`, it creates a project manifest, source tree, and tests. With `fresh build`, it compiles the project to a bare-metal machine executable."*

```bash
# 1. Initialize project
python -m fresh init demo_app

# 2. Compile to native binary (transpiles to C and compiles with GCC/Clang/MSVC)
python -m fresh build demo_app

# 3. Execute the standalone native executable!
.\demo_app\build\demo_app.exe
```
*Expected Output:*
```text
Initialized new Fresh project 'demo_app' in 'demo_app'.
Build succeeded: 'demo_app\build\demo_app.exe'.
Hello from demo_app!
```

---

### Step 3: Run on the Bytecode VM
> **What to say**: *"Here is our sample program, `demo/quick_demo.fresh`. We can run it instantly using the Fresh Bytecode Virtual Machine."*

```bash
python -m fresh run demo/quick_demo.fresh
```
*Expected Output:*
```text
Processing: Professor
Fibonacci( 10 ) = 55
```

---

### Step 4: Explain the Two Execution Modes (Dual-Backend)
> **What to say**: *"Fresh features a unique **dual-execution architecture**. From the exact same source code, you get two distinct execution paths:"*

1. **Mode 1: Bytecode Virtual Machine (Interpreter)**
   - Stack-based VM with automatic **Mark-and-Sweep Garbage Collection**.
   - Zero compile time — executes immediately for rapid scripting, development, and REPL prototyping.
2. **Mode 2: Native C Compilation Backend**
   - Transpiles the AST into clean, ANSI C99 code.
   - Compiles via GCC/Clang into standalone native machine code, running up to **92x faster** for heavy computational tasks.

---

### Step 5: Inspect Scanned Tokens (`--dump-tokens`)
> **What to say**: *"Phase 1 of our compiler is the Lexer/Scanner. It breaks raw UTF-8 text into a linear stream of strongly typed tokens, keeping track of exact 1-indexed lines and columns."*

```bash
python -m fresh run demo/quick_demo.fresh --dump-tokens
```
*Expected Output snippet:*
```text
=== TOKENS (demo\quick_demo.fresh) ===
  Token(FN, 'fn')
  Token(IDENTIFIER, 'fibonacci')
  Token(LEFT_PAREN, '(')
  Token(IDENTIFIER, 'n')
  Token(COLON, ':')
  Token(INT_TYPE, 'int')
  ...
  Token(INT_LIT, '10', value=10)
  Token(EOF, '')
```

---

### Step 6: Inspect the Abstract Syntax Tree (`--dump-ast`)
> **What to say**: *"Phase 2 uses a Pratt Parser (Top-Down Operator Precedence). Unlike recursive descent arithmetic parsers that can overflow the call stack, the Pratt parser builds the Abstract Syntax Tree efficiently in linear time."*

```bash
python -m fresh run demo/quick_demo.fresh --dump-ast
```
*Expected Output:*
```text
=== AST (demo\quick_demo.fresh) ===
FnDecl fibonacci(n: int) -> int
  If ((n <= 1))
    Return n
  Return (fibonacci((n - 1)) + fibonacci((n - 2)))
FnDecl compute_stats(name: string, count: int)
  ExprStmt println('Processing:', name)
  VarDecl result = fibonacci(count)
  ExprStmt println('Fibonacci(', count, ') =', result)
VarDecl user = 'Professor'
VarDecl terms = 10
ExprStmt compute_stats(user, terms)
```

---

### Step 7: Inspect Disassembled Bytecode Instructions (`--disassemble`)
> **What to say**: *"Phase 7 translates the optimized AST into flat bytecode chunks with an explicit constant pool. Here is the disassembled VM instruction stream:"*

```bash
python -m fresh run demo/quick_demo.fresh --disassemble
```
*Expected Output:*
```text
=== DISASSEMBLY (demo\quick_demo.fresh) ===
=== main ===
0000    3  OP_CLOSURE          0 <fn fibonacci>
0002    |  OP_DEFINE_GLOBAL    1 'fibonacci'
0004   10  OP_CLOSURE          2 <fn compute_stats>
0006    |  OP_DEFINE_GLOBAL    3 'compute_stats'
0008   16  OP_CONSTANT         4 'Professor'
0010    |  OP_DEFINE_GLOBAL    5 'user'
0012   17  OP_CONSTANT         6 '10'
0014    |  OP_DEFINE_GLOBAL    7 'terms'
0016   19  OP_GET_GLOBAL       3 'compute_stats'
0018    |  OP_GET_GLOBAL       5 'user'
0020    |  OP_GET_GLOBAL       7 'terms'
0022    |  OP_CALL             2
0024    |  OP_POP
0025    |  OP_NIL
0026    |  OP_RETURN
```

---

### Step 8: View the Generated C99 Code (`--emit-c`)
> **What to say**: *"Finally, here is the native C transpilation output. The compiler translates our Fresh program into standalone, human-readable C99 with built-in runtime safety helpers for division-by-zero checks and string operations."*

```bash
python -m fresh run demo/quick_demo.fresh --emit-c
```
*Expected Output:*
```c
// Generated by Fresh Compiler C Transpiler
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <time.h>

// Helper runtimes for safe arithmetic and I/O...

long long fibonacci(long long n) {
    if ((n <= 1)) {
        return n;
    }
    return (fibonacci((n - 1)) + fibonacci((n - 2)));
}

void compute_stats(const char* name, long long count) {
    println_str("Processing:");
    long long result = fibonacci(count);
    println_str("Fibonacci(");
}

int main() {
    const char* user = "Professor";
    long long terms = 10;
    compute_stats(user, terms);
    return 0;
}
```

---

### Step 9: Static Type Checking Without Execution (`fresh check`)
> **What to say**: *"Unlike Python which crashes with a TypeError at runtime, Fresh catches type mismatches before any code runs."*

```bash
python -m fresh check demo/quick_demo.fresh
```
*Expected Output: Exits with code 0 (valid type signatures).*
