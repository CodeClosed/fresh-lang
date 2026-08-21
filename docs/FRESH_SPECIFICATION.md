# 📜 The Fresh Language Specification (v0.1.0)
## Normative Architecture & Language Reference

---

## 1. Introduction & Conformance

This document is the official, normative specification for the **Fresh Programming Language** (version 0.1.0). A conforming Fresh implementation must adhere to all lexical, syntactic, semantic, and runtime rules defined in this document.

---

## 2. Lexical Grammar

### 2.1 Character Set & Source Encoding
Fresh source code is a sequence of Unicode characters encoded in UTF-8. Non-UTF-8 byte sequences must be rejected at scan time.

### 2.2 Whitespace & Comments
- **Whitespace**: Spaces (`\u0020`), horizontal tabs (`\t`), newlines (`\n`), and carriage returns (`\r`) delimit tokens and are otherwise discarded.
- **Line Comments**: Begin with `//` and extend to the end of the line.
- **Block Comments**: Enclosed within `/*` and `*/`. Block comments may be arbitrarily nested.

### 2.3 Keywords & Identifiers
**Keywords** are reserved and cannot be used as variable or function names:
```text
let      fn       struct   import   if       else     while    for
break    continue return   match    true     false    nil
```

**Identifiers** match the regular expression:
```regex
[a-zA-Z_][a-zA-Z0-9_]*
```

### 2.4 Literals
- **Integer Literals**: Decimal sequences `[0-9]+` representing signed 64-bit integers.
- **Float Literals**: Decimal floating-point sequences `[0-9]+\.[0-9]+` conforming to IEEE 754 double precision.
- **Boolean Literals**: `true` and `false`.
- **Nil Literal**: `nil`.
- **String Literals**: Double-quoted sequences `"..."` supporting escape sequences:
  - `\n` — Line Feed (U+000A)
  - `\t` — Horizontal Tab (U+0009)
  - `\"` — Double Quote (U+0022)
  - `\\` — Backslash (U+005C)
  - `\0` — Null Character (U+0000)

---

## 3. Syntactic Grammar (EBNF)

```ebnf
Program        ::= Statement* EOF

Statement      ::= VarDecl
                 | FnDecl
                 | StructDecl
                 | ImportStmt
                 | IfStmt
                 | WhileStmt
                 | ForStmt
                 | ReturnStmt
                 | BreakStmt
                 | ContinueStmt
                 | ExprStmt
                 | Block

VarDecl        ::= "let" IDENTIFIER ( ":" TypeAnnotation )? ( "=" Expr )? ";"
FnDecl         ::= "fn" IDENTIFIER "(" ParamList? ")" ( "->" TypeAnnotation )? Block
StructDecl     ::= "struct" IDENTIFIER "{" ( StructField ( "," StructField )* ","? )? "}"
StructField    ::= IDENTIFIER ":" TypeAnnotation
ImportStmt     ::= "import" ( STRING_LIT | IDENTIFIER ) ";"

IfStmt         ::= "if" "(" Expr ")" Block ( "else" ( IfStmt | Block ) )?
WhileStmt      ::= "while" "(" Expr ")" Block
ForStmt        ::= "for" "(" ( VarDecl | ExprStmt | ";" ) Expr? ";" Expr? ")" Block
ReturnStmt     ::= "return" Expr? ";"
BreakStmt      ::= "break" ";"
ContinueStmt   ::= "continue" ";"
ExprStmt       ::= Expr ";"
Block          ::= "{" Statement* "}"

ParamList      ::= Parameter ( "," Parameter )*
Parameter      ::= IDENTIFIER ( ":" TypeAnnotation )?

TypeAnnotation ::= "int" | "float" | "bool" | "string" | "fn" | "[" TypeAnnotation "]" | IDENTIFIER

Expr           ::= Assignment
Assignment     ::= ( Primary "." IDENTIFIER "=" Expr )
                 | ( Primary "[" Expr "]" "=" Expr )
                 | ( IDENTIFIER "=" Expr )
                 | LogicalOr

LogicalOr      ::= LogicalAnd ( "||" LogicalAnd )*
LogicalAnd     ::= Equality ( "&&" Equality )*
Equality       ::= Relational ( ( "==" | "!=" ) Relational )*
Relational     ::= Additive ( ( "<" | "<=" | ">" | ">=" ) Additive )*
Additive       ::= Multiplicative ( ( "+" | "-" ) Multiplicative )*
Multiplicative ::= Unary ( ( "*" | "/" | "%" ) Unary )*
Unary          ::= ( "!" | "-" ) Unary | Call

Call           ::= Primary ( "(" ArgList? ")" | "." IDENTIFIER | "[" Expr "]" )*
ArgList        ::= Expr ( "," Expr )*

Primary        ::= INT_LIT
                 | FLOAT_LIT
                 | STRING_LIT
                 | "true" | "false" | "nil"
                 | IDENTIFIER
                 | "(" Expr ")"
                 | "[" ( Expr ( "," Expr )* ","? )? "]"
                 | StructLiteral
                 | LambdaExpr
                 | MatchExpr

StructLiteral  ::= IDENTIFIER "{" ( FieldInit ( "," FieldInit )* ","? )? "}"
FieldInit      ::= IDENTIFIER ":" Expr

LambdaExpr     ::= "fn" "(" ParamList? ")" ( "->" TypeAnnotation )? Block

MatchExpr      ::= "match" Expr "{" ( MatchArm ( "," MatchArm )* ","? )? "}"
MatchArm       ::= Pattern ( "if" Expr )? "=>" Expr
Pattern        ::= LiteralPattern | VariablePattern | WildcardPattern
LiteralPattern ::= INT_LIT | FLOAT_LIT | STRING_LIT | "true" | "false" | "nil"
VariablePattern::= IDENTIFIER
WildcardPattern::= "_"
```

