# 📜 The Fresh Language Specification (v0.1.0)
## Normative Grammar, Type System, and Runtime Semantics

---

## 1. Introduction & Conformance

This document is the official, normative specification for the **Fresh Programming Language** (version 0.1.0). A conforming Fresh implementation must adhere to all lexical, syntactic, semantic, and runtime rules defined herein.

### Conformance Classes
- **Conforming Compiler**: Translates valid Fresh source into bytecode or native code conforming to Section 3 and Section 4.
- **Conforming Virtual Machine**: Executes bytecode instructions maintaining memory safety, garbage collection invariants, and call frame semantics described in Section 6.
- **Conforming Native Backend**: Translates conforming AST nodes to target code (such as C99) with 1:1 observable behavioral parity with the VM.

---

## 2. Lexical Grammar

### 2.1 Source Encoding
Fresh source code is a stream of Unicode code points encoded in UTF-8. Non-UTF-8 byte sequences must be rejected at lexical analysis time with diagnostic `[E1001]`.

### 2.2 Whitespace & Comments
- **Whitespace**: ASCII space (`0x20`), horizontal tab (`0x09`), newline (`0x0A`), and carriage return (`0x0D`) separate tokens and are otherwise discarded.
- **Line Comments**: Begin with `//` and extend to the end of the line.
- **Block Comments**: Begin with `/*` and terminate with `*/`. Block comments may be arbitrarily nested.

### 2.3 Reserved Keywords
The following tokens are reserved and cannot be used as identifiers:
```text
let      fn       struct   import   if       else     while    for
break    continue return   match    true     false    nil
```

### 2.4 Identifiers
Identifiers name variables, functions, types, and struct fields:
```regex
[a-zA-Z_][a-zA-Z0-9_]*
```

### 2.5 Literals
- **Integer**: Sequence of decimal digits `[0-9]+` representing signed 64-bit integers.
- **Float**: Sequence of decimal digits with a radix point `[0-9]+\.[0-9]+` conforming to IEEE 754 double precision.
- **Boolean**: `true` and `false`.
- **Nil**: `nil`.
- **String**: Enclosed within double quotes `"..."`. The following escape sequences must be supported:
  - `\n` — Line feed (U+000A)
  - `\t` — Horizontal tab (U+0009)
  - `\"` — Double quotation mark (U+0022)
  - `\\` — Reverse solidus (U+005C)
  - `\0` — Null character (U+0000)

### 2.6 Operators and Delimiters
```text
+   -   *   /   %   =   ==  !=  <   <=  >   >=  &&  ||  !
(   )   [   ]   {   }   ,   :   ;   .   ->  =>
```

---

## 3. Syntactic Grammar (EBNF)

```ebnf
Program        ::= Declaration* EOF ;

Declaration    ::= VarDecl
                 | FnDecl
                 | StructDecl
                 | ImportDecl
                 | Statement ;

VarDecl        ::= "let" IDENTIFIER ( ":" Type )? ( "=" Expression )? ";" ;

FnDecl         ::= "fn" IDENTIFIER "(" ParameterList? ")" ( "->" Type )? BlockStmt ;

ParameterList  ::= Parameter ( "," Parameter )* ;
Parameter      ::= IDENTIFIER ":" Type ;

StructDecl     ::= "struct" IDENTIFIER "{" ( StructField ( "," StructField )* ","? )? "}" ;
StructField    ::= IDENTIFIER ":" Type ;

ImportDecl     ::= "import" STRING_LITERAL ";" ;

Statement      ::= BlockStmt
                 | ExprStmt
                 | IfStmt
                 | WhileStmt
                 | ForStmt
                 | ReturnStmt
                 | BreakStmt
                 | ContinueStmt ;

BlockStmt      ::= "{" Declaration* "}" ;
ExprStmt       ::= Expression ";" ;
IfStmt         ::= "if" "(" Expression ")" Statement ( "else" Statement )? ;
WhileStmt      ::= "while" "(" Expression ")" Statement ;
ForStmt        ::= "for" "(" ( VarDecl | ExprStmt | ";" ) Expression? ";" Expression? ")" Statement ;
ReturnStmt     ::= "return" Expression? ";" ;
BreakStmt      ::= "break" ";" ;
ContinueStmt   ::= "continue" ";" ;

Expression     ::= Assignment ;
Assignment     ::= ( Call "." IDENTIFIER "=" Expression )
                 | ( Call "[" Expression "]" "=" Expression )
                 | ( IDENTIFIER "=" Expression )
                 | LogicalOr ;

LogicalOr      ::= LogicalAnd ( "||" LogicalAnd )* ;
LogicalAnd     ::= Equality ( "&&" Equality )* ;
Equality       ::= Relational ( ( "==" | "!=" ) Relational )* ;
Relational     ::= Additive ( ( "<" | "<=" | ">" | ">=" ) Additive )* ;
Additive       ::= Multiplicative ( ( "+" | "-" ) Multiplicative )* ;
Multiplicative ::= Unary ( ( "*" | "/" | "%" ) Unary )* ;
Unary          ::= ( "!" | "-" ) Unary | Call ;

Call           ::= Primary ( "(" ArgumentList? ")"
                           | "." IDENTIFIER
                           | "[" Expression "]" )* ;

ArgumentList   ::= Expression ( "," Expression )* ;

Primary        ::= IDENTIFIER
                 | NUMBER
                 | STRING
                 | "true"
                 | "false"
                 | "nil"
                 | "(" Expression ")"
                 | ArrayLiteral
                 | MatchExpr ;

ArrayLiteral   ::= "[" ( Expression ( "," Expression )* ","? )? "]" ;

MatchExpr      ::= "match" Expression "{" MatchArm* "}" ;
MatchArm       ::= MatchPattern ( "if" Expression )? "=>" ( Statement | Expression ","? ) ;
MatchPattern   ::= IDENTIFIER | NUMBER | STRING | "true" | "false" | "nil" | "_" ;

Type           ::= "int" | "float" | "bool" | "string" | "nil" | "fn"
                 | "[" Type "]"
                 | IDENTIFIER ;
```

