# Fresh project review results

Review performed on 2026-10-14 in the repository at `C:\Users\arkob\compiler\fresh-lang`.

## Environment and repository state

- The `fresh` command is available and executes Fresh programs, but each invocation prints a stale-launcher warning: `Failed to find real location of C:\Users\arkob\AppData\Local\Programs\Python\Python313\python.exe`.
- `python` resolves to the MSYS2 Python at `C:\msys64\ucrt64\bin\python.exe`; it reports `No module named pytest`. The installed `fresh` launcher uses Python 3.13.1, where pytest 8.4.2 is available through `fresh test`.
- `py -3.13 -m pytest -q` cannot run because the Python launcher reports `No installed Python found!`.
- The bundled Codex Python also has no pytest module. No package installation was attempted.
- The working tree already had a user modification to `examples/01_fibonacci.fresh` and an untracked `examples/fib.c` before this review. They were preserved. The modified Fibonacci source prints `Iterative fib(20) = 6765`, although the call is to `fib_recursive`; the result is correct, but the label is inaccurate.

## Test suite

With `TEMP` and `TMP` pointed at a temporary directory inside the workspace, `fresh test tests` completed with **113 passed and 4 failed** (exit 1). The failures are `test_method_overriding`, `test_super_method_invocation`, `test_multi_level_inheritance`, and `test_error_this_outside_class`, all in `tests/test_oop.py`.

The focused `fresh test tests/cli` run passed all **4** CLI tests. The new operator-precedence regression check passed separately. Without the workspace-local temp directory, the CLI tests could not create pytest's temporary files under the sandbox's default temp path. The one-click script sets a local temp path for its focused CLI test step and restores the environment afterward.

## Verified demo programs

Commands were run using the installed `fresh` CLI. Each command exited successfully (0); the launcher warning above appeared before results.

| Example | Command | Observed output / behavior |
|---|---|---|
| Recursion and inferred binding | `fresh run examples/01_fibonacci.fresh` | `--- Fibonacci Benchmarks ---`; `Iterative fib(20) = 6765` |
| Closure capture | `fresh run examples/04_closure_counter.fresh` | A counter: `1, 2, 3`, B counter: `101, 102`, then A: `4`; captures retain independent mutable state |
| Struct and array | `fresh run examples/06_inventory.fresh` | `Item: Iron Sword`; `Total Value: $149.97`; `Inventory size: 3` |
| Broader integration example | `fresh run examples/08_aggressive_suite.fresh` | Printed success markers for arithmetic, logic, loops, closures, higher-order functions, recursion, structs, matrices, arrays, matching, and math; final line: `[SUCCESS] ALL 10 SUBSYSTEMS PASSED AGGRESSIVE SUITE!` |
| OOP | `fresh run examples/oop_demo.fresh` | `<Generic> makes a sound`; `<Rex> barks` |
| Operator precedence | `fresh run examples/07_stress_suite.fresh` | `1 + 2 * 3 = 7`; `(1 + 2) * 3 = 9` after correcting the example's parenthesized expression |
| Algorithms and tooling showcases | Matrix multiply, quicksort, calculator, `demo/quick_demo.fresh`, `all_features.fresh`, and `demo/master_showcase.fresh` | All exited 0 in the one-click script; file-writing showcases ran from its temporary directory |

The current Fibonacci source explicitly types the parameter and return value, while `let r1 = fib_recursive(20);` infers the local binding. It demonstrates local inference, not polymorphic or whole-program inference.

## CLI inspection flags

All four commands completed with exit code 0 using `examples/01_fibonacci.fresh`:

- `fresh run examples/01_fibonacci.fresh --dump-tokens`
- `fresh run examples/01_fibonacci.fresh --dump-ast`
- `fresh run examples/01_fibonacci.fresh --disassemble`
- `fresh run examples/01_fibonacci.fresh --emit-c`

For `--emit-c`, the command emits C source and exits without running the VM program.

## Compile-time diagnostic

A temporary source containing `let x: int = "hello";` was passed to `fresh check`. It exited 1 with `FreshTypeError` and the message `Cannot initialize variable 'x' of type 'int' with value of type 'string'.` The file was deleted afterward. This confirms a real type error is rejected before execution.

## Native build

The documented project workflow was exercised against a temporary project with `fresh.toml` and `src/main.fresh`:

1. `fresh build <temporary-project-path>` exited 0 and created `build/review_demo.exe` using the detected GCC compiler.
2. Running the generated `.exe` exited 0 and printed `Native build works`.

The temporary project and executable were removed after verification. Native compilation is verified on this machine; portability to other host compilers was not tested.

The expanded one-click script now uses `fresh init review_demo --dir <temporary-directory>` before `fresh build`. The generated executable exited 0 and printed `Hello from review_demo!`. A temporary copy of `demo/quick_demo.fresh` passed `fresh fmt` followed by `fresh fmt --check`.

## Performance demonstrations (not GC benchmarks)

Two equivalent workloads were built with `fresh build` and compared with straightforward Python 3.14.7 versions. GCC 16.2.0 was used; compilation was excluded, and no optimization flag was passed to GCC. Five wall-clock runs per executable were timed in PowerShell, including process startup. Both output values were checked in a separate run.

| Workload | Output | Fresh native median | Python median |
|---|---:|---:|---:|
| Sum integers from 0 through 20,000,000 | `200000010000000` | 54.0 ms | 1,532.2 ms |
| Recursive Fibonacci at 32 | `2178309` | 47.5 ms | 405.7 ms |

These are single-machine observations, not portable claims. They demonstrate the speed of the native C build against this Python interpreter on these workloads. They do not measure the Fresh VM's garbage collector and do not compare against C or C++; the native backend uses C allocation/runtime semantics, so these results cannot support a claim that Fresh GC is faster.

The expanded `review_demo.ps1` was run end to end after these additions. It passed the GC stress closure check, both output-equality checks, both native builds, and all prior demonstrations. Timings varied between separate runs, as expected; the script reports fresh five-run medians when executed rather than treating these recorded values as guaranteed.
