Add C++ OOP Concepts to Fresh Language
Fresh currently supports struct as flat data records without behavior. This plan adds full C++-style Object-Oriented Programming: classes with methods, constructors, this, single inheritance, and method overriding.

Proposed OOP Syntax for Fresh
fresh

// ── Base class ──────────────────────────────────────────
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
// ── Derived class (single inheritance) ──────────────────
class Dog : Animal {
breed: string
constructor(name: string, age: int, breed: string) {
super(name, age);
this.breed = breed;
}
// Override base method
fn speak() -> string {
return this.name + " says Woof!";
}
fn fetch(item: string) -> string {
return this.name + " fetches " + item;
}
}
// ── Usage ───────────────────────────────────────────────
let dog = Dog("Rex", 5, "German Shepherd");
println(dog.speak()); // Rex says Woof!
println(dog.get_info()); // Rex (age 5) — inherited method
println(dog.fetch("ball")); // Rex fetches ball
User Review Required
IMPORTANT

Syntax Design Decisions — The proposed syntax uses:

class Name { fields, constructor, methods } (C++/Java-style)
constructor(...) instead of **init** or fn Name(...) (explicit, readable)
this.field for instance access (C++/Java convention)
class Child : Parent for inheritance (C++ convention)
super(args) for parent constructor calls
If you prefer different keywords (e.g., new for instantiation, extends instead of :), please let me know.

IMPORTANT

Scope of this change: This adds OOP on top of the existing struct system. Existing struct declarations remain fully supported and unchanged. Classes are a new, richer construct.

Open Questions
Access modifiers? — Should we add public/private field modifiers in this version, or keep it simple with all-public access?
new keyword for instantiation? — Should we require let dog = new Dog(...) or keep the current function-call style let dog = Dog(...)? The plan uses the current style to stay consistent with struct instantiation.
Static methods? — Should we include static fn class methods in this version, or defer to a future iteration?
Proposed Changes
The change touches every layer of the compiler pipeline. Files are grouped by component and ordered dependency-first.

Lexer (Token Definitions & Scanner)
[MODIFY]
tokens.py
Add 4 new keyword tokens:

CLASS — class
CONSTRUCTOR — constructor
THIS — this
SUPER — super
Add them to both the TokenType enum and the KEYWORDS lookup table.

[MODIFY]
scanner.py
No changes needed — the existing identifier/keyword scanning logic automatically picks up new KEYWORDS entries.

Type System
[MODIFY]
types.py
Add FreshClass type:

python

@dataclass
class FreshClass(FreshType):
name: str = ""
fields: dict[str, FreshType] = field(default_factory=dict)
methods: dict[str, FreshFunction] = field(default_factory=dict)
parent: FreshClass | None = None
Includes parent reference for inheritance chain lookups. Field/method resolution walks the chain.

AST Node Definitions
[MODIFY]
ast.py
Add 4 new AST node classes:

Node Family Purpose
ClassDeclStmt Stmt Class declaration with fields, constructor, methods, optional parent
ThisExpr Expr this keyword reference inside methods
SuperExpr Expr super.method() call
ConstructorDecl Helper Constructor parameter list and body
python

@dataclass(slots=True)
class ConstructorDecl:
keyword: Token
params: list[Parameter]
body: list[Stmt]
super_args: list[Expr] | None = None # super(args) call
@dataclass(slots=True)
class ClassDeclStmt(Stmt):
name: Token
parent_name: Token | None
fields: list[StructField]
constructor: ConstructorDecl | None
methods: list[FnDeclStmt]
@dataclass(slots=True)
class ThisExpr(Expr):
keyword: Token
@dataclass(slots=True)
class SuperExpr(Expr):
keyword: Token
method: Token # the method name after super.
Update ASTPrinter to format these new nodes.

Parser
[MODIFY]
parser.py
Declaration routing: Add TokenType.CLASS check in \_declaration() → \_class_declaration().
\_class_declaration(): Parse the full class syntax:
Class name, optional : ParentName
{ body with field declarations, constructor(...), and fn method declarations }
this prefix rule: Map TokenType.THIS → \_this_expr() in the Pratt prefix table.
super prefix rule: Map TokenType.SUPER → \_super_expr() — expects super.method_name or super(args) (in constructors).
Error synchronization: Add TokenType.CLASS to the synchronization set.
Semantic Analysis — Resolver
[MODIFY]
resolver.py
Pre-declare class names in the top-level pass (alongside functions and structs).
Resolve ClassDeclStmt: Open a new scope, declare this, resolve constructor body and method bodies.
Track class context: Add current_class state to validate this/super usage (only legal inside class methods/constructors).
Resolve ThisExpr and SuperExpr: Validate they appear inside a class context.
Semantic Analysis — Type Checker
[MODIFY]
type_checker.py
Register class types: In the pre-pass, build FreshClass objects with field types, method signatures, and parent references.
Check ClassDeclStmt: Validate constructor assignments, method return types, field types.
Check ThisExpr: Return the current class type.
Check SuperExpr: Return the parent class type and validate the method exists on the parent.
Check method calls: On CallExpr where callee is FieldAccessExpr on a class instance, resolve the method signature.
Inheritance compatibility: FreshClass subtypes should be compatible with parent types (\_types_compatible).
Bytecode — Opcodes
[MODIFY]
opcodes.py
Add new opcodes:

