# 🛡 Fresh Compatibility Guarantees & Diagnostics Catalog

This document establishes the official semantic versioning policy, stability guarantees, deprecation lifecycle, and compiler diagnostic error code catalog for the Fresh programming language.

---

## 1. Semantic Versioning Policy (SemVer 2.0)

Fresh adheres strictly to Semantic Versioning (`MAJOR.MINOR.PATCH`):

- **MAJOR (e.g., 1.0.0 $\rightarrow$ 2.0.0)**:
  Incompatible syntax changes, breaking modifications to the standard library APIs, or breaking alterations to bytecode VM opcode semantics.
- **MINOR (e.g., 1.0.0 $\rightarrow$ 1.1.0)**:
  Backwards-compatible additions of new syntax, new standard library functions, compiler optimization passes, or non-breaking CLI enhancements.
- **PATCH (e.g., 1.0.0 $\rightarrow$ 1.0.1)**:
  Backwards-compatible bug fixes, security updates, diagnostic formatting improvements, and internal refactorings.

---

## 2. Stability Guarantees

### Language Specification Stability
Any conforming Fresh program adhering to the specification in [`docs/specification.md`](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/docs/specification.md) will remain valid and produce identical observable outputs across all minor and patch releases within a `MAJOR` series.

### Standard Library API Stability
All public functions documented in [`docs/standard_library.md`](file:///c:/Users/vihaa/OneDrive/Desktop/NEW_LANG/docs/standard_library.md) (`println`, `len`, `push`, `pop`, `abs`, `sqrt`, etc.) are guaranteed stable. No parameter or return types will change without a major version bump.

### Bytecode VM ISA Stability
Opcodes defined in `fresh.codegen.opcodes` are stable within minor versions. New opcodes may be appended in minor versions, but existing opcode behaviors remain backwards-compatible.

### Backend Capability Tiers
- **Tier 1 (Fresh VM Runtime)**: Fully compliant host execution for all language features including closures, pattern matching, dynamic arrays, and garbage collection.
- **Tier 2 (Fresh Native C Backend)**: Transpiles statically typed functions, structs, and loops with verified 1:1 behavioral equivalence. Any unsupported dynamic construct is rejected at compile-time with diagnostic `[E3001]`.

---

## 3. Deprecation Lifecycle

When an existing feature or API is slated for removal:
1. It will first be marked as **deprecated** in a minor release (`1.x.0`) with a clear compiler warning diagnostic.
2. It will remain fully functional throughout all subsequent `1.x` releases.
3. It will only be removed in the next major release (`2.0.0`).

---

## 4. Diagnostic Error Codes Catalog

Fresh uses standardized diagnostic error codes across all compilation phases:

| Code | Phase | Category | Description |
|:---|:---|:---|:---|
| **`[E1001]`** | Lexer | `FreshLexError` | Invalid or unrecognized token, unclosed string literal, or non-UTF-8 character sequence. |
| **`[E2001]`** | Parser | `FreshParseError` | Syntax error, unexpected token, missing semicolon or closing delimiter. |
| **`[E3001]`** | Type Checker | `FreshTypeError` | Type mismatch in assignment, arithmetic operation, function argument, or invalid struct access. |
| **`[E4001]`** | Modules | `FreshModuleError` | Module not found, invalid import path, or circular module dependency detected. |
| **`[E5001]`** | Runtime | `FreshRuntimeError` | Division by zero, array out-of-bounds, pop from empty array, or file I/O failure. |

All errors are rendered with the source line, column, and diagnostic caret underlines for immediate error localization.
