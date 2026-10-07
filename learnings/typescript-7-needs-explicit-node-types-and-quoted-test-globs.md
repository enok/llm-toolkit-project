---
title: TypeScript 7 needs explicit Node types, and node --test needs a quoted glob
category: build
created: 2026-10-07
tags: [typescript, nodejs, tsconfig, node-test, glob, npm-ci, build-config]
---

# Problem

Two build traps with the native TypeScript 7 compiler on Node 24. TS 6 and 7 no longer
include `@types/*` packages automatically, so Node typings must be declared. Separately,
`node --test` given a bare directory fails; the pattern must be a quoted glob.

# Failed Approaches

- `node --test` with a bare directory (for example `node --test dist/test`): it fails.

# Solution

Declare the Node typings in both places, use the Node-aware module settings, and quote the
glob in the npm script (fragments of the full templates in the durable reference):

```json
{
  "compilerOptions": {
    "module": "nodenext",
    "moduleResolution": "nodenext",
    "types": ["node"],
    "rootDir": ".",
    "outDir": "dist"
  }
}
```

```json
{
  "scripts": {
    "test": "npm run build && node --test \"dist/test/**/*.test.js\""
  },
  "devDependencies": {
    "@types/node": "<24.x current>",
    "typescript": "<7.x exact>"
  }
}
```

- Avoid the removed options: `moduleResolution: node` or `node10`, `baseUrl`,
  `target: es5`, `outFile`.
- Commit `package-lock.json` so CI can run `npm ci`. Generate it with `npm install` on a
  machine that can reach the registry; the sandbox could not.

Durable guidance: skills/multi-language-study-repo/references/toolchain-notes.md

# Why

TS 6 and 7 stopped auto-including `@types`, so `@types/node` plus `"types": ["node"]` is
required. For the test command the session recorded that a bare directory fails and a
quoted glob works, without a cause. General guidance, not observed in this session:
quoting passes the pattern to Node unchanged instead of leaving the shell to expand it.
