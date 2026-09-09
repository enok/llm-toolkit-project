---
title: Use Maven Compiler release for Cross-Compilation
impact: MEDIUM
impactDescription: source/target alone can compile calls to APIs that do not exist on the target runtime
tags: java, maven, compiler, release, cross-compilation, runtime-compatibility
---

## Use `release` when building with JDK 9+

When Maven runs on JDK 9 or newer but the application targets an older Java runtime, configure `maven-compiler-plugin` with `release` instead of separate `source` and `target`.

**Incorrect (bytecode target only):**

```xml
<source>1.8</source>
<target>1.8</target>
```

This can still compile references to APIs introduced after Java 8 when the build runs on JDK 17.

**Correct (syntax, bytecode, and API surface):**

```xml
<release>8</release>
```

Do not combine `release` with `source`/`target` in the same compiler configuration. If the build must run on JDK 8, use `source`/`target` because `release` is unavailable.
