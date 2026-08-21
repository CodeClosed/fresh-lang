# Fresh Language Compatibility & Versioning Policy

This document establishes the official stability guarantees, semantic versioning policy, and deprecation cycle for the Fresh programming language and toolchain.

---

## 1. Semantic Versioning (SemVer 2.0)

Fresh adheres to Semantic Versioning (MAJOR.MINOR.PATCH):

- **MAJOR (e.g., 1.0.0 -> 2.0.0)**:
  Incompatible syntax changes, breaking modifications to the standard library APIs, or breaking changes to core VM opcode semantics.
- **MINOR (e.g., 1.0.0 -> 1.1.0)**:
  Backwards-compatible additions of new syntax, new standard library modules/functions, compiler optimization flags, or non-breaking toolchain enhancements.
- **PATCH (e.g., 1.0.0 -> 1.0.1)**:
  Backwards-compatible bug fixes, security patches, diagnostic formatting improvements, and internal refactorings.

---

## 2. Stability Guarantees

### Language Specification Stability
- Any valid Fresh program adhering to the specification in docs/FRESH_SPECIFICATION.md will remain valid and produce identical observable outputs across all minor and patch releases within a MAJOR series.

### Standard Library API Stability
- All public functions documented in Section 10 of docs/FRESH_SPECIFICATION.md (e.g. println, len, push, pop, bs, sqrt, etc.) are guaranteed stable. No parameter or return types will change without a major version bump.

### Bytecode VM ISA Stability
- Opcodes defined in resh.codegen.opcodes are stable within minor versions. New opcodes may be introduced in minor versions, but existing opcode semantics remain consistent.

### Backend Capability Tiers
- **Tier 1 (Fresh VM Runtime)**: Fully compliant host execution for all language features.
- **Tier 2 (Fresh Native C Backend)**: Transpiles statically typed functions, structs, and loops with verified 1:1 behavioral equivalence. Any unsupported construct is rejected at compile-time with diagnostic [E3001].

---

## 3. Deprecation Policy

When an existing feature or API is slated for removal:
1. It will first be marked as **deprecated** in a minor release (1.x.0) with a clear compiler warning diagnostic.
2. It will remain functional throughout all subsequent 1.x releases.
3. It will only be removed in the next major release (2.0.0).
