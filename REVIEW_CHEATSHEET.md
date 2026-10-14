# Fresh: five-minute review cheatsheet

Run these from the repository root in PowerShell. `fresh` must be available on `PATH`.

For the complete one-click walkthrough, run:

```powershell
.\review_demo.ps1
```

It covers the VM, type errors, closures and GC stress, OOP, algorithms, arrays, structs, pattern matching, math and file I/O, compiler inspection, formatting, project initialization, a focused CLI test run, native build, and two measured native-versus-Python scenarios. It writes temporary files in a generated `.fresh-review-*` directory and removes that directory on completion. The REPL is interactive and is not part of the unattended sequence.

## Exact demonstration sequence

1. Functions, recursion, local type inference:

   ```powershell
   fresh run examples/01_fibonacci.fresh
   ```

   Observed program output:

   ```text
   --- Fibonacci Benchmarks ---
   Iterative fib(20) = 6765
   ```

   The second label is inaccurate in the current working-tree version: the call is recursive. The numeric result was observed directly.

2. Compile-time type rejection (the script generates and removes a temporary invalid file):

   ```powershell
   .\review_demo.ps1
   ```

   Or create a file with `let x: int = "hello";` and run `fresh check FILE`. The verified diagnostic is `Cannot initialize variable 'x' of type 'int' with value of type 'string'.` with exit code 1. The error output is expected for this demonstration.

3. Closures, then structs and arrays:

   ```powershell
   fresh run examples/04_closure_counter.fresh
   fresh run examples/06_inventory.fresh
   ```

   Observed closure sequence: A yields `1, 2, 3`, B yields `101, 102`, and A then yields `4`. Inventory output includes `Iron Sword`, `$149.97`, and size `3`.

4. Inspect compiler representations (each command was verified to exit 0):

   ```powershell
   fresh run examples/01_fibonacci.fresh --dump-tokens
   fresh run examples/01_fibonacci.fresh --dump-ast
   fresh run examples/01_fibonacci.fresh --disassemble
   fresh run examples/01_fibonacci.fresh --emit-c
   ```

5. OOP and remaining language examples:

   ```powershell
   fresh run examples/oop_demo.fresh
   fresh check examples/oop_demo.fresh
   fresh run examples/oop_demo.fresh --dump-ast
   fresh run examples/oop_demo.fresh --disassemble
   fresh run examples/02_matrix_multiply.fresh
   fresh run examples/03_quicksort.fresh
   fresh run examples/05_calculator.fresh
   fresh run examples/07_stress_suite.fresh
   fresh run examples/08_aggressive_suite.fresh
   fresh run demo/quick_demo.fresh
   ```

   The OOP program prints `<Generic> makes a sound` and `<Rex> barks`. The corrected precedence example prints `1 + 2 * 3 = 7` and `(1 + 2) * 3 = 9`. The one-click script runs file-writing showcases from a temporary directory.

6. CLI tooling and native compilation: the script runs `fresh check`, formats and checks a temporary copy, uses `fresh init` to scaffold a project, runs the four CLI tests, then uses `fresh build` and executes the resulting `.exe`. This is the actual package build workflow with a detected GCC compiler. `fresh run` uses the VM.

The complete suite currently has **113 passing tests and four failing OOP tests**. The one-click script runs the verified CLI subset (four passing tests) and does not present the full suite as green.

## Compiler stages

1. **Source:** the `.fresh` text to compile.
2. **Lexer/scanner:** converts characters into tokens such as identifiers, keywords, operators, and literals. `--dump-tokens` displays this stream.
3. **Parser:** consumes tokens and builds the AST, representing expressions and statements as structured nodes. `--dump-ast` displays it.
4. **Module loading:** resolves imports and checks module cycles before semantic analysis.
5. **Resolver:** tracks lexical scopes, declarations, and name references; reports unresolved names and scope errors.
6. **Type checker and local inferrer:** checks type constraints and records types for expressions and bindings. A mismatch is reported before code runs.
7. **Bytecode compiler:** lowers the checked AST to VM instructions and constants.
8. **Optimizer:** applies bytecode-level simplifications, including constant folding and peephole transformations.
9. **Execution backend:** the VM interprets the optimized bytecode, or the C transpiler emits C from the AST for a host C compiler.

The run pipeline and the native C path are related through parsing and semantic checks, but they do not execute the same representation: the VM runs bytecode, while native build generates and compiles C.

## Why a Pratt parser?

A Pratt parser is a compact top-down operator-precedence method for expressions. Prefix handlers parse forms such as literals, unary operators, and grouping; infix handlers parse calls, indexing, assignment, and binary operators. A precedence table controls which operator binds more tightly. This keeps expression precedence and associativity in one extensible mechanism instead of requiring a separate grammar production for every precedence level. Statements and declarations still use ordinary parser routines.

## How static type inference works

Fresh has static checking with **local inference**. For a binding such as `let r1 = fib_recursive(20);`, the checker visits the initializer, obtains the call's return type, and assigns that type to `r1` in the current scope. An annotation such as `let x: int` supplies an expected type, which the initializer must satisfy. Function parameters and return types in the selected Fibonacci demo are explicitly annotated. This is not evidence of global Hindley–Milner inference, generic type variables, or inference across mutually recursive unannotated functions.

## How the VM executes bytecode

The compiler produces a chunk of opcodes and constants. The VM maintains a value stack and call frames for active functions; instructions push, read, update, and pop values, perform operations, branch, and invoke functions. Calls create frames and returns restore the caller's execution position. Closures retain references to captured upvalues so a returned nested function can continue to observe and mutate its lexical variables. `--disassemble` shows the generated instructions in readable form.