Opcode Operands Description
OP_CLASS_DEF name_idx, field_count Define a class (fields + methods)
OP_METHOD name_idx Bind a closure as a method on the class
OP_INHERIT — Copy parent methods into child class
OP_GET_THIS — Push this (slot 0 of current method frame)
OP_SUPER_INVOKE method_name_idx, arg_count Invoke a method on the superclass
Bytecode Compiler
[MODIFY]
compiler.py
Compile ClassDeclStmt:
Emit OP_CLASS_DEF with field names
If parent: emit OP_GET_GLOBAL for parent, OP_INHERIT
Compile constructor as a special function (with this in slot 0)
Compile each method as a closure, emit OP_METHOD to bind it
Define the class name as a global
Compile ThisExpr: Emit OP_GET_LOCAL for slot 0 (this is always slot 0 in methods).
Compile SuperExpr: Emit OP_GET_LOCAL for slot 0 (this) + OP_SUPER_INVOKE.
Handle constructor calls: When OP_CALL targets a class definition, automatically create an instance and invoke the constructor.
Add ClassDeclStmt, ThisExpr, SuperExpr imports.

VM — Object Model
[MODIFY]
objects.py
Add two new object types:

python

class ObjClass(Obj):
"""Runtime class definition with fields, methods, and optional parent."""
name: str
field_names: list[str]
field_indices: dict[str, int]
methods: dict[str, ObjClosure]
parent: ObjClass | None
class ObjInstance(Obj):
"""An instance of a class."""
klass: ObjClass
fields: list[Any]
ObjInstance replaces ObjStructInstance for class-based objects. ObjClass replaces ObjStructDef for class-based definitions. Both support trace_references() for GC.

VM — Execution Engine
[MODIFY]
vm.py
OP_CLASS_DEF handler: Create ObjClass, register it in globals and a new class_defs dict.
OP_METHOD handler: Pop the closure and bind it to the class at TOS.
OP_INHERIT handler: Copy parent methods into child class methods dict.
OP_GET_THIS handler: Push self.stack[frame.stack_base].
OP_SUPER_INVOKE handler: Look up the method in the parent class, create a bound call.
\_call_value extension: When calling an ObjClass, allocate a new ObjInstance, push it, invoke the constructor if present.
OP_GET_FIELD / OP_SET_FIELD extension: Handle ObjInstance in addition to ObjStructInstance. For OP_GET_FIELD, also check methods on the instance's class (bound method lookup).
VM — Value Display
[MODIFY]
value.py
Add formatting for ObjInstance: display as ClassName { field: val, ... }.

Disassembler
[MODIFY]
disassembler.py
Add disassembly for the new opcodes: OP_CLASS_DEF, OP_METHOD, OP_INHERIT, OP_GET_THIS, OP_SUPER_INVOKE.

Code Formatter
[MODIFY]
formatter.py
Add formatting for ClassDeclStmt, ThisExpr, SuperExpr in both statement and expression formatters.

C Transpiler
[MODIFY]
c_transpiler.py
Add basic class transpilation: classes become C typedef struct with method functions taking an explicit self pointer. Inheritance maps to struct embedding.

Documentation & Examples
[MODIFY]
LANGUAGE_GUIDE.md
Add a new section "Classes & Object-Oriented Programming" covering:

Class declarations with fields and methods
Constructors and this
Single inheritance with : Parent and super
Method overriding
Complete examples
[NEW] examples/oop_demo.fresh
A comprehensive demo file exercising all OOP features: classes, constructors, methods, inheritance, method overriding, and polymorphic usage.

[MODIFY]
all_features.fresh
Add an OOP section at the end of the feature showcase.

Verification Plan
Automated Tests
bash

python -m pytest tests/ -v
All existing tests must continue to pass (no regressions to struct, function, or other features).

Manual Verification
Run fresh run examples/oop_demo.fresh — verify class creation, method calls, inheritance, and overriding produce correct output.
Run fresh run all_features.fresh — verify the new OOP section runs.
Run fresh run examples/oop_demo.fresh --dump-ast — verify OOP AST nodes print correctly.
Run fresh run examples/oop_demo.fresh --disassemble — verify OOP bytecode disassembles correctly.
Run fresh check examples/oop_demo.fresh — verify static type checking works for classes.
Run fresh fmt examples/oop_demo.fresh --check — verify the formatter handles class syntax.
