---
title: Source-backed Node.js and TypeScript guidance
tags: [nodejs, typescript, tsconfig, async, event-loop, reliability]
---

# Source-backed Node.js and TypeScript guidance

Use this reference for Node runtime behavior, TypeScript configuration, async
execution, and service reliability. Primary sources:

- [Node.js TypeScript support](https://nodejs.org/api/typescript.html)
- [Node.js event-loop guidance](https://nodejs.org/en/learn/asynchronous-work/dont-block-the-event-loop)
- [TypeScript TSConfig reference](https://www.typescriptlang.org/tsconfig/)

- Preserve an existing strict TypeScript configuration. Add stricter options
  only with a scoped migration plan.
- Treat native TypeScript execution as runtime-specific: syntax stripping does
  not replace type checking, bundling, or publishing transforms.
- Keep CPU-heavy work, synchronous I/O, and large unbounded transforms off
  request-path event loops.
- Use cancellation, explicit timeouts, and graceful shutdown at external and
  background-work boundaries.
- Prefer discriminated unions, type guards, and `unknown` for untrusted data.
- Validate environment variables before opening listeners or processing jobs.

Adapt guidance to the repository's runtime, module system, bundler, test
runner, and deployment model.