## Mark-and-sweep garbage collection

Fresh's collector tracks managed VM objects. During marking, it starts from live roots such as globals, stack values, call-frame closures, and open upvalues, then follows references held by closures, structs, and arrays. During sweeping, unmarked objects are removed from the tracked heap; marks on survivors are cleared for the next collection. This is tracing collection, not reference counting. It manages Fresh VM objects; it does not imply that all host Python allocations are controlled by this collector.

For a safe live illustration that reachable state survives frequent collections, run:

```powershell
$env:FRESH_GC_STRESS = '1'
fresh run examples/04_closure_counter.fresh
Remove-Item Env:FRESH_GC_STRESS
```

The counter should still print A as `1, 2, 3`, B as `101, 102`, then A as `4`. Stress mode asks the collector to run on every managed allocation. This demonstrates root/reference tracing under pressure; it does **not** measure GC speed or prove that Fresh's collector is faster than Python's collector.

## C99 transpilation versus VM execution

`fresh run` compiles to Fresh bytecode, optimizes that bytecode, and executes it in the Fresh VM. `fresh run FILE --emit-c` translates the program to C source and prints it; it does not compile or run that C. `fresh build PROJECT` reads the manifest entry, transpiles it to C, then invokes a detected host compiler to make a native executable. The native executable runs as compiled machine code and does not need the Fresh VM at runtime. Backend coverage is not identical: current capability declarations mark arrays restricted for native C and `match` and lambdas unsupported for that backend.

### Honest performance comparison and two measured scenarios

Do not claim that mark-and-sweep makes Fresh faster. The VM is implemented in Python, and its GC adds tracing work. Also, the native backend uses C allocation/runtime behavior, not the Fresh VM collector. A measured native-vs-Python speed difference demonstrates compiled-code execution, not superior memory management.

I measured two equivalent scalar workloads on this review machine: Windows, Python 3.14.7, GCC 16.2.0. Each native executable was built once with `fresh build`; build time was excluded. Timings are five-run medians from PowerShell and include starting a new process for each run. The Fresh build invokes GCC without an optimization flag, and the Python programs used the same straightforward algorithms.

| Scenario | Workload / verified result | Fresh native median | Python median |
|---|---|---:|---:|
| Integer loop | Sum `0..20,000,000`; both printed `200000010000000` | 54.0 ms | 1,532.2 ms |
| Recursion | Recursive Fibonacci `fib(32)`; both printed `2178309` | 47.5 ms | 405.7 ms |

These are observations from one machine and one run session, not portable benchmark guarantees. They compare Fresh's generated C executable with this Python interpreter, not the Fresh VM, and do not establish an advantage over optimized C or C++. C and C++ are compiled languages too and may match or beat the native Fresh output. The GC comparison to explain at the review is about automatic reclamation and reduced manual lifetime bookkeeping; speed must be benchmarked separately for a specific workload.

## 20 likely viva questions

1. **What is Fresh?** A statically checked language with a bytecode VM and a C99 transpilation/build path.
2. **What does the lexer do?** It turns source characters into a stream of tokens with source locations.
3. **What does the AST represent?** The parsed program's nested expression and statement structure.
4. **Why use Pratt parsing?** It handles prefix and infix expression forms with precedence and associativity in a concise table-driven parser.
5. **What is precedence?** The rule determining which operator groups first, such as multiplication before addition.
6. **What does the resolver do?** It checks declarations and names against lexical scopes.
7. **When are type errors caught?** During static checking, before bytecode execution or native code generation.
8. **What is type inference here?** Local bindings can obtain their type from the initializer expression.
9. **Is Fresh fully inferred?** No claim of full polymorphic inference; the examples use explicit function signatures and local inference.
10. **What is bytecode?** A compact instruction representation executed by the VM.
11. **What is a call frame?** VM state for a currently executing function, including its instruction position and locals.
12. **How does recursion work?** Each call creates another active frame, and return resumes the caller.
13. **What is a closure?** A function value together with access to captured lexical variables.
14. **What is an upvalue?** A VM reference used to preserve a captured variable after its defining scope returns.
15. **What does the optimizer do?** Simplifies bytecode with supported folding and peephole passes.
16. **How does mark-and-sweep work?** Trace reachable heap objects from roots, then reclaim unmarked objects.
17. **What roots does the collector inspect?** The implementation traces globals, VM stack values, frames/closures, and upvalues.
18. **What does `--emit-c` do?** It prints transpiled C source; the command itself does not produce a binary.
19. **How does `fresh build` produce a native program?** It loads the project entry, transpiles to C, then invokes an available host C compiler.
20. **What is a known native backend limitation?** Capability checks currently restrict arrays and reject lambdas and match expressions for native C.

## Honest limitations and review caveats

- The full pytest suite could not be run in the review environment because pytest is absent and the registered Python 3.13 path is stale. Do not describe the suite as passing.
- The installed `fresh` launcher prints a stale Python path warning even though the commands used for this review returned the expected results.
- The working-tree Fibonacci example has an inaccurate `Iterative` output label and explicit function types; only its local `let` binding demonstrates inference. The file was already modified before this review and was preserved.
- Native backend support is not feature-for-feature equal to VM support. Capability metadata marks arrays restricted and match/lambda unsupported.
- Native build depends on an installed compatible C compiler. GCC build and execution were verified on this machine only.
- The README's advertised test count and broad compatibility claims were not independently verified in this review.
