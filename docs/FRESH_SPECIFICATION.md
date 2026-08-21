# The Fresh Language Specification (v0.1.0)
## Normative Reference Specification

---

## 1. Introduction & Scope

This document is the official, normative specification for the **Fresh Programming Language** (version 0.1.0). A conforming Fresh implementation must adhere to all lexical, syntactic, semantic, and runtime specifications defined in this document.

---

## 2. Lexical Structure

### 2.1 Character Set & Encodings
Fresh source code is a sequence of Unicode characters encoded in UTF-8. Any malformed UTF-8 byte sequences must be rejected during lexical scanning.

### 2.2 Whitespace & Comments
Whitespace characters (space `\u0020`, tab `\t`, newline `\n`, carriage return `\r`) delimit tokens and are ignored otherwise.

Comments:
- **Line Comments**: Start with `//` and extend to the end of the line.
- **Block Comments**: Enclosed in `/* ... */` (nested block comments are supported).

### 2.3 Identifiers & Keywords
Identifiers start with `[a-zA-Z_]` followed by zero or more `[a-zA-Z0-9_]`.

**Reserved Keywords**:
`let`, `fn`, `struct`, `import`, `if`, `else`, `while`, `for`, `break`, `continue`, `return`, `match`, `true`, `false`, `nil`, `and`, `or`, `not`

### 2.4 Literals
- **Integers**: `[0-9]+` representing 64-bit signed integers.
- **Floats**: `[0-9]+\.[0-9]+` representing 64-bit IEEE 754 double precision floats.
- **Booleans**: `true`, `false`.
- **Nil**: `nil`.
- **Strings**: Double-quoted sequences `"..."` supporting escape sequences `\\`, `\"`, `\n`, `\t`, `\r`.

---

## 3. Grammar & Concrete Syntax (EBNF)

```ebnf
Program        ::= Statement* EOF
Statement      ::= VarDecl | FnDecl | StructDecl | ImportStmt | IfStmt | WhileStmt | ForStmt | ReturnStmt | BreakStmt | ContinueStmt | ExprStmt | Block
VarDecl        ::= "let" IDENTIFIER (":" TypeAnnotation)? ("=" Expr)? ";"
FnDecl         ::= "fn" IDENTIFIER "(" ParamList? ")" ("->" TypeAnnotation)? Block
StructDecl     ::= "struct" IDENTIFIER "{" FieldList? "}"
ImportStmt     ::= "import" (STRING_LIT | IDENTIFIER) ";"
IfStmt         ::= "if" "(" Expr ")" Block ("else" (IfStmt | Block))?
WhileStmt      ::= "while" "(" Expr ")" Block
ForStmt        ::= "for" "(" VarDecl? Expr? ";" Expr? ")" Block
ReturnStmt     ::= "return" Expr? ";"
BreakStmt      ::= "break" ";"
ContinueStmt   ::= "continue" ";"
ExprStmt       ::= Expr ";"
Block          ::= "{" Statement* "}"
```

---

## 4. Operator Precedence & Associativity

| Precedence | Operator | Description | Associativity |
|---|---|---|---|
| 1 | `=` | Assignment | Right-to-left |
| 2 | `or` | Logical OR | Left-to-right (short-circuit) |
| 3 | `and` | Logical AND | Left-to-right (short-circuit) |
| 4 | `==`, `!=` | Equality | Left-to-right |
| 5 | `<`, `<=`, `>`, `>=` | Relational | Left-to-right |
| 6 | `+`, `-` | Additive, String Concatenation | Left-to-right |
| 7 | `*`, `/`, `%` | Multiplicative | Left-to-right |
| 8 | `not`, `-` (unary) | Logical NOT, Negation | Right-to-left |
| 9 | `()`, `[]`, `.field` | Function Call, Indexing, Field Access | Left-to-right |

---

## 5. Type System & Inference

Fresh uses strict static typing with local type inference:
- **`int`**: 64-bit signed two's complement integer.
- **`float`**: 64-bit IEEE 754 floating-point.
- **`bool`**: Boolean value (`true` or `false`).
- **`string`**: Immutable UTF-8 string.
- **`[T]`**: Uniform dynamically sized list/array of type `T`.
- **Structs**: User-defined compound types with named typed fields.
- **Functions**: `fn(T1, T2) -> R` first-class function signatures.
- **`nil`**: Null unit value.

