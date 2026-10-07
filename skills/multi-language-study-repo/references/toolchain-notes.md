---
title: Toolchain notes for Java 25, Python 3, JavaScript and TypeScript 7
tags: [java-25, python, nodejs, typescript-7, maven, junit, sandbox, powershell, verification, single-language]
---

# Toolchain notes

Targets for the languages a study repo can use: Java 25 (Temurin) with Maven
3.9, Python 3.12+ (CI runs 3.12 then 3.13), Node.js 24 LTS, TypeScript 7
(native `tsc`). Versions move: check the current releases before pinning, and
keep CI, READMEs and the spec on the same numbers.

The language set is a per-project decision (one language is fine). The
sections below are independent: read only those of the chosen languages, plus
"Sandboxes and the user's machine". A single-language repo needs that one
language section, its CI job plus `docs`, and a verify script trimmed to its
own blocks.

## Java 25

- Instance main (JEP 512): the demo is an ordinary class with
  `void main()`; no `public static`, no `String[]`. `IO.println(...)`
  (`java.lang.IO`) replaces `System.out.println`. A compact source file with no
  class declaration is the unnamed-package form; inside a Maven package, use an
  explicit class and run it with `java -cp target/classes <package>.Demo`.
- Value objects are `record`s; validate in the compact canonical constructor
  and throw `IllegalArgumentException`. `Math.ceilDiv(int, int)` gives integer
  ceil-division.
- The abstraction is a plain `interface` (annotate `@FunctionalInterface`
  when it has one operation so lambdas qualify). Do not `seal` it: the
  pattern stays open for extension.
- JUnit Jupiter through the BOM, so versions stay aligned. Check the current
  release on Maven Central (a sandbox may block it; read it on the user's
  machine or from CI logs):

```xml
<properties>
  <maven.compiler.release>25</maven.compiler.release>
  <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
  <junit.version><!-- current JUnit release --></junit.version>
</properties>
<dependencyManagement>
  <dependencies>
    <dependency>
      <groupId>org.junit</groupId>
      <artifactId>junit-bom</artifactId>
      <version>${junit.version}</version>
      <type>pom</type>
      <scope>import</scope>
    </dependency>
  </dependencies>
</dependencyManagement>
<dependencies>
  <dependency>
    <groupId>org.junit.jupiter</groupId>
    <artifactId>junit-jupiter</artifactId>
    <scope>test</scope>
  </dependency>
</dependencies>
<!-- build: maven-compiler-plugin <release>${maven.compiler.release}</release> with -Xlint:all;
     maven-surefire-plugin 3.x; pin current plugin versions -->
```

- CI: `actions/setup-java` with `distribution: temurin`, `java-version: '25'`,
  `cache: maven`; then `mvn -B -ntp verify` and the demo.

## Python 3.12+

- `typing.Protocol` for the abstraction (adapt plain callables with a small
  adapter or a `__call__` Protocol); `typing.override` (3.12) on concrete
  methods.
- Value objects: `@dataclass(frozen=True, slots=True)`; validate in
  `__post_init__` and raise `ValueError`.
- Standard library only; tests with `unittest`; `src/` layout. Run:
  `PYTHONPATH=src python -m unittest discover -s tests -t .` and the demo as
  `PYTHONPATH=src python -m <python_package>` (`__main__.py`). Minimal
  `pyproject.toml` with `requires-python = ">=3.12"`.
- Run on both 3.12 and 3.13 sequentially inside ONE CI job named `python`
  (stable required-check name).
- Commands in these docs say `python`; use `python3` where `python` is missing
  or not Python 3. On Windows keep `python` (`python3` is often a Microsoft
  Store stub).
- Format money with `divmod(cents, 100)` and zero padding, never floats.

## JavaScript on Node 24

- ES modules (`"type": "module"`), no runtime dependencies, `node:test` with
  `node:assert/strict`, run with `node --test`.
- Use only ES2025/ES2026 features that Node 24 actually supports (for
  example iterator helpers). Probe before use, for example
  `node -p "typeof Iterator.prototype.map"`; do not depend on proposals that
  need flags (for example `Temporal`) in an example.
- There are no interfaces: the contract is a duck-typed object (or a plain
  function) documented with a JSDoc `@typedef`. Use `#private` fields and
  `Object.freeze` for value objects; throw `RangeError` / `TypeError`.
- Keep money as safe integers; cents formatting with integer division.

## TypeScript 7 (native tsc)

- Install the native compiler as `typescript@7.x` (pin an exact version in
  `devDependencies`) and run `tsc -v` in the verification to prove which
  compiler ran.
- TS 6 and 7 no longer auto-include `@types/*`: add `@types/node` AND
  `"types": ["node"]`, or `node:` imports and `process` fail to resolve.
- Removed or deprecated options to avoid: `moduleResolution: node` /
  `node10`, `baseUrl`, `target: es5`, `outFile`. Use `module: nodenext` with
  `moduleResolution: nodenext`.
- With `nodenext` and `"type": "module"`, relative imports in TS source need
  the `.js` extension (`import { Order } from "./order.js"`), and
  `verbatimModuleSyntax` needs `import type` for type-only imports.
- `node --test` needs a QUOTED glob: `node --test "dist/test/**/*.test.js"`.
  A bare directory fails, and an unquoted glob is expanded (or not) by the
  shell. Learning: `typescript-7-needs-explicit-node-types-and-quoted-test-globs`.
- Commit `package-lock.json` (generate it on a machine with registry access
  using `npm install --no-audit --no-fund`) so CI can `npm ci`. Keep it when
  lanes are re-merged: lanes cannot create it in a registry-blocked sandbox.

