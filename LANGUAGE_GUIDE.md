# 📘 Fresh Language Specification & User Guide

Welcome to the **Fresh Language Guide**! This document provides a complete guide to writing code in **Fresh**, covering everything from basic syntax, data types, and control flow to advanced features like closures, structs, pattern matching with guards, multi-file module imports, project management, and the standard library.

---

## 📌 Table of Contents

1. [Source Files & Comments](#1-source-files--comments)
2. [Data Types & Literals](#2-data-types--literals)
3. [Variables & Type Annotations](#3-variables--type-annotations)
4. [Operators & Expression Precedence](#4-operators--expression-precedence)
5. [Control Flow](#5-control-flow)
   - [If / Else If / Else](#if--else-if--else)
   - [While Loops](#while-loops)
   - [For Loops](#for-loops)
   - [Break and Continue](#break-and-continue)
6. [Functions & Closures](#6-functions--closures)
   - [Named Functions](#named-functions)
   - [Anonymous Functions (Lambdas)](#anonymous-functions-lambdas)
   - [Closures & Captured State](#closures--captured-state)
7. [Structs (Records)](#7-structs-records)
8. [Arrays & Indexing](#8-arrays--indexing)
9. [Pattern Matching (`match`)](#9-pattern-matching-match)
10. [Modules & Imports System](#10-modules--imports-system)
11. [Developer Tooling & CLI](#11-developer-tooling--cli)
12. [Standard Library Reference](#12-standard-library-reference)
13. [Complete Code Examples](#13-complete-code-examples)

---

## 1. Source Files & Comments

### File Extension
Fresh source code files use the `.fresh` file extension (e.g., `program.fresh`).

### Single-Line Comments
Single-line comments start with `//` and continue until the end of the line:
```fresh
// This is a single-line comment
let x = 42; // Comment after code
```

### Multi-Line Comments
Multi-line comments start with `/*` and end with `*/`. Fresh supports **nested** multi-line comments:
```fresh
/* This is a multi-line comment
   /* Nested comment inside */
   Back to outer comment */
```

---

## 2. Data Types & Literals

Fresh supports 5 primitive data types and 2 compound data types:

| Type | Syntax / Literal | Description | Example |
| :--- | :--- | :--- | :--- |
| `int` | Integers | 64-bit signed integers | `42`, `-10`, `0` |
| `float` | Floating-point numbers | 64-bit double precision numbers | `3.14`, `-0.001`, `2.0` |
| `bool` | Booleans | Logical truth values | `true`, `false` |
| `string` | Text strings | UTF-8 encoded text literals | `"hello\nworld"` |
| `nil` | Absence of value | Represents null / empty value | `nil` |
| `[T]` | Arrays | Homogenous dynamic arrays of type `T` | `[1, 2, 3]`, `["a", "b"]` |
| `Struct` | Records | User-defined record types | `Point { x: 1.0, y: 2.0 }` |

### String Escape Sequences
Strings support standard escape sequences:
- `\n` — Newline
- `\t` — Horizontal tab
- `\"` — Double quote
- `\\` — Backslash
- `\0` — Null character

```fresh
let msg = "Hello,\t\"Fresh\"!\n";
```

---

## 3. Variables & Type Annotations

### Declaration & Initialization
Variables are declared using the `let` keyword:

```fresh
let age = 25;            // Inferred as int
let pi = 3.14159;        // Inferred as float
let is_valid = true;     // Inferred as bool
let greeting = "Hello";  // Inferred as string
```

### Explicit Type Annotations
You can optionally specify explicit type annotations using `: Type`:

```fresh
let count: int = 100;
let rate: float = 0.05;
let active: bool = false;
let message: string = "Welcome";
let numbers: [int] = [1, 2, 3];
```

### Variable Reassignment
Variables in Fresh can be reassigned using the `=` operator:

```fresh
let score = 0;
score = score + 10;
score = 25;
```

---

## 4. Operators & Expression Precedence

Fresh provides a full suite of arithmetic, comparison, logical, and unary operators:

### Operator Table

| Category | Operators | Examples |
| :--- | :--- | :--- |
| **Arithmetic** | `+`, `-`, `*`, `/`, `%` | `a + b`, `10 % 3` |
| **Comparison** | `==`, `!=`, `<`, `<=`, `>`, `>=` | `x >= 10`, `name == "Fresh"` |
| **Logical** | `&&` (AND), `||` (OR), `!` (NOT) | `a && b`, `!is_ready` |
| **Unary** | `-` (Negation), `!` (Logical Not) | `-5`, `!true` |

### String Concatenation
The `+` operator automatically performs string concatenation when either operand is a string:

```fresh
let greeting = "Hello, " + "World!"; // "Hello, World!"
```

### Precedence Hierarchy (Highest to Lowest)

1. Primary: Literals, identifiers, parenthesised expressions `(expr)`
2. Postfix / Access: Calls `foo()`, array indexing `arr[i]`, field access `obj.field`
3. Unary: `-expr`, `!expr`
4. Factor: `*`, `/`, `%`
5. Term: `+`, `-`
6. Comparison: `<`, `<=`, `>`, `>=`
7. Equality: `==`, `!=`
8. Logical AND: `&&`
9. Logical OR: `||`
10. Assignment: `=`

---

## 5. Control Flow

### If / Else If / Else
Conditional execution based on boolean expressions:

```fresh
let score = 85;

if (score >= 90) {
    println("Grade: A");
} else if (score >= 80) {
    println("Grade: B");
} else if (score >= 70) {
    println("Grade: C");
} else {
    println("Grade: F");
}
```

### While Loops
Executes a block repeatedly as long as the condition evaluates to `true`:

```fresh
let i = 0;
while (i < 5) {
    println("Iteration: " + to_string(i));
    i = i + 1;
}
```

### For Loops
C-style for loops with an initializer, condition, and increment expression:

```fresh
for (let i = 0; i < 5; i = i + 1) {
    println("i = " + to_string(i));
}
```

### Break and Continue
- `break`: Immediately exits the nearest enclosing loop.
- `continue`: Skips the rest of the current loop iteration and proceeds to the increment / condition.

```fresh
for (let i = 0; i < 10; i = i + 1) {
    if (i == 3) {
        continue; // Skip 3
    }
    if (i == 7) {
        break; // Exit loop when reaching 7
    }
    println(i);
}
```

---

## 6. Functions & Closures

### Named Functions
Functions are declared using `fn`, parameter type annotations, and an optional return type `-> Type`:

```fresh
fn add(a: int, b: int) -> int {
    return a + b;
}

fn greet(name: string) {
    println("Hello, " + name + "!");
}

let sum = add(10, 20); // 30
greet("Alice");
```

### Recursive Functions
Functions can call themselves recursively:

```fresh
fn fibonacci(n: int) -> int {
    if (n <= 1) {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}

let result = fibonacci(10); // 55
```

### Anonymous Functions (Lambdas)
Functions in Fresh are first-class values and can be passed as arguments or assigned to variables:

```fresh
let multiply = fn(x: int, y: int) -> int {
    return x * y;
};

println(multiply(6, 7)); // 42
```

### Closures & Captured State
Inner functions automatically capture variables from enclosing scopes using upvalues:

```fresh
fn make_counter(start: int) -> fn {
    let count = start;
    fn increment() -> int {
        count = count + 1;
        return count;
    }
    return increment;
}

let counter = make_counter(10);
println(counter()); // 11
println(counter()); // 12
```

---

## 7. Structs (Records)

Structs define custom composite data structures with typed fields:

```fresh
struct Point {
    x: float,
    y: float
}

// Instantiation
let p = Point { x: 3.0, y: 4.0 };

// Field Access
println(p.x); // 3.0
println(p.y); // 4.0

// Field Mutation
p.x = 10.5;
println(p.x); // 10.5
```

---

## 8. Arrays & Indexing

Arrays in Fresh are dynamic, homogenous collections of elements:

```fresh
let numbers = [10, 20, 30, 40];

// Indexing
println(numbers[0]); // 10

// Array Mutation
numbers[1] = 99;
println(numbers[1]); // 99

// Array Length
println(len(numbers)); // 4
```

---

## 9. Pattern Matching (`match`)

Fresh provides powerful pattern matching supporting literal matching, variable bindings, wildcards (`_`), and conditional `if` guard clauses:

```fresh
let val = 42;

let description = match val {
    0 => "Zero",
    1 => "One",
    v if v > 10 && v < 50 => "Between 10 and 50",
    _ => "Other number"
};

println(description); // "Between 10 and 50"
```

---

## 10. Modules & Imports System

Fresh supports modular programming across multiple source files.

### Importing Other Files
Use the `import` statement to include definitions from another `.fresh` file:

```fresh
// In math_utils.fresh:
fn square(x: int) -> int {
    return x * x;
}

// In main.fresh:
import "math_utils.fresh";

println(square(7)); // 49
```

### Identifier Import Syntax
```fresh
import math_utils; // Resolves math_utils.fresh in current or base directory
```

### Safety & Circular Import Detection
The Fresh `ModuleLoader` automatically caches imported modules to avoid duplicate evaluations and detects circular import loops (e.g. `a.fresh -> b.fresh -> a.fresh`), halting with diagnostic error `[E4001]`:
```text
error[E4001]: Circular module dependency detected: a.fresh -> b.fresh -> a.fresh
```

---

## 11. Developer Tooling & CLI

Fresh provides comprehensive command-line tooling for building, testing, checking, and formatting code:

| Command | Description | Example |
| :--- | :--- | :--- |
| `fresh run <file>` | Run a Fresh source file on the VM | `fresh run main.fresh` |
| `fresh run <file> --emit-c` | Transpile source code to standalone C | `fresh run main.fresh --emit-c` |
| `fresh check <file>` | Static analysis (scoping, types) without execution | `fresh check main.fresh` |
| `fresh fmt <file> [--check]` | Format source code deterministically | `fresh fmt main.fresh` |
| `fresh init <name>` | Scaffold a new Fresh project with `fresh.toml` | `fresh init myapp` |
| `fresh build [path]` | Build project to native C/binary | `fresh build myapp` |
| `fresh test [dir]` | Run automated test suite | `fresh test` |
| `fresh repl` | Start interactive Read-Eval-Print Loop | `fresh repl` |

---

## 12. Standard Library Reference

### Built-in I/O & Conversions
- `println(val)`: Prints a value to stdout with a newline.
- `print(val)`: Prints a value without a newline.
- `to_string(val)`: Converts any primitive value to its string representation.
- `to_int(val)`: Converts float or string to integer.
- `to_float(val)`: Converts int or string to float.
- `clock()`: Returns the current system timestamp in seconds (float).

### Array Built-ins
- `len(arr)`: Returns the number of elements in an array.
- `push(arr, val)`: Appends an element to the end of the array.
- `pop(arr)`: Removes and returns the last element.

### File I/O Built-ins
- `read_file(path)`: Reads the entire contents of a file as a string.
- `write_file(path, content)`: Writes text content to a file.
- `file_exists(path)`: Returns `true` if the file exists, `false` otherwise.

### Math Functions (`math_lib`)
- `sqrt(x)`: Square root.
- `pow(base, exp)`: Exponentiation.
- `abs(x)`: Absolute value.
- `floor(x)`: Round down to integer float.
- `ceil(x)`: Round up to integer float.
- `sin(x)`, `cos(x)`, `tan(x)`: Trigonometric functions.

---

## 13. Complete Code Examples

### Example 1: Modular Math Program
```fresh
// math.fresh
fn factorial(n: int) -> int {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

// main.fresh
import "math.fresh";

println("Factorial of 5: " + to_string(factorial(5)));
```

### Example 2: In-Place Quicksort Algorithm
```fresh
fn swap(arr: [int], i: int, j: int) {
    let temp = arr[i];
    arr[i] = arr[j];
    arr[j] = temp;
}

fn partition(arr: [int], low: int, high: int) -> int {
    let pivot = arr[high];
    let i = low - 1;

    for (let j = low; j < high; j = j + 1) {
        if (arr[j] <= pivot) {
            i = i + 1;
            swap(arr, i, j);
        }
    }
    swap(arr, i + 1, high);
    return i + 1;
}

fn quicksort(arr: [int], low: int, high: int) {
    if (low < high) {
        let pi = partition(arr, low, high);
        quicksort(arr, low, pi - 1);
        quicksort(arr, pi + 1, high);
    }
}

let numbers = [64, 34, 25, 12, 22, 11, 90];
println("Before: " + to_string(numbers));

quicksort(numbers, 0, len(numbers) - 1);

println("After:  " + to_string(numbers));
```
