# 🍃 Fresh

### A modern, lightweight programming language built from scratch

**Fresh** is a programming language and compiler project designed with a simple, readable syntax while providing the foundations of a complete compiled language.

The project includes its own **lexer, parser, AST, semantic analysis, type checker, bytecode compiler, virtual machine, formatter, and C transpiler**.

---

## 🚀 Project Status

Fresh currently supports several core language features, including:

- Variables and expressions
- Functions
- Structs
- Type checking
- Bytecode compilation
- Virtual machine execution
- C transpilation
- Code formatting
- AST generation
- Bytecode disassembly

### 🆕 Object-Oriented Programming

Fresh is being extended with **C++/Java-style Object-Oriented Programming**.

The OOP system introduces:

- Classes
- Fields
- Methods
- Constructors
- `this`
- Single inheritance
- `super`
- Method overriding
- Class instances
- Inherited methods

Existing `struct` declarations remain fully supported and unchanged.

---

# ✨ OOP Syntax

Fresh uses a clean class syntax inspired by C++ and Java.

## 🐾 Basic Class

```fresh
class Animal {
    name: string,
    age: int

    constructor(name: string, age: int) {
        this.name = name;
        this.age = age;
    }

    fn speak() -> string {
        return this.name + " makes a sound";
    }

    fn get_info() -> string {
        return this.name + " (age " + to_string(this.age) + ")";
    }
}
```

---

## 🐕 Inheritance

Fresh supports **single inheritance** using `:`.

```fresh
class Dog : Animal {
    breed: string

    constructor(name: string, age: int, breed: string) {
        super(name, age);
        this.breed = breed;
    }

    fn speak() -> string {
        return this.name + " says Woof!";
    }

    fn fetch(item: string) -> string {
        return this.name + " fetches " + item;
    }
}
```

---

## ▶️ Using Classes

Classes can be instantiated using the existing function-call style:

```fresh
let dog = Dog("Rex", 5, "German Shepherd");

println(dog.speak());
println(dog.get_info());
println(dog.fetch("ball"));
```

Output:

```text
Rex says Woof!
Rex (age 5)
Rex fetches ball
```

The derived `Dog` class overrides `speak()` while still inheriting `get_info()` from `Animal`.

---

# 🧩 OOP Design

The proposed OOP system follows these design decisions:

| Feature            | Fresh Syntax                        |
| ------------------ | ----------------------------------- |
| Class              | `class Animal { ... }`              |
| Field              | `name: string`                      |
| Method             | `fn speak() -> string { ... }`      |
| Constructor        | `constructor(...) { ... }`          |
| Instance access    | `this.name`                         |
| Inheritance        | `class Dog : Animal`                |
| Parent constructor | `super(name, age)`                  |
| Method overriding  | Define the same method in the child |
| Object creation    | `Dog(...)`                          |

The syntax intentionally stays consistent with Fresh's existing style while introducing familiar object-oriented concepts.

---

# 🏗️ Compiler Architecture

Adding OOP affects every major stage of the Fresh compiler pipeline.

```text
                 Fresh Source Code
                        │
                        ▼
                  ┌───────────┐
                  │   Lexer   │
                  └─────┬─────┘
                        │
                        ▼
                  ┌───────────┐
                  │   Parser  │
                  └─────┬─────┘
                        │
                        ▼
                     AST
                        │
             ┌──────────┴──────────┐
             ▼                     ▼
       Semantic Analysis       Type Checker
             │                     │
             └──────────┬──────────┘
                        ▼
                Bytecode Compiler
                        │
                        ▼
                   Bytecode
                        │
                        ▼
                Virtual Machine
                        │
                        ▼
                    Program
```

---

# 🔧 Implementation Plan

## 1. Lexer

### `tokens.py`

Add the following keyword tokens:

```text
CLASS
CONSTRUCTOR
THIS
SUPER
```

They are also added to the `KEYWORDS` lookup table.

### `scanner.py`

No major changes are required because the existing keyword scanning mechanism automatically recognizes the new keywords.

---

# 🧱 Type System

### `types.py`

Introduce a new `FreshClass` type containing:

```python
@dataclass
class FreshClass(FreshType):
    name: str = ""
    fields: dict[str, FreshType] = field(default_factory=dict)
    methods: dict[str, FreshFunction] = field(default_factory=dict)
    parent: FreshClass | None = None
```

The `parent` reference allows field and method lookup to walk through the inheritance chain.

---

# 🌳 AST

The following AST nodes are introduced:

### `ClassDeclStmt`

Represents a class declaration.

### `ThisExpr`

Represents the `this` keyword inside a class.

### `SuperExpr`

Represents access to the parent class.

### `ConstructorDecl`

Represents a class constructor.

Example structure:

```python
@dataclass(slots=True)
class ConstructorDecl:
    keyword: Token
    params: list[Parameter]
    body: list[Stmt]
    super_args: list[Expr] | None = None
```

The AST printer is also updated to display the new OOP nodes.

---

# 🧠 Parser

### `parser.py`

The parser will recognize:

```fresh
class Animal {
    ...
}
```

and route class declarations through:

```text
_declaration()
    └── _class_declaration()
```

The parser also adds support for:

```fresh
this.name
```

and:

```fresh
super.speak()
```

as well as:

```fresh
super(name, age)
```

inside constructors.

---

# 🔍 Semantic Analysis

### `resolver.py`

The resolver will:

- Pre-declare class names
- Create a class scope
- Declare `this`
- Resolve constructors
- Resolve methods
- Track the current class context
- Validate `this`
- Validate `super`
- Prevent class-only features from being used outside classes

For example:

```fresh
this.name
```

is only valid within a class method or constructor.