`tsconfig.json`:

```json
{
  "compilerOptions": {
    "target": "ES2024",
    "lib": ["ES2024"],
    "module": "nodenext",
    "moduleResolution": "nodenext",
    "types": ["node"],
    "strict": true,
    "verbatimModuleSyntax": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitOverride": true,
    "noFallthroughCasesInSwitch": true,
    "isolatedModules": true,
    "skipLibCheck": true,
    "rootDir": ".",
    "outDir": "dist"
  },
  "include": ["src/**/*.ts", "test/**/*.ts"]
}
```

`package.json` (`rootDir: "."` makes the output `dist/src/**` and
`dist/test/**`):

```json
{
  "name": "<repo>-ts",
  "version": "1.0.0",
  "private": true,
  "type": "module",
  "engines": { "node": ">=24" },
  "scripts": {
    "build": "tsc -p tsconfig.json",
    "test": "npm run build && node --test \"dist/test/**/*.test.js\"",
    "demo": "npm run build && node dist/src/demo.js",
    "typecheck": "tsc -p tsconfig.json --noEmit"
  },
  "devDependencies": {
    "@types/node": "<24.x current>",
    "typescript": "<7.x exact>"
  }
}
```

## Sandboxes and the user's machine

Cloud sandboxes often block package registries and release hosts (npm, Maven
Central, GitHub web and releases, YouTube, Medium returned HTTP 403). So:

- In the sandbox do best-effort checks with whatever is installed (an older
  JDK, Node or `tsc` is fine for syntax and logic). Report them as partial.
- Run the DEFINITIVE build and tests on the user's machine (or in CI), after
  installing missing toolchains user-locally without admin rights:

```powershell
# JDK: Adoptium API zip into the user profile (no admin, no PATH change)
$jdkRoot = "$env:USERPROFILE\.jdks"
New-Item -ItemType Directory -Force $jdkRoot | Out-Null
Invoke-WebRequest "https://api.adoptium.net/v3/binary/latest/25/ga/windows/x64/jdk/hotspot/normal/eclipse" -OutFile "$jdkRoot\jdk25.zip"
Expand-Archive "$jdkRoot\jdk25.zip" -DestinationPath $jdkRoot -Force
# Maven: the binary zip from the Apache Maven downloads page into "$env:USERPROFILE\.m2\tools"
```

- Never change the global PATH. Set `JAVA_HOME` and `PATH` per command inside a
  verification script, so the machine's other tools keep working.
- Sync lane output to the machine as ONE archive (extract with `tar -xf`).
  Write each new version under a fresh filename and check a unique marker or
  length on the machine: overwriting an existing path once kept the old bytes
  (learning `device-commit-to-existing-path-can-keep-stale-bytes`).
- Learning for this whole class of problems:
  `cloud-sandbox-egress-blocks-registries-verify-on-user-machine`.

Verification script skeleton (`verify.ps1`; keep it and its log outside the
repo, since logs contain local paths):

```powershell
# $Only defaults to the repo's chosen languages plus docs (for example @('java','docs'));
# delete the blocks of languages the repo does not use.
param([string]$Repo = '<repo checkout path>', [string[]]$Only = @('java','python','javascript','typescript','docs'))
$env:JAVA_HOME = "$env:USERPROFILE\.jdks\<extracted jdk folder>"
$env:Path = "$env:JAVA_HOME\bin;$env:USERPROFILE\.m2\tools\<maven folder>\bin;$env:Path"
$log = "$env:TEMP\verify-<repo>.log"
"=== verify $(Get-Date -Format s) ===" | Set-Content $log
function Step($name, [scriptblock]$cmd) {
  $out = & $cmd 2>&1 | Out-String
  $code = $LASTEXITCODE
  "--- $name -> exit $code" | Add-Content $log
  $out | Add-Content $log
  "$name -> exit $code"
}
if ($Only -contains 'java') {
  Set-Location "$Repo\java"
  Step 'java: mvn verify' { mvn -B -ntp -q verify }
  Step 'java: demo' { java -cp target/classes <package>.Demo }
}
if ($Only -contains 'python') {
  Set-Location "$Repo\python"; $env:PYTHONPATH = 'src'
  Step 'python: unittest' { python -m unittest discover -s tests -t . }
  Step 'python: demo' { python -m <python_package> }
  Remove-Item Env:PYTHONPATH
}
if ($Only -contains 'javascript') {
  Set-Location "$Repo\javascript"
  Step 'js: node --test' { node --test }
  Step 'js: demo' { node src/demo.js }
}
if ($Only -contains 'typescript') {
  Set-Location "$Repo\typescript"
  if (Test-Path package-lock.json) { Step 'ts: npm ci' { npm ci --no-audit --no-fund } }
  else { Step 'ts: npm install (creates the lockfile to commit)' { npm install --no-audit --no-fund } }
  Step 'ts: tsc version' { npx tsc -v }
  Step 'ts: npm test' { npm test }
  Step 'ts: demo' { npm run -s demo }
}
if ($Only -contains 'docs') {
  Set-Location $Repo
  Step 'docs: generated page up to date' { python .github/scripts/gen_code_by_component.py --config .github/scripts/components.json --root . --check }
  Step 'docs: check_docs' { python .github/scripts/check_docs.py --root . }
}
```

Report each `Step` line (name and exit code) as evidence, plus the toolchain
versions printed for the chosen languages (`java -version`, `python --version`,
`node -v`, `npx tsc -v`).