---

## 4. Operator Precedence & Associativity

| Precedence | Operator | Description | Associativity |
| :---: | :--- | :--- | :---: |
| **1 (Lowest)** | `=` | Variable / Field / Index Assignment | Right-to-Left |
| **2** | `\|\|` | Logical OR (Short-Circuit) | Left-to-Right |
| **3** | `&&` | Logical AND (Short-Circuit) | Left-to-Right |
| **4** | `==`, `!=` | Value Equality / Inequality | Left-to-Right |
| **5** | `<`, `<=`, `>`, `>=` | Relational Ordering | Left-to-Right |
| **6** | `+`, `-` | Addition, Subtraction, String Concatenation | Left-to-Right |
| **7** | `*`, `/`, `%` | Multiplication, Division, Modulo | Left-to-Right |
| **8** | `!`, `-` (unary) | Logical NOT, Arithmetic Negation | Right-to-Left |
| **9 (Highest)**| `()`, `[]`, `.field` | Function Invocation, Indexing, Member Access | Left-to-Right |

---

## 5. Type System & Operational Semantics

Fresh uses strong static typing with local type inference:

- **Type Promotion**: In binary numeric expressions combining `int` and `float`, the `int` operand is automatically widened to `float`.
- **String Concatenation**: The `+` operator over two `string` operands creates a new string containing their concatenation.
- **Truthiness**: Only boolean `false` and `nil` evaluate to falsey in boolean conditions (`if`, `while`, `&&`, `||`, guards). All other values are truthy.
- **Closures & Upvalues**: Functions capturing local variables from an enclosing activation frame create heap-allocated upvalues that outlive the enclosing frame's termination.
- **Memory Reclamation**: Managed automatically via mark-and-sweep garbage collection tracing all call frames, operand stacks, globals, and upvalue chains.

---

## 6. Standard Library Builtins

| Signature | Description |
| :--- | :--- |
| `println(val: any) -> nil` | Prints string representation of value to stdout with newline. |
| `print(val: any) -> nil` | Prints string representation of value to stdout without newline. |
| `to_string(val: any) -> string` | Converts any value to its canonical string form. |
| `type(val: any) -> string` | Returns the runtime type name (`"int"`, `"float"`, `"string"`, `"bool"`). |
| `len(arr: [T] \| str: string) -> int` | Returns array element count or string length. |
| `push(arr: [T], item: T) -> nil` | Appends element to dynamic array. |
| `pop(arr: [T]) -> T` | Removes and returns last element from dynamic array. |
| `abs(x: int \| float) -> int \| float` | Absolute value of number. |
| `sqrt(x: float) -> float` | Square root of float. |
| `pow(base: float, exp: float) -> float` | Power / exponentiation. |
| `min(a: int \| float, b: int \| float)` | Minimum of two numbers. |
| `max(a: int \| float, b: int \| float)` | Maximum of two numbers. |
| `floor(x: float) -> float` | Largest integer value less than or equal to `x`. |
| `ceil(x: float) -> float` | Smallest integer value greater than or equal to `x`. |
| `round(x: float) -> float` | Float rounded to nearest integer value. |
| `clock() -> float` | High-resolution monotonic timestamp in seconds. |
| `write_file(path: string, text: string) -> nil` | Writes UTF-8 text to disk file. |
| `read_file(path: string) -> string` | Reads text file content as string. |
| `file_exists(path: string) -> bool` | Checks whether file exists on disk. |