---

# 🧪 Type Checking

### `type_checker.py`

The type checker will:

- Register class types
- Check field types
- Check method signatures
- Check constructor parameters
- Validate return types
- Resolve `this`
- Resolve `super`
- Validate inherited methods
- Check method calls
- Support derived-to-parent type compatibility

For example:

```fresh
class Dog : Animal {
    ...
}
```

allows a `Dog` instance to be used where an `Animal` is expected.

---

# ⚙️ Bytecode

New bytecode operations are introduced for class support:

| Opcode            | Purpose                     |
| ----------------- | --------------------------- |
| `OP_CLASS_DEF`    | Define a class              |
| `OP_METHOD`       | Attach a method to a class  |
| `OP_INHERIT`      | Establish inheritance       |
| `OP_GET_THIS`     | Access the current instance |
| `OP_SUPER_INVOKE` | Invoke a superclass method  |

These operations allow the VM to efficiently represent classes and method calls.

---

# 🖥️ Virtual Machine

### `objects.py`

Fresh introduces runtime objects for classes and instances:

```text
ObjClass
ObjInstance
```

`ObjClass` contains:

- Class name
- Fields
- Methods
- Parent class

`ObjInstance` contains:

- Reference to its class
- Instance field values

---

## Method Lookup

When executing:

```fresh
dog.speak()
```

the VM searches the object's class for `speak()`.

If the method is not found directly on the class, inherited methods can be resolved through the parent class.

This allows:

```fresh
dog.get_info()
```

to call a method inherited from `Animal`.

---

# 🔄 Method Overriding

A child class can define a method with the same name as its parent:

```fresh
class Animal {
    fn speak() -> string {
        return "Animal sound";
    }
}

class Dog : Animal {
    fn speak() -> string {
        return "Woof!";
    }
}
```

Calling:

```fresh
dog.speak()
```

uses the `Dog` implementation.

---

# 🧰 Tooling

OOP support will also be integrated into Fresh's development tools.

### Disassembler

`disassembler.py` will support:

```text
OP_CLASS_DEF
OP_METHOD
OP_INHERIT
OP_GET_THIS
OP_SUPER_INVOKE
```

### Formatter

`formatter.py` will format:

- Class declarations
- Fields
- Constructors
- Methods
- `this`
- `super`

### C Transpiler

`c_transpiler.py` will provide basic class translation using C structures.

Conceptually:

```text
Fresh Class
     │
     ▼
C typedef struct
     │
     ├── Fields
     │
     └── Method functions
```

Inheritance can be represented through structure embedding.

---

# 📚 Documentation

The OOP documentation will be available in:

```text
LANGUAGE_GUIDE.md
```

A dedicated OOP section will cover:

- Classes
- Fields
- Methods
- Constructors
- `this`
- Inheritance
- `super`
- Method overriding
- Complete examples

---

# 📁 Project Structure

```text
fresh-lang-main/
│
├── src/
│   ├── tokens.py
│   ├── scanner.py
│   ├── ast.py
│   ├── parser.py
│   ├── resolver.py
│   ├── types.py
│   ├── type_checker.py
│   ├── compiler.py
│   ├── objects.py
│   ├── opcodes.py
│   ├── vm.py
│   ├── value.py
│   ├── disassembler.py
│   ├── formatter.py
│   └── c_transpiler.py
│
├── examples/
│   └── oop_demo.fresh
│
├── tests/
│
├── docs/
│
├── LANGUAGE_GUIDE.md
├── all_features.fresh
└── README.md
```

---

# 🧪 Verification

All existing functionality should continue to work after the OOP implementation.

Run the complete test suite:

```bash
python -m pytest tests/ -v
```

OOP functionality can then be manually verified with:

```bash
fresh run examples/oop_demo.fresh
```

AST output:

```bash
fresh run examples/oop_demo.fresh --dump-ast
```

Bytecode:

```bash
fresh run examples/oop_demo.fresh --disassemble
```

Type checking:

```bash
fresh check examples/oop_demo.fresh
```

Formatter:

```bash
fresh fmt examples/oop_demo.fresh --check
```

---

# ❓ Design Questions

The following features can be considered for future iterations:

### Access Modifiers

Should Fresh eventually support:

```fresh
public
private
protected
```

The initial implementation keeps fields and methods simple without access modifiers.

### `new` Keyword

The current design uses:

```fresh
let dog = Dog(...)
```

rather than:

```fresh
let dog = new Dog(...)
```

This maintains consistency with existing struct instantiation.

### Static Methods

Static methods can be introduced as a future extension:

```fresh
static fn create() -> Animal {
    ...
}
```

---

# 🎯 Goals

The OOP extension aims to make Fresh capable of expressing larger programs while keeping its syntax straightforward.

The implementation focuses on:

- 🧩 Simple class syntax
- 🔗 Single inheritance
- 🏗️ Constructors
- 🎯 Instance methods
- 👤 `this`
- ⬆️ `super`
- 🔄 Method overriding
- 🧠 Static type checking
- ⚡ Bytecode execution
- 🛠️ Integrated compiler tooling

---

# 🌱 Fresh Language

Fresh is being developed as a complete programming-language project, from source code all the way to execution.

```text
Source
  ↓
Lexer
  ↓
Parser
  ↓
AST
  ↓
Semantic Analysis
  ↓
Type Checker
  ↓
Bytecode Compiler
  ↓
Virtual Machine
  ↓
Execution
```

**Fresh is built to keep programming simple, readable, and — well — fresh. 🍃**

---

## 📄 License

See the repository for license information.

---

<p align="center">
  <b>🍃 Fresh Language</b><br>
  A programming language built from the ground up.
</p>
