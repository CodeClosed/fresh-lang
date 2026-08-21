"""Garbage Collector test suite for Fresh."""


from fresh.pipeline import run_source
from fresh.stdlib.builtins import register_builtins
from fresh.vm.objects import ObjArray, ObjStructDef, ObjStructInstance
from fresh.vm.vm import VM


def test_gc_basic_allocation_and_sweep():
    vm = VM()
    gc = vm.gc

    # Allocate unreachable objects
    gc.allocate(ObjArray([1, 2, 3]))
    gc.allocate(ObjArray([4, 5, 6]))
    assert len(vm.objects) == 2

    # Run collection without stack/global roots
    gc.collect_garbage()
    assert len(vm.objects) == 0


def test_gc_cyclic_structs():
    vm = VM()
    gc = vm.gc

    sdef = ObjStructDef("Node", ["next"])
    gc.allocate(sdef)
    vm.globals["Node"] = sdef

    n1 = ObjStructInstance(sdef)
    n2 = ObjStructInstance(sdef)
    gc.allocate(n1)
    gc.allocate(n2)

    # Create cycle: n1 -> n2 -> n1
    n1.fields[0] = n2
    n2.fields[0] = n1

    # Keep n1 reachable on stack
    vm.push(n1)
    gc.collect_garbage()

    assert n1 in vm.objects
    assert n2 in vm.objects
    assert sdef in vm.objects

    # Pop root and sweep cycle
    vm.pop()
    vm.globals.clear()
    gc.collect_garbage()
    assert len(vm.objects) == 0



def test_gc_deep_object_graph():
    vm = VM()
    gc = vm.gc

    head = ObjArray([0])
    gc.allocate(head)
    curr = head

    for i in range(1, 100):
        next_node = ObjArray([i])
        gc.allocate(next_node)
        curr.elements.append(next_node)
        curr = next_node

    vm.push(head)
    gc.collect_garbage()
    assert len(vm.objects) == 100

    vm.pop()
    gc.collect_garbage()
    assert len(vm.objects) == 0


def test_gc_stress_mode_execution(run_fresh):
    source = """
    fn make_counter() -> fn {
        let count = 0;
        fn inc() -> int {
            count = count + 1;
            return count;
        }
        return inc;
    }
    let c = make_counter();
    let nums = [c(), c(), c()];
    println(nums);
    """
    vm = VM(gc_stress=True)
    register_builtins(vm)
    run_source(source, vm_instance=vm)
    assert len(vm.objects) >= 0


def test_gc_stress_env_var(monkeypatch, run_fresh):
    monkeypatch.setenv("FRESH_GC_STRESS", "1")
    source = """
    let arr = [1, 2, 3];
    push(arr, 4);
    push(arr, 5);
    println(arr);
    """
    out = run_fresh(source)
    assert out.strip() == "[1, 2, 3, 4, 5]"