---

## 6. Closures & Upvalues

Functions capture enclosing lexical variables via upvalues. Upvalues reference heap-allocated cells that remain valid beyond the lifetime of the enclosing activation frame.

```fresh
fn make_counter() -> fn {
    let count = 0;
    fn inc() -> int {
        count = count + 1;
        return count;
    }
    return inc;
}
let counter = make_counter();
println(counter()); // 1
println(counter()); // 2
```

---

## 7. Pattern Matching

The `match` expression evaluates a subject against sequential pattern branches:
- **Literal Pattern**: `42 => ...`
- **Variable Pattern**: `x => ...` (binds the subject value to `x`)
- **Wildcard Pattern**: `_ => ...` (matches any value)
- **Guard Clause**: `v if v > 10 => ...` (conditional filter)

```fresh
let val = 42;
let category = match val {
    v if v > 100 => "big",
    v if v > 10 => "medium",
    _ => "small",
};
println(category);
```

---

## 8. Runtime Error Semantics

Conforming runtimes must produce structured runtime errors:
1. **Division by Zero (`[E5001]`)**: Attempting integer or float division/modulo by zero.
2. **Index Out of Bounds (`[E5002]`)**: Indexing arrays or strings beyond `[0, len - 1]`.
3. **Stack Overflow (`[E5003]`)**: Call frame stack exceeding configured threshold.
4. **Invalid Field Access (`[E5004]`)**: Accessing a struct field that does not exist.

---

## 9. Backend Capability Matrix

| Feature | VM Backend | Native C Backend | Parity Status |
|---|---|---|---|
| Primitive Types (`int`, `float`, `bool`, `string`) | Supported | Supported | Verified 1:1 |
| Arithmetic & Logical Operators | Supported | Supported | Verified 1:1 |
| Structs & Field Getters/Setters | Supported | Supported | Verified 1:1 |
| Functions & Recursion | Supported | Supported | Verified 1:1 |
| While & For Loops, Branching | Supported | Supported | Verified 1:1 |
| Closures & Upvalues | Supported | Explicit Rejection `[E3001]` | Specified |
| Pattern Matching (`match`) | Supported | Explicit Rejection `[E3001]` | Specified |

---

## 10. Standard Library Specification

### Built-in Functions

- **`println(val: any) -> nil`**: Prints value representation to standard output followed by a newline.
- **`print(val: any) -> nil`**: Prints value representation without a trailing newline.
- **`to_string(val: any) -> string`**: Converts any primitive, struct, or array into its canonical string representation.
- **`type(val: any) -> string`**: Returns the runtime type name (`"int"`, `"float"`, `"bool"`, `"string"`, `"array"`, `"struct"`, `"fn"`, `"nil"`).
- **`len(val: [T] | string) -> int`**: Returns element count for arrays or byte/character length for strings.
- **`push(arr: [T], val: T) -> nil`**: Appends an element to the end of a dynamic array.
- **`pop(arr: [T]) -> T`**: Removes and returns the last element of a dynamic array.
- **`clock() -> float`**: Returns high-resolution monotonic timestamp in seconds.
- **`read_file(path: string) -> string`**: Reads text file contents as UTF-8 string.
- **`write_file(path: string, content: string) -> nil`**: Writes UTF-8 string to specified filepath.
- **`file_exists(path: string) -> bool`**: Returns whether the specified file exists on disk.

### Standard Math Module (`fresh.stdlib.math_lib`)

- **`abs(x: int | float) -> int | float`**: Absolute value.
- **`sqrt(x: float) -> float`**: Square root.
- **`pow(base: float, exp: float) -> float`**: Power / exponentiation.
- **`min(a: int | float, b: int | float) -> int | float`**: Minimum of two numbers.
- **`max(a: int | float, b: int | float) -> int | float`**: Maximum of two numbers.
- **`floor(x: float) -> int`**: Largest integer less than or equal to `x`.
- **`ceil(x: float) -> int`**: Smallest integer greater than or equal to `x`.
- **`round(x: float) -> int`**: Nearest integer to `x`.