---

## 4. Type System & Static Semantics

### 4.1 Primitive Types
- `int`: Signed 64-bit integer.
- `float`: IEEE 754 64-bit double precision float.
- `bool`: Truth values `true` or `false`.
- `string`: Immutable UTF-8 byte sequences.
- `nil`: Unit type representing absence of value.

### 4.2 Composite & Compound Types
- **Array (`[T]`)**: Dynamically-sized homogenous sequence of elements of type `T`.
- **Struct**: User-defined record type containing named, strongly-typed fields.
- **Function (`fn`)**: First-class callable entity accepting typed parameters and returning a typed result.

### 4.3 Type Inference
Fresh supports local variable type inference on `let` declarations:
- If a type annotation `: T` is omitted, the variable's type is inferred from the initializing expression.
- Variables declared without an initializer default to type `nil` or must provide an explicit type annotation.

### 4.4 Static Type Checking Rules
1. **Arithmetic Operators (`+`, `-`, `*`, `/`, `%`)**:
   - `int (+|-|*|/|%) int -> int`
   - `float (+|-|*|/) float -> float`
   - String concatenation: `string + string -> string`
   - Mixing `int` and `float` without explicit conversion is rejected with `[E3001]`.
2. **Comparison Operators (`<`, `<=`, `>`, `>=`)**:
   - Permitted between operand pairs of type `int` or `float`. Result is `bool`.
3. **Equality Operators (`==`, `!=`)**:
   - Valid between operands of identical types. Comparing mismatched types is a static error.
4. **Logical Operators (`&&`, `||`, `!`)**:
   - Operands must be strictly of type `bool`. No implicit truthiness coercion exists for numbers or strings.

---

## 5. Functions, Closures, and Upvalues

### 5.1 First-Class Functions
Functions in Fresh are first-class values. They may be stored in variables, passed into other functions as arguments, and returned from functions.

### 5.2 Lexical Closures
An inner function that references a variable declared in an enclosing function captures that variable as an **upvalue**:
- Captured variables survive the termination of the enclosing function's call frame (open upvalues are closed onto the heap upon frame exit).
- Multiple closures referencing the same variable share the identical storage location; mutations in one closure are immediately visible to the other.

---

## 6. Virtual Machine & Memory Model

### 6.1 Call Frame & Operand Stack
- Execution proceeds on a stack-based Virtual Machine.
- Local variables and intermediate expression values occupy stack slots within the active `CallFrame`.
- When a function call occurs, a new `CallFrame` is pushed with base slot pointer `ip`, return address, and parameter slots.

### 6.2 Garbage Collection Invariants
Fresh manages dynamically allocated memory (strings, arrays, structs, closures, upvalues) through a precise **Mark-and-Sweep Garbage Collector**:
- **Roots**: The active VM operand stack, all active `CallFrame`s, global variables table, and open upvalues list.
- **Mark Phase**: Traverses all reachable objects starting from the roots, setting their `is_marked` flag to true.
- **Sweep Phase**: Reclaims all heap allocations where `is_marked == false` and resets marked flags on surviving objects.
- Conforming runtimes must support a stress mode (`--gc-stress`) where a full collection cycle is triggered on every allocation.

---

## 7. Modules & Imports

1. Modules are addressed via relative string paths in `import` statements:
   ```fresh
   import "./math_utils.fresh";
   ```
2. Each imported module is evaluated exactly once and cached in a module registry.
3. **Cycle Detection**: The compiler constructs a directed module dependency graph before execution. Circular dependencies (e.g., `A -> B -> A`) must be statically detected and aborted with diagnostic `[E4001]`.

---

## 8. Diagnostic Format Specification

All compiler and runtime errors must follow the standard diagnostic schema:
```text
error[<Category>]: <Description> [<Code>]
  --> <file>:<line>:<column>
   |
<line> | <source line>
   | <underline caret(s)>
```
- Codes: `[E1001]` (Scanner), `[E2001]` (Parser), `[E3001]` (Type Checker), `[E4001]` (Modules), `[E5001]` (Runtime).
