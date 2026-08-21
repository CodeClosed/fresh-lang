# 📘 Fresh Language User Guide & Tutorial

Welcome to the **Fresh Language Guide**! Fresh is a modern, statically typed, compiled programming language designed to combine high readability, strong type safety, and fast bytecode execution.

This guide provides a comprehensive, beginner-friendly walkthrough of the language—from writing your first `"Hello, World!"` to advanced patterns like closures, nested structs, and pattern matching with guards.

---

## 📑 Table of Contents

1. [Hello, World!](#1-hello-world)
2. [Comments & File Structure](#2-comments--file-structure)
3. [Data Types & Literals](#3-data-types--literals)
4. [Variables & Type Inference](#4-variables--type-inference)
5. [Operators & Precedence](#5-operators--precedence)
6. [Control Flow: Conditionals & Loops](#6-control-flow-conditionals--loops)
7. [Functions, Recursion & Higher-Order Functions](#7-functions-recursion--higher-order-functions)
8. [Closures & State Capture](#8-closures--state-capture)
9. [Struct Records & Mutation](#9-struct-records--mutation)
10. [Dynamic Arrays & 2D Matrices](#10-dynamic-arrays--2d-matrices)
11. [Pattern Matching (`match`) with Guards](#11-pattern-matching-match-with-guards)
12. [Module Import System](#12-module-import-system)
13. [Standard Library Reference](#13-standard-library-reference)
14. [CLI Developer Tooling](#14-cli-developer-tooling)

---

## 1. Hello, World!

Fresh source code files use the **`.fresh`** file extension. Every program can write statements at the top level or organize code into functions:

```fresh
// hello.fresh
println("Hello, World from Fresh! ⚡");
```

Run this file from your terminal:

```bash
# Option 1: Direct command
fresh run hello.fresh

# Option 2: Windows local repository wrapper
.\fresh run hello.fresh

# Option 3: Universal Python command
python -m fresh run hello.fresh
```


---

## 2. Comments & File Structure

Fresh supports both single-line and multi-line comments. Multi-line comments can be nested safely:

```fresh
// Single-line comment: explain the next line
let port = 8080;

/* Multi-line block comment:
   /* Nested comment block */
   Useful for commenting out large sections of code.
*/
```

---

## 3. Data Types & Literals

Fresh features 5 primitive types and 2 compound types:

| Type | Name | Literal Syntax | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| `int` | Integer | `42`, `-10`, `0` | 64-bit signed integer | `let x: int = 100;` |
| `float` | Float | `3.14`, `-0.5`, `2.0` | 64-bit IEEE 754 double | `let pi: float = 3.14159;` |
| `bool` | Boolean | `true`, `false` | Logical boolean | `let is_open: bool = true;` |
| `string` | String | `"..."` | UTF-8 encoded text string | `let s: string = "Fresh";` |
| `nil` | Nil | `nil` | Represents the absence of a value | `let n = nil;` |
| `[T]` | Dynamic Array | `[elem1, elem2, ...]` | Homogeneous dynamic list of type `T` | `let arr: [int] = [1, 2, 3];` |
| `Struct` | Record | `Point { x: 1.0, y: 2.0 }` | User-defined named structure | `let pt = Point { x: 0.0, y: 0.0 };` |

### String Escape Sequences
Strings support common escape sequences:
- `\n` — Newline
- `\t` — Tab
- `\"` — Double quote
- `\\` — Backslash

```fresh
let greeting = "Line 1\nLine 2 with \"quotes\" and a \ttab";
```

---

## 4. Variables & Type Inference

### Declaration with `let`
Variables are declared using the `let` keyword:

```fresh
let count = 10;          // Inferred as int
let price = 19.99;       // Inferred as float
let is_ready = true;     // Inferred as bool
let title = "Fresh App"; // Inferred as string
```

### Explicit Type Annotations
You can explicitly declare types for documentation and strict checking:

```fresh
let max_retries: int = 5;
let threshold: float = 0.85;
let debug_mode: bool = false;
let user_name: string = "Alice";
```

### Mutation & Scoping
Variables can be reassigned within their scope:

```fresh
let total = 0;
total = total + 50;

{
    // Block scope creates a local scope
    let inner_val = 100;
    total = total + inner_val;
}
// inner_val is no longer in scope here
```

---

## 5. Operators & Precedence

Fresh supports standard mathematical, comparison, and boolean logic operators:

### Arithmetic Operators
```fresh
let sum  = 10 + 5;   // 15 (Addition)
let diff = 10 - 5;   // 5  (Subtraction)
let prod = 10 * 5;   // 50 (Multiplication)
let quot = 10 / 2;   // 5  (Division)
let rem  = 10 % 3;   // 1  (Modulo)
let neg  = -sum;     // -15 (Unary negation)
```

### Comparison Operators
```fresh
let a = 10;
let b = 20;

let eq  = (a == b);  // false (Equal)
let neq = (a != b);  // true  (Not Equal)
let lt  = (a < b);   // true  (Less Than)
let lte = (a <= b);  // true  (Less Than or Equal)
let gt  = (a > b);   // false (Greater Than)
let gte = (a >= b);  // false (Greater Than or Equal)
```

### Logical Operators (with Short-Circuiting)
```fresh
let cond1 = true && false; // false (Logical AND)
let cond2 = true || false; // true  (Logical OR)
let cond3 = !true;         // false (Logical NOT)
```

---

## 6. Control Flow: Conditionals & Loops

### `if` / `else if` / `else`
```fresh
let score = 85;

if (score >= 90) {
    println("Grade: A");
} else {
    if (score >= 80) {
        println("Grade: B");
    } else {
        println("Grade: C");
    }
}
```

### `while` Loops
```fresh
let counter = 0;
while (counter < 5) {
    println("Counter is: " + to_string(counter));
    counter = counter + 1;
}
```

### `for` Loops with `break` and `continue`
```fresh
let sum = 0;
for (let i = 0; i < 20; i = i + 1) {
    if (i % 2 != 0) {
        continue; // Skip odd numbers
    }
    if (i > 10) {
        break; // Stop loop once past 10
    }
    sum = sum + i;
}
println("Sum of even numbers 0..10: " + to_string(sum)); // 30
```

---

## 7. Functions, Recursion & Higher-Order Functions

### Named Functions
Functions are declared with `fn`, optional parameter types, and an optional return type `-> ReturnType`:

```fresh
fn add(x: int, y: int) -> int {
    return x + y;
}

let result = add(15, 27);
println("Result: " + to_string(result)); // 42
```

### Recursion
```fresh
fn fibonacci(n: int) -> int {
    if (n <= 1) {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}

println("Fibonacci(10) = " + to_string(fibonacci(10))); // 55
```

### Anonymous Functions (Lambdas)
```fresh
let multiply = fn(a: int, b: int) -> int {
    return a * b;
};

println("6 * 7 = " + to_string(multiply(6, 7))); // 42
```

---

## 8. Closures & State Capture

Fresh functions are first-class citizens that can capture variables from their enclosing lexical scope (upvalues):

```fresh
fn make_counter(start: int) -> fn {
    let count = start;
    fn increment() -> int {
        count = count + 1;
        return count;
    }
    return increment;
}

let counter1 = make_counter(0);
let counter2 = make_counter(100);

println(to_string(counter1())); // 1
println(to_string(counter1())); // 2
println(to_string(counter2())); // 101
println(to_string(counter1())); // 3 (counter1 maintains independent state!)
```

### Custom Map & Filter with Closures
```fresh
fn map_ints(arr: [int], transform: fn) -> [int] {
    let out: [int] = [];
    for (let i = 0; i < len(arr); i = i + 1) {
        push(out, transform(arr[i]));
    }
    return out;
}

let nums = [1, 2, 3, 4, 5];
let double_fn = fn(n: int) -> int { return n * 2; };
let doubled = map_ints(nums, double_fn);

println("Doubled: " + to_string(doubled)); // [2, 4, 6, 8, 10]
```

---

## 9. Struct Records & Mutation

Structs define typed, named records:

```fresh
struct Vector3 {
    x: float,
    y: float,
    z: float
}

struct Player {
    name: string,
    pos: Vector3,
    health: int
}

// Instantiation
let p1 = Player {
    name: "Hero",
    pos: Vector3 { x: 0.0, y: 10.0, z: 0.0 },
    health: 100
};

// Access fields
println("Player " + p1.name + " at y=" + to_string(p1.pos.y));

// In-place field mutation
p1.pos.x = 25.5;
p1.health = p1.health - 20;

println("Updated HP: " + to_string(p1.health)); // 80
```

---

## 10. Dynamic Arrays & 2D Matrices

Arrays are dynamically sized and indexed using `[index]` (0-based):

```fresh
let fruits: [string] = ["apple", "banana"];

// push adds to the end
push(fruits, "cherry");
println("Length: " + to_string(len(fruits))); // 3

// pop removes from the end
let last_fruit = pop(fruits); // "cherry"
println("Popped: " + last_fruit);

// Index read and write
fruits[0] = "avocado";
println("First fruit: " + fruits[0]); // avocado
```

### Multi-Dimensional Matrices
```fresh
let matrix = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
];

// Read row 1, col 2
println("Element at (1, 2): " + to_string(matrix[1][2])); // 6

// Mutate cell (1, 1)
matrix[1][1] = 99;
println("Modified center: " + to_string(matrix[1][1])); // 99
```

---

## 11. Pattern Matching (`match`) with Guards

Fresh supports expressive pattern matching with literal values, variable bindings, wildcard defaults (`_`), and conditional `if` guard expressions:

```fresh
fn classify_http(code: int, authenticated: bool) -> string {
    return match code {
        200 if authenticated => "200 OK (Authorized User)",
        200 if !authenticated => "200 OK (Guest)",
        401 => "401 Unauthorized",
        404 => "404 Not Found",
        err if err >= 500 && err < 600 => "Server Error (" + to_string(err) + ")",
        _ => "Unknown HTTP Code"
    };
}

println(classify_http(200, true));  // 200 OK (Authorized User)
println(classify_http(200, false)); // 200 OK (Guest)
println(classify_http(404, false)); // 404 Not Found
println(classify_http(503, true));  // Server Error (503)
println(classify_http(302, false)); // Unknown HTTP Code
```

---

## 12. Module Import System

Organize large programs cleanly across multiple `.fresh` source files:

### Defining a Module (`math_utils.fresh`)
```fresh
// math_utils.fresh
fn square(x: int) -> int {
    return x * x;
}

fn cube(x: int) -> int {
    return x * x * x;
}
```

### Importing into Another File (`main.fresh`)
```fresh
// main.fresh
import "math_utils.fresh";

let sq = square(6);
let cb = cube(3);

println("6 squared: " + to_string(sq)); // 36
println("3 cubed: " + to_string(cb));   // 27
```

Fresh automatically resolves relative paths, caches duplicate imports, and detects and prevents circular imports (`[E4001]`).

---

## 13. Standard Library Reference

### Console Output
- `println(val: any)` — Prints value followed by a newline.
- `print(val: any)` — Prints value without trailing newline.

### Inspection & Conversions
- `to_string(val: any) -> string` — Converts integer, float, boolean, or struct to string.
- `type(val: any) -> string` — Returns runtime type name (`"int"`, `"float"`, `"string"`, `"bool"`).
- `len(arr: [T] | str: string) -> int` — Returns number of elements in array or string length.

### Dynamic Array Operations
- `push(arr: [T], item: T)` — Appends item to array end.
- `pop(arr: [T]) -> T` — Removes and returns the last element.

### Math Library
- `abs(x: float | int) -> float | int` — Absolute value.
- `sqrt(x: float) -> float` — Square root.
- `pow(base: float, exponent: float) -> float` — Power calculation.
- `min(a: int | float, b: int | float)` — Minimum of two values.
- `max(a: int | float, b: int | float)` — Maximum of two values.
- `floor(x: float) -> float` — Floor round down.
- `ceil(x: float) -> float` — Ceiling round up.
- `round(x: float) -> float` — Round to nearest integer.

### System & File I/O
- `clock() -> float` — High-resolution timestamp in seconds.
- `write_file(path: string, content: string)` — Writes UTF-8 text to disk file.
- `read_file(path: string) -> string` — Reads entire file content as string.
- `file_exists(path: string) -> bool` — Checks if file exists on disk.

---

## 14. CLI Developer Tooling

Fresh comes with a full suite of built-in developer tools accessible via the CLI:

```bash
# General invocation methods on all commands:
fresh <command> [args]           # Direct command (if PATH configured)
.\fresh <command> [args]         # Windows repository wrapper
python -m fresh <command> [args] # Universal Python command
```

---

### 14.1 `fresh run <file>` — Program Execution
Compiles your code through all frontend and backend passes and executes it on the Bytecode VM:

```bash
fresh run my_script.fresh
```

#### Compiler Inspection Options
You can inspect intermediate representations at any phase of compilation:

- **`--dump-tokens`**: Prints scanner tokens with line and column numbers.
  ```bash
  fresh run my_script.fresh --dump-tokens
  ```
- **`--dump-ast`**: Prints the formatted Abstract Syntax Tree from the Pratt parser.
  ```bash
  fresh run my_script.fresh --dump-ast
  ```
- **`--disassemble`**: Prints disassembled VM bytecode instructions and constant pool.
  ```bash
  fresh run my_script.fresh --disassemble
  ```
- **`--emit-c`**: Transpiles the Fresh AST into standalone C99 source code.
  ```bash
  fresh run my_script.fresh --emit-c
  ```

---

### 14.2 `fresh check <file>` — Static Type Checking & Linting
Runs lexical scanning, parsing, name resolution, and static type checking without executing the script. Catches type errors, undefined variables, and mismatched function signatures:

```bash
fresh check my_script.fresh
```
*Output on success:* `Check passed for 'my_script.fresh'.`

---

### 14.3 `fresh fmt <file>` — Deterministic Code Formatter
Formats Fresh source files with standardized indentation, spacing, and brace placement:

```bash
# Format file in-place:
fresh fmt my_script.fresh

# Verify formatting without modifying (returns exit code 1 if unformatted, ideal for CI):
fresh fmt my_script.fresh --check
```

---

### 14.4 `fresh init <name>` — Project Scaffolding
Initializes a new Fresh project directory with a manifest and standard layout:

```bash
fresh init my_project
```
*Creates:*
```text
my_project/
├── fresh.toml         # Project manifest (package metadata & entry point)
├── src/
│   └── main.fresh     # Application entrypoint
└── tests/
    └── test_basic.fresh
```

---

### 14.5 `fresh build [path]` — Native Executable Compiler
Reads `fresh.toml`, resolves all imported modules, and compiles the project entrypoint into a standalone native binary executable using the C backend (`gcc`/`clang`):

```bash
cd my_project
fresh build
```
*Output:* `Build succeeded: 'build/my_project.exe'` *(Run directly with `./build/my_project.exe` without Python!)*

---

### 14.6 `fresh test [path]` — Automated Testing
Runs the test suite using pytest directly from the CLI:

```bash
fresh test
```

---

### 14.7 `fresh repl` — Interactive REPL
Starts an interactive Read-Eval-Print-Loop session to test language features live:

```bash
fresh repl
```
```text
Fresh Programming Language v0.1.0
Type 'exit()' or Ctrl+C to quit.

fresh> let a = 10;
nil
fresh> let b = 25;
nil
fresh> a + b * 2;
60
fresh> fn greet(name: string) -> string { return "Hello, " + name; }
nil
fresh> greet("Fresh")
Hello, Fresh
fresh> exit()
```

