"""Dedicated OOP Unit and Integration Test Suite for Fresh.

Covers:
- Class declarations, fields, constructors (constructor and init)
- Instance creation, field mutation, and method calls
- Inheritance (both ':' and 'extends' syntax)
- Constructor chaining via super.init / super(...)
- Method overriding and super method calls
- Multi-level inheritance hierarchy
- Subtype compatibility and static type checking
- Static diagnostic error checking (this outside class, super without parent, undefined super methods, self-inheritance)
"""

import pytest

from fresh.common.errors import (
    FreshError,
    FreshNameError,
    FreshSyntaxError,
    FreshTypeError,
)
from fresh.pipeline import run_source


# ── 1. Basic Classes & Instantiation ──────────────────────────────────────────


def test_basic_class_instantiation(run_fresh):
    out = run_fresh("""
    class Point {
        var x;
        var y;

        init(x, y) {
            this.x = x;
            this.y = y;
        }

        fn get_x() {
            return this.x;
        }

        fn get_y() {
            return this.y;
        }
    }

    let p = Point(10, 20);
    println(to_string(p.get_x()) + " " + to_string(p.get_y()));
    """)
    assert out.strip() == "10 20"


def test_class_constructor_keyword(run_fresh):
    out = run_fresh("""
    class Greeter {
        var prefix;

        constructor(prefix) {
            this.prefix = prefix;
        }

        fn greet(name) {
            return this.prefix + " " + name + "!";
        }
    }

    let g = Greeter("Hello");
    println(g.greet("World"));
    """)
    assert out.strip() == "Hello World!"


def test_instance_field_mutation(run_fresh):
    out = run_fresh("""
    class Counter {
        var count;

        init() {
            this.count = 0;
        }

        fn increment() {
            this.count = this.count + 1;
        }

        fn get() {
            return this.count;
        }
    }

    let c = Counter();
    c.increment();
    c.increment();
    c.increment();
    println(to_string(c.get()));
    """)
    assert out.strip() == "3"


def test_multiple_independent_instances(run_fresh):
    out = run_fresh("""
    class Box {
        var val;
        init(v) {
            this.val = v;
        }
        fn get() {
            return this.val;
        }
    }

    let b1 = Box(100);
    let b2 = Box(200);
    println(to_string(b1.get()) + " and " + to_string(b2.get()));
    """)
    assert out.strip() == "100 and 200"


# ── 2. Inheritance & Method Resolution ────────────────────────────────────────


def test_single_inheritance_colon_syntax(run_fresh):
    out = run_fresh("""
    class Animal {
        var name;
        init(name) {
            this.name = name;
        }
        fn speak() {
            return this.name + " speaks";
        }
    }

    class Cat : Animal {
        init(name) {
            super.init(name);
        }
    }

    let c = Cat("Luna");
    println(c.speak());
    """)
    assert out.strip() == "Luna speaks"


def test_single_inheritance_extends_syntax(run_fresh):
    out = run_fresh("""
    class Vehicle {
        var speed;
        init(s) {
            this.speed = s;
        }
        fn get_speed() {
            return this.speed;
        }
    }

    class Bicycle extends Vehicle {
        init(s) {
            super.init(s);
        }
    }

    let b = Bicycle(25);
    println(to_string(b.get_speed()));
    """)
    assert out.strip() == "25"


def test_method_overriding(run_fresh):
    out = run_fresh("""
    class Base {
        fn message() {
            return "Base message";
        }
    }

    class Derived : Base {
        fn message() {
            return "Derived message";
        }
    }

    let b = Base();
    let d = Derived();
    println(b.message());
    println(d.message());
    """)
    lines = out.strip().splitlines()
    assert lines == ["Base message", "Derived message"]


def test_super_method_invocation(run_fresh):
    out = run_fresh("""
    class Parent {
        fn greet() {
            return "Hello from Parent";
        }
    }

    class Child : Parent {
        fn greet() {
            return super.greet() + " and Child";
        }
    }

    let c = Child();
    println(c.greet());
    """)
    assert out.strip() == "Hello from Parent and Child"


def test_multi_level_inheritance(run_fresh):
    out = run_fresh("""
    class A {
        fn tag() {
            return "A";
        }
    }

    class B : A {
        fn tag() {
            return super.tag() + " -> B";
        }
    }

    class C : B {
        fn tag() {
            return super.tag() + " -> C";
        }
    }

    let obj = C();
    println(obj.tag());
    """)
    assert out.strip() == "A -> B -> C"


# ── 3. Type Checking & Subtyping ──────────────────────────────────────────────


def test_subclass_polymorphic_assignment(run_fresh):
    out = run_fresh("""
    class Shape {
        fn area() -> float {
            return 0.0;
        }
    }

    class Square : Shape {
        var side: float;
        init(s: float) {
            this.side = s;
        }
        fn area() -> float {
            return this.side * this.side;
        }
    }

    let s: Shape = Square(4.0);
    println(to_string(s.area()));
    """)
    assert out.strip() == "16.0"


def test_type_error_incompatible_class_assignment():
    source = """
    class Cat {
        var name: string;
        init(n: string) { this.name = n; }
    }
    class Dog {
        var name: string;
        init(n: string) { this.name = n; }
    }
    let c: Cat = Dog("Rover");
    """
    with pytest.raises(FreshTypeError) as excinfo:
        run_source(source, filename="test_err.fresh")
    assert "Cannot initialize variable 'c' of type 'Cat' with value of type 'Dog'" in str(excinfo.value)


def test_type_error_constructor_argument_count():
    source = """
    class Item {
        var id: int;
        init(id: int) {
            this.id = id;
        }
    }
    let i = Item(1, 2, 3);
    """
    with pytest.raises(FreshTypeError) as excinfo:
        run_source(source, filename="test_err.fresh")
    assert "Constructor for 'Item' expected 1 arguments but got 3" in str(excinfo.value)


# ── 4. Diagnostics & Semantic Errors ──────────────────────────────────────────


def test_error_this_outside_class():
    source = """
    fn standalone() {
        print this.x;
    }
    """
    with pytest.raises(FreshError):
        run_source(source, filename="test_err.fresh")


def test_error_super_outside_class():
    source = """
    fn standalone() {
        super.init();
    }
    """
    with pytest.raises(FreshError):
        run_source(source, filename="test_err.fresh")


def test_error_super_in_root_class():
    source = """
    class Root {
        fn test() {
            super.test();
        }
    }
    """
    with pytest.raises(FreshError):
        run_source(source, filename="test_err.fresh")


def test_error_self_inheritance():
    source = """
    class Cyclic : Cyclic {
    }
    """
    with pytest.raises((FreshSyntaxError, FreshError)):
        run_source(source, filename="test_err.fresh")


def test_error_undefined_parent_class():
    source = """
    class Child : NonExistentParent {
    }
    """
    with pytest.raises((FreshNameError, FreshError)):
        run_source(source, filename="test_err.fresh")


def test_error_super_undefined_method():
    source = """
    class Parent {
        init() {}
    }
    class Child : Parent {
        fn test() {
            super.does_not_exist();
        }
    }
    """
    with pytest.raises(FreshTypeError) as excinfo:
        run_source(source, filename="test_err.fresh")
    assert "Superclass 'Parent' has no method 'does_not_exist'" in str(excinfo.value)
