# ⚡ The Complete Fresh Language Syntax Handbook & Demonstration Guide

This document is an exhaustive, practical syntax catalog containing **every single language construct, data type, statement, expression, and built-in function** in the Fresh Programming Language. Use this guide to study, test, or demonstrate Fresh live.

---

## 📑 Quick Navigation

1. [Variables & Type Annotations](#1-variables--type-annotations)
2. [Data Types & Literals](#2-data-types--literals)
3. [Operators (Arithmetic, Comparison, Logical)](#3-operators)
4. [Control Flow (If/Else, While, For, Break, Continue)](#4-control-flow)
5. [Functions & Recursion](#5-functions--recursion)
6. [Closures & Upvalues (State Capture)](#6-closures--upvalues)
7. [Struct Records & Field Mutation](#7-struct-records--field-mutation)
8. [Arrays & Multidimensional Matrices](#8-arrays--multidimensional-matrices)
9. [Pattern Matching (`match`) with Guards](#9-pattern-matching-with-guards)
10. [File I/O Subsystem](#10-file-io-subsystem)
11. [Math Standard Library](#11-math-standard-library)
12. [System, Time & Reflection](#12-system-time--reflection)
13. [Multi-File Modules (`import`)](#13-multi-file-modules-import)
14. [Full Live Demo Script (Copy & Run)](#14-full-live-demo-script-copy--run)

---

## 1. Variables & Type Annotations

Fresh supports both **explicit static typing** and **automatic local type inference**.

### 1.1 Inferred Variable Declaration
```fresh
// Inferred as int
let count = 10;

// Inferred as string
let message = "Hello from Fresh";

// Inferred as float
let pi = 3.14159;

// Inferred as bool
let is_ready = true;
```

### 1.2 Explicitly Typed Variable Declaration
```fresh
let score: int = 100;
let rate: float = 0.05;
let label: string = "Status OK";
let active: bool = false;
let empty = nil;
```

### 1.3 Variable Reassignment & Mutation
```fresh
let x = 5;
x = 10;
x = x + 1; // x is now 11
```

### 1.4 Static Type Protection
```fresh
let total = 50;
// total = "fifty"; // COMPILE ERROR [E3001]: Cannot assign 'string' to 'int' variable 'total'
```

---

## 2. Data Types & Literals

Fresh features 5 primitive types and 3 composite types:

| Type | Syntax Example | Notes |
|:---|:---|:---|
| `int` | `42`, `-10`, `0` | Signed 64-bit integer |
| `float` | `3.14`, `0.001`, `-7.5` | IEEE 754 64-bit double precision |
| `bool` | `true`, `false` | Strict boolean logic |
| `string` | `"Fresh Language\n"` | UTF-8 string with escape sequences |
| `nil` | `nil` | Represents the absence of a value |
| `[T]` | `[1, 2, 3]`, `["a", "b"]` | Dynamically-sized typed array |
| `struct` | `struct Point { x: int, y: int }` | User-defined record type |
| `fn` | `fn(x: int) -> int` | First-class callable function |

### String Escape Sequences
```fresh
let escaped = "Line 1\nLine 2\tTabbed \"Quoted\" \\ Backslash";
println(escaped);
```

---

## 3. Operators

### 3.1 Arithmetic Operators
```fresh
let sum = 10 + 5;        // 15 (Addition)
let diff = 20 - 8;       // 12 (Subtraction)
let prod = 4 * 7;        // 28 (Multiplication)
let quot = 30 / 5;       // 6  (Integer Division)
let rem = 17 % 5;        // 2  (Modulo)

// String Concatenation
let greeting = "Hello, " + "World!"; // "Hello, World!"
```

### 3.2 Comparison Operators
```fresh
let eq = (10 == 10);     // true  (Equal)
let ne = (10 != 5);      // true  (Not equal)
let lt = (3 < 7);        // true  (Less than)
let lte = (5 <= 5);      // true  (Less than or equal)
let gt = (8 > 2);        // true  (Greater than)
let gte = (6 >= 9);      // false (Greater than or equal)
```

### 3.3 Logical Operators
```fresh
let a = true;
let b = false;

let and_res = a && b;    // false (Logical AND)
let or_res = a || b;     // true  (Logical OR)
let not_res = !a;        // false (Logical NOT)
```

---

## 4. Control Flow

### 4.1 `if` / `else if` / `else`
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

### 4.2 `while` Loop
```fresh
let countdown = 3;
while (countdown > 0) {
    println("T-minus", countdown);
    countdown = countdown - 1;
}
println("Liftoff!");
```

### 4.3 `for` Loop
```fresh
// Standard 3-part for loop: initializer; condition; increment
let sum = 0;
for (let i = 1; i <= 10; i = i + 1) {
    sum = sum + i;
}
println("Sum 1..10 =", sum); // 55
```

### 4.4 `break` and `continue`
```fresh
for (let i = 0; i < 10; i = i + 1) {
    if (i == 3) {
        continue; // Skip number 3
    }
    if (i == 7) {
        break;    // Stop loop at 7
    }
    println("Number:", i);
}
```

---

## 5. Functions & Recursion

### 5.1 Basic Function Declaration
```fresh
fn add(a: int, b: int) -> int {
    return a + b;
}

let result = add(15, 25);
println("15 + 25 =", result); // 40
```

### 5.2 Functions Without Return Value (Void / Nil)
```fresh
fn say_hello(name: string) {
    println("Hello,", name);
}

say_hello("Vihaan");
```

### 5.3 Recursive Functions
```fresh
fn factorial(n: int) -> int {
    if (n <= 1) {
        return 1;
    }
    return n * factorial(n - 1);
}

println("factorial(5) =", factorial(5)); // 120

fn fibonacci(n: int) -> int {
    if (n <= 1) {
        return n;
    }
    return fibonacci(n - 1) + fibonacci(n - 2);
}

println("fibonacci(10) =", fibonacci(10)); // 55
```

---

## 6. Closures & Upvalues

Fresh functions are first-class citizens that can capture variables from their outer lexical scope.

### 6.1 State-Preserving Counter Factory
```fresh
fn make_counter() -> fn {
    let count = 0;
    fn increment() -> int {
        count = count + 1;
        return count;
    }
    return increment;
}

let c1 = make_counter();
println(c1()); // 1
println(c1()); // 2
println(c1()); // 3

let c2 = make_counter();
println(c2()); // 1 (independent state!)
```

### 6.2 Higher-Order Functions (Passing Functions as Arguments)
```fresh
fn apply_twice(f: fn, x: int) -> int {
    return f(f(x));
}

fn double_it(n: int) -> int {
    return n * 2;
}

let val = apply_twice(double_it, 5);
println("apply_twice(double, 5) =", val); // 20
```

---

## 7. Struct Records & Field Mutation

Structs are user-defined data types containing strongly-typed named fields.

### 7.1 Struct Declaration
```fresh
struct Player {
    name: string,
    health: int,
    score: float
}
```

### 7.2 Instantiation & Field Access
```fresh
let p1 = Player { name: "Hero", health: 100, score: 50.5 };

println("Player:", p1.name);
println("Health:", p1.health);
println("Score:", p1.score);
```

### 7.3 Field Mutation
```fresh
p1.health = p1.health - 25; // Took damage!
p1.score = p1.score + 100.0;

println("Updated Health:", p1.health); // 75
println("Updated Score:", p1.score);   // 150.5
```

---

## 8. Arrays & Multidimensional Matrices

### 8.1 Array Literal & Element Access
```fresh
let fruits = ["apple", "banana", "cherry"];
println("First:", fruits[0]);
println("Second:", fruits[1]);
```

### 8.2 Array Index Mutation
```fresh
fruits[0] = "avocado";
println("Mutated:", fruits[0]); // avocado
```

### 8.3 Dynamic Array Built-ins (`len`, `push`, `pop`)
```fresh
let nums = [10, 20, 30];

// Length
println("Length:", len(nums)); // 3

// Push element to end
push(nums, 40);
println("After push len:", len(nums)); // 4
println("Last element:", nums[3]);     // 40

// Pop element from end
let last = pop(nums);
println("Popped:", last);              // 40
println("Len after pop:", len(nums));  // 3
```

### 8.4 2D Multidimensional Matrices
```fresh
let matrix = [
    [1, 2, 3],
    [4, 5, 6],
    [7, 8, 9]
];

println("Center element:", matrix[1][1]); // 5

// Mutate matrix element
matrix[1][1] = 99;
println("New center:", matrix[1][1]);     // 99
```

---

## 9. Pattern Matching with Guards

Fresh provides an expressive `match` construct with literal matching, variable binding, wildcard `_`, and conditional `if` guards.

### 9.1 Basic Value Matching
```fresh
let code = 404;

let msg = match code {
    200 => "OK",
    404 => "Not Found",
    500 => "Internal Server Error",
    _   => "Unknown Code"
};

println("Status:", msg); // Not Found
```

### 9.2 Pattern Matching with Conditional Guards (`if`)
```fresh
let temperature = 32;

let report = match temperature {
    t if t <= 0  => "Freezing",
    t if t < 20  => "Cold",
    t if t <= 30 => "Pleasant",
    t if t > 30  => "Hot",
    _            => "Invalid"
};

println("Weather is:", report); // Hot
```

### 9.3 Matching with Guard Predicates on Structured Values
```fresh
let http_status = 200;
let is_admin = true;

let access = match http_status {
    200 if is_admin  => "200: Admin Access Granted",
    200 if !is_admin => "200: Guest Access Granted",
    403              => "403: Forbidden",
    _                => "Other Status"
};

println("Result:", access); // 200: Admin Access Granted
```

---

## 10. File I/O Subsystem

Fresh provides built-in file operations directly out of the box:

### 10.1 Writing a File (`write_file`)
```fresh
let ok = write_file("demo_file.txt", "Fresh Language File I/O Demo\nCreated successfully!");
println("File written successfully?", ok); // true
```

### 10.2 Checking File Existence (`file_exists`)
```fresh
let exists = file_exists("demo_file.txt");
println("Does file exist?", exists); // true
```

### 10.3 Reading a File (`read_file`)
```fresh
let content = read_file("demo_file.txt");
println("--- File Content ---");
println(content);
println("-------------------");
```

---

## 11. Math Standard Library

Fresh includes an optimized native math library:

```fresh
println("abs(-42)        =", abs(-42));        // 42
println("sqrt(81.0)      =", sqrt(81.0));      // 9.0
println("pow(2.0, 8.0)   =", pow(2.0, 8.0));   // 256.0
println("min(14, 29)     =", min(14, 29));     // 14
println("max(14, 29)     =", max(14, 29));     // 29
println("floor(4.89)     =", floor(4.89));     // 4
println("ceil(4.12)      =", ceil(4.12));      // 5
println("round(4.5)      =", round(4.5));      // 5
```

---

## 12. System, Time & Reflection

### 12.1 High-Resolution Timestamp (`clock`)
```fresh
let start = clock();

// Perform some calculations
let total = 0;
for (let i = 0; i < 10000; i = i + 1) {
    total = total + i;
}

let elapsed = clock() - start;
println("Calculated total in:", elapsed, "seconds");
```

### 12.2 Runtime Type Inspection (`type`)
```fresh
println("Type of 42:       ", type(42));           // int
println("Type of 3.14:     ", type(3.14));         // float
println("Type of 'Hello':  ", type("Hello"));      // string
println("Type of true:     ", type(true));         // bool
println("Type of nil:      ", type(nil));          // nil
println("Type of array:    ", type([1, 2, 3]));    // array
```

### 12.3 Type Conversions (`to_string`, `to_int`, `to_float`)
```fresh
let s = to_string(100);    // "100"
let i = to_int("456");     // 456
let f = to_float("12.75"); // 12.75

println("Parsed integer + 4:", i + 4); // 460
```

---

## 13. Multi-File Modules (`import`)

Fresh allows modular project organization with circular import protection.

### `math_utils.fresh`:
```fresh
fn square(x: int) -> int {
    return x * x;
}
```

### `main.fresh`:
```fresh
import "./math_utils.fresh";

let val = square(8);
println("Square of 8 is:", val); // 64
```

---

## 14. Full Live Demo Script (Copy & Run)

Save the following code into `demo/master_showcase.fresh` and run it with `python -m fresh run demo/master_showcase.fresh` to demonstrate **every single feature** live to an audience!

```fresh
// ================================================================
//        FRESH PROGRAMMING LANGUAGE — MASTER SYNTAX DEMO
// ================================================================

println("================================================================");
println("       *** FRESH PROGRAMMING LANGUAGE MASTER SYNTAX DEMO ***       ");
println("================================================================");

// 1. PRIMITIVES & OPERATORS
let my_int: int = 42;
let my_float: float = 3.14159;
let my_bool: bool = true;
let my_str: string = "Fresh Language";
let my_nil = nil;

println("\n[1] PRIMITIVES & ARITHMETIC:");
println("int:", my_int, "| float:", my_float, "| bool:", my_bool, "| str:", my_str);
println("Math calculation (42 * 2 + 10 / 2 - 4 % 3) =", 42 * 2 + 10 / 2 - 4 % 3);

// 2. CONTROL FLOW (IF / WHILE / FOR)
println("\n[2] CONTROL FLOW:");
let test_score = 88;
if (test_score >= 90) {
    println("Score 88: Grade A");
} else if (test_score >= 80) {
    println("Score 88: Grade B");
} else {
    println("Score 88: Grade C or below");
}

let even_sum = 0;
for (let i = 1; i <= 10; i = i + 1) {
    if (i % 2 == 0) {
        even_sum = even_sum + i;
    }
}
println("Sum of even numbers 1..10 =", even_sum);

// 3. FUNCTIONS & RECURSION
println("\n[3] FUNCTIONS & RECURSION:");
fn fib(n: int) -> int {
    if (n <= 1) {
        return n;
    }
    return fib(n - 1) + fib(n - 2);
}
println("fibonacci(10) =", fib(10));

// 4. CLOSURES WITH ENCLOSED STATE
println("\n[4] CLOSURES & UPVALUES:");
fn make_counter(start: int) -> fn {
    let count = start;
    fn tick() -> int {
        count = count + 1;
        return count;
    }
    return tick;
}
let counter = make_counter(0);
println("counter() tick 1:", counter());
println("counter() tick 2:", counter());
println("counter() tick 3:", counter());

// 5. STRUCT RECORDS & MUTATION
println("\n[5] STRUCTS & MUTATION:");
struct Hero {
    name: string,
    health: int,
    power: float
}
let hero = Hero { name: "Knight", health: 100, power: 45.5 };
println("Initial Hero:", hero.name, "HP:", hero.health, "Power:", hero.power);
hero.health = hero.health - 20; // Mutate field
println("Hero took 20 damage! New HP:", hero.health);

// 6. ARRAYS & 2D MATRICES
println("\n[6] DYNAMIC ARRAYS & 2D MATRICES:");
let items = ["shield", "sword", "potion"];
println("Items len:", len(items), "first item:", items[0]);
push(items, "helmet");
println("After push('helmet'), len is:", len(items));
let removed = pop(items);
println("Popped item:", removed, "| remaining len:", len(items));

let grid = [
    [10, 20],
    [30, 40]
];
println("Grid[1][0] =", grid[1][0]);

// 7. PATTERN MATCHING WITH GUARDS
println("\n[7] PATTERN MATCHING WITH GUARDS:");
let code = 200;
let is_vip = true;
let status_msg = match code {
    200 if is_vip  => "200: VIP Access Granted",
    200 if !is_vip => "200: Standard Access",
    404            => "404: Resource Not Found",
    _              => "Other Status"
};
println("Match result:", status_msg);

// 8. MATH LIBRARY
println("\n[8] STANDARD MATH LIBRARY:");
println("abs(-75)      =", abs(-75));
println("sqrt(144.0)   =", sqrt(144.0));
println("pow(3.0, 3.0) =", pow(3.0, 3.0));
println("min(25, 9)    =", min(25, 9));
println("max(25, 9)    =", max(25, 9));

// 9. FILE I/O SUBSYSTEM
println("\n[9] FILE I/O SUBSYSTEM:");
let filename = "demo_test_file.txt";
let write_ok = write_file(filename, "Hello from Fresh File I/O!\nWritten successfully.");
println("Wrote file?", write_ok);
println("File exists?", file_exists(filename));
let read_back = read_file(filename);
println("File contents:\n" + read_back);

// 10. SYSTEM REFLECTION
println("\n[10] SYSTEM & REFLECTION:");
println("Type of hero: ", type(hero));
println("Type of items:", type(items));
println("Clock timestamp:", clock());

println("\n================================================================");
println("      [SUCCESS] ALL FRESH SYNTAX DEMONSTRATIONS COMPLETED!      ");
println("================================================================");
```

---

## 15. How to Run & Verify

```bash
# 1. Run the master demonstration script:
python -m fresh run demo/master_showcase.fresh

# 2. Check types without running:
python -m fresh check demo/master_showcase.fresh

# 3. Format the code:
python -m fresh fmt demo/master_showcase.fresh

# 4. View disassembled bytecode:
python -m fresh run demo/master_showcase.fresh --disassemble
```
