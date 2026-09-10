#!/usr/bin/env node
"use strict";

const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");

function usage() {
  console.log(`Usage:
  node scripts/create-specialist-agent.js <agent-name> [--domain "..."] [--description "..."] [--force] [--dry-run]
  node scripts/create-specialist-agent.js --sync-tool-configs [project]
  node scripts/create-specialist-agent.js --apply-subagents <codex|cursor|claude|all> [project]
  node scripts/create-specialist-agent.js --apply-subagents <codex|cursor|claude> --target <dir>

Renders copy only the files each provider actually reads from tool-subagents/:
codex reads *.toml only, cursor and claude read *.md only ('all' applies each
provider's own rule to its own project-relative directory). For claude and
cursor, the rendered *.md frontmatter drops the toolkit-only 'readonly' and
'tier' keys and, when 'tier: light' was set, writes the provider's cheap-model
value ('model: haiku' for claude, 'model: fast' for cursor) so the cost intent
survives the render; the canonical tool-subagents/*.md source is untouched.
--target <dir> renders a single provider (not 'all') into an explicit
directory (e.g. ~/.claude/agents) instead of "<project>/.codex|.cursor|.claude/agents";
see docs/global-install.md for the optional provider-rendered agent copies.
`);
}

function fail(message) {
  console.error(`FAIL: ${message}`);
  process.exit(1);
}

function safeRepoPath(relativePath) {
  if (path.isAbsolute(relativePath) || relativePath.split(/[\\/]+/).includes("..")) {
    fail(`refusing path outside repository: ${relativePath}`);
  }
  // nosemgrep: javascript.lang.security.audit.path-traversal.path-join-resolve-traversal.path-join-resolve-traversal
  const resolved = path.resolve(ROOT, relativePath);
  if (resolved !== ROOT && !resolved.startsWith(`${ROOT}${path.sep}`)) {
    fail(`refusing path outside repository: ${relativePath}`);
  }
  return resolved;
}

function resolveProjectPath(projectArg) {
  const raw = projectArg || ".";
  // nosemgrep: javascript.lang.security.audit.path-traversal.path-join-resolve-traversal.path-join-resolve-traversal
  const resolved = path.resolve(ROOT, raw);
  if (!fs.existsSync(resolved) || !fs.statSync(resolved).isDirectory()) {
    fail(`project directory not found: ${raw}`);
  }
  return resolved;
}

function parseFlags(argv) {
  const flags = { _: [] };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (!arg.startsWith("--")) {
      flags._.push(arg);
      continue;
    }
    const key = arg.slice(2);
    if (key === "force" || key === "dry-run") {
      // Normalize kebab-case flags to the camelCase keys consumers read.
      flags[key === "dry-run" ? "dryRun" : key] = true;
      continue;
    }
    const value = argv[i + 1];
    if (!value || value.startsWith("--")) {
      fail(`--${key} requires a value`);
    }
    flags[key] = value;
    i += 1;
  }
  return flags;
}

function ensureKebabName(name) {
  if (!/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/.test(name)) {
    fail(`agent name must be kebab-case and start with a letter: ${name}`);
  }
}

function titleCase(name) {
  return name
    .split("-")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function writeFile(relativePath, content, options) {
  const target = safeRepoPath(relativePath);
  const exists = fs.existsSync(target);
  if (exists && !options.force) {
    console.log(`SKIP exists: ${relativePath}`);
    return;
  }
  if (options.dryRun) {
    console.log(`${exists ? "WOULD UPDATE" : "WOULD CREATE"}: ${relativePath}`);
    return;
  }
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.writeFileSync(target, content, "utf8");
  console.log(`${exists ? "UPDATE" : "CREATE"}: ${relativePath}`);
}

function runPowerShell(args, cwd = ROOT) {
  const result = spawnSync("powershell.exe", args, {
    cwd,
    stdio: "inherit",
    shell: false,
  });
  if (result.error) {
    fail(`powershell.exe failed to start: ${result.error.message}`);
  }
  if (result.status !== 0) {
    fail(`powershell.exe ${args.join(" ")} exited ${result.status}`);
  }
}

function runBash(args, cwd = ROOT) {
  const result = spawnSync("bash", args, {
    cwd,
    stdio: "inherit",
    shell: false,
  });
  if (result.error) {
    fail(`bash failed to start: ${result.error.message}`);
  }
  if (result.status !== 0) {
    fail(`bash ${args.join(" ")} exited ${result.status}`);
  }
}

function runToolkitSync(projectArg) {
  const project = projectArg || ".";
  if (process.platform === "win32") {
    runPowerShell([
      "-NoProfile",
      "-ExecutionPolicy",
      "Bypass",
      "-File",
      safeRepoPath("scripts/sync-tool-configs.ps1"),
      project,
    ]);
  } else {
    runBash([safeRepoPath("scripts/sync-tool-configs.sh"), project]);
  }
}

function sameRealPath(a, b) {
  try {
    return fs.realpathSync.native(a) === fs.realpathSync.native(b);
  } catch (_err) {
    return false;
  }
}

// Only rewrite `destination` when its content would actually change, and never
// touch it when it is the same real file as `source` (a provider directory
// that is itself a symlink/junction onto tool-subagents/ is canonical by
// construction; "copying" onto it would self-mutate the canonical source).
function copyChangedFile(source, destination, transform) {
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  if (sameRealPath(source, destination)) {
    return false;
  }
  const raw = fs.readFileSync(source);
  const next = transform ? Buffer.from(transform(raw.toString("utf8")), "utf8") : raw;
  if (fs.existsSync(destination)) {
    const current = fs.readFileSync(destination);
    if (Buffer.compare(current, next) === 0) {
      return false;
    }
  }
  fs.writeFileSync(destination, next);
  return true;
}

// Each provider only reads one of the two canonical file shapes.
function providerRenderExtension(provider) {
  if (provider === "codex") {
    return ".toml";
  }
  if (provider === "cursor" || provider === "claude") {
    return ".md";
  }
  fail(`unsupported provider '${provider}', expected codex, cursor, claude, or all`);
  return null;
}

// claude/cursor renders keep frontmatter as-is except: drop the 'readonly'
// and 'tier' keys (unknown to those tools), and when 'tier: light' was set,
// write the provider's cheap-model value so the cost intent survives the
// render (model: haiku for claude, model: fast for cursor).
function rewriteFrontmatterForProvider(provider, content) {
  const match = content.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n/);
  if (!match) {
    return content;
  }
  let tierValue = null;
  const kept = [];
  for (const line of match[1].split(/\r?\n/)) {
    const colon = line.indexOf(":");
    const key = colon === -1 ? line.trim() : line.slice(0, colon).trim();
    if (key === "tier") {
      tierValue = colon === -1 ? "" : line.slice(colon + 1).trim().replace(/^["']|["']$/g, "");
      continue;
    }
    if (key === "readonly") {
      continue;
    }
    kept.push(line);
  }
  if (tierValue === "light") {
    const cheapModel = provider === "claude" ? "haiku" : "fast";
    for (let i = 0; i < kept.length; i += 1) {
      const colon = kept[i].indexOf(":");
      if (colon !== -1 && kept[i].slice(0, colon).trim() === "model") {
        kept[i] = `model: ${cheapModel}`;
      }
    }
  }
  return `---\n${kept.join("\n")}\n---\n${content.slice(match[0].length)}`;
}

function expandHome(target) {
  const home = process.env.HOME || process.env.USERPROFILE;
  if (!home) {
    return target;
  }
  if (target === "~") {
    return home;
  }
  if (target.startsWith("~/") || target.startsWith("~\\")) {
    return path.join(home, target.slice(2));
  }
  return target;
}

function renderProviderInto(provider, sourceRoot, targetRoot, label) {
  const extension = providerRenderExtension(provider);
  fs.mkdirSync(targetRoot, { recursive: true });
  const transform = provider === "codex" ? null : (text) => rewriteFrontmatterForProvider(provider, text);
  let changed = 0;
  for (const entry of fs.readdirSync(sourceRoot)) {
    if (!entry.endsWith(extension)) {
      continue;
    }
    if (!/^[a-z0-9-]+(?:\.md|\.toml)$/.test(entry) && entry !== "README.md") {
      fail(`unexpected subagent filename: ${entry}`);
      continue;
    }
    const source = path.join(sourceRoot, entry);
    // nosemgrep: javascript.lang.security.audit.path-traversal.path-join-resolve-traversal.path-join-resolve-traversal
    const destination = path.join(targetRoot, entry);
    if (copyChangedFile(source, destination, transform)) {
      changed += 1;
      console.log(`APPLY ${label}/${entry}`);
    }
  }
  return changed;
}

function applySubagents(providerArg, projectArg, targetArg) {
  const provider = providerArg || "codex";
  const projectTargets = {
    codex: ".codex/agents",
    cursor: ".cursor/agents",
    claude: ".claude/agents",
  };
  const providers = provider === "all" ? ["codex", "cursor", "claude"] : [provider];
  if (provider !== "all" && !projectTargets[provider]) {
    fail(`unsupported provider '${provider}', expected codex, cursor, claude, or all`);
  }

  const sourceRoot = path.join(ROOT, "tool-subagents");
  let changed = 0;

  if (targetArg) {
    if (provider === "all") {
      fail("--target requires a single provider (codex, cursor, or claude), not 'all'");
    }
    const expanded = expandHome(targetArg);
    if (!path.isAbsolute(expanded)) {
      fail(`--target must be an absolute path: ${targetArg}`);
    }
    changed = renderProviderInto(provider, sourceRoot, expanded, expanded);
    console.log(`Subagent apply complete for ${provider} -> ${expanded} (${changed} file update(s)).`);
    return;
  }

  const project = resolveProjectPath(projectArg || ".");
  for (const p of providers) {
    const targetRel = projectTargets[p];
    // targetRel comes from the provider allowlist above.
    // nosemgrep: javascript.lang.security.audit.path-traversal.path-join-resolve-traversal.path-join-resolve-traversal
    const targetRoot = path.resolve(project, targetRel);
    if (targetRoot !== project && !targetRoot.startsWith(`${project}${path.sep}`)) {
      fail(`refusing provider target outside project: ${targetRel}`);
      continue;
    }
    changed += renderProviderInto(p, sourceRoot, targetRoot, targetRel);
  }
  console.log(`Subagent apply complete for ${provider} (${changed} file update(s)).`);
}

function scaffold(name, flags) {
  ensureKebabName(name);
  const title = titleCase(name);
  const domain = flags.domain || title;
  const description =
    flags.description ||
    `${domain} specialist. Use for focused ${domain.toLowerCase()} validation, implementation guidance, and evidence-backed findings.`;
  const readOnly = flags.readonly !== "false";

  const files = new Map([
    [
      `tool-subagents/${name}.md`,
      `---
name: ${name}
description: ${description}
model: inherit
readonly: ${readOnly ? "true" : "false"}
---

You are the ${title} specialist.

Authority: ${readOnly ? "read-only; do not edit files, post comments, stage, commit, or push" : "bounded worker; edit only the files assigned by the root agent"}.

## Inputs

- Objective, repo path, base/head refs, and changed files.
- Relevant rules, workflows, skills, docs, tests, logs, and external evidence.
- Write ownership and user-facing approval constraints.

## Procedure

1. Inspect the actual source and evidence before reaching conclusions.
2. Stay inside the assigned scope and cite exact files, commands, or artifacts.
3. Separate blockers from optional improvements.
4. Recommend the smallest implementer action and the validation that proves it.
5. Surface reusable learning or token-efficiency improvements for the root agent.

## Related Specialists

- Name companion specialists that should review adjacent evidence lanes, and why.
- Return handoff recommendations to the root agent; do not contact other agents,
  tools, or humans directly.

## Output Contract

- Scope and evidence reviewed.
- Findings with severity, impact, evidence, and exact next action.
- Validation commands or evidence gaps.
- Related specialist handoffs.
- Risks and assumptions.
- Learning/token efficiency: reusable lesson, routing gap, or context that can
  move to \`workflows/${name}-evolution.md\`,
  \`workflows/specialist-agent-evolution.md\`, a rule, workflow, skill,
  reference, or consumer profile.
`,
    ],
    [
      `tool-subagents/${name}.toml`,
      `name = "${name}"
description = "${description.replace(/"/g, '\\"')}"
readonly = ${readOnly ? "true" : "false"}
developer_instructions = """
You are the ${title} specialist. Stay in assigned scope, cite evidence, return
actionable findings, recommend related specialist handoffs, surface
learning/token-efficiency improvements, and let the root agent own user
communication, validation, commits, pushes, and PR actions."""
`,
    ],
    [
      `workflows/${name}-validation.md`,
      `---
description: Run the ${title} specialist validation workflow
---

# ${title} Validation

Use this workflow when the ${title} specialist should validate a change or
artifact before implementation, approval, merge, or handoff.

## Steps

1. Establish repo, base/head, dirty-tree ownership, scope, and relevant evidence.
2. Load only the rules, skills, docs, and source files needed for the specialist.
3. Invoke or follow \`tool-subagents/${name}.md\`.
4. Reduce findings locally: accept only evidence-backed, in-scope findings.
5. Implement the smallest safe change only when the user requested fixes.
6. Run the narrowest meaningful validation.
7. Report findings, validation, residual risk, and reusable learning.

---

## Evolution

If this specialist misses a recurring issue or is too noisy, run
\`workflows/${name}-evolution.md\`.
`,
    ],
    [
      `workflows/${name}-evolution.md`,
      `---
description: Improve the ${title} specialist from validated misses, noisy findings, and routing gaps
---

# ${title} Evolution

Use this workflow when the ${title} specialist needs a durable improvement.

## Steps

1. Capture concrete evidence of the miss, noisy output, stale routing, or token
   inefficiency.
2. Classify the fix across the prompt, workflow, skill, routing map, client
   overlays, or validation gate.
3. Make the smallest generic update.
4. Run \`node scripts/validate-specialist-agent.js ${name}\`.
5. Sync provider surfaces and run the repository validation required by the task.
6. Report the evidence, updated files, validation, and residual risk.
`,
    ],
    [
      `skills/${name}/SKILL.md`,
      `---
name: ${name}
description: ${description}
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.0.0"
---

# ${title}

Use this skill to route work through the ${title} specialist.

## Workflow

1. Load \`workflows/${name}-validation.md\`.
2. Invoke or follow \`tool-subagents/${name}.md\`.
3. Keep root-agent ownership for edits, validation, commits, pushes, and
   user-facing communication.
4. Compose with related specialists only when their evidence lanes are relevant.
5. If the specialist misses a reusable pattern, run
   \`workflows/${name}-evolution.md\`.
`,
    ],
  ]);

  for (const [relativePath, content] of files.entries()) {
    writeFile(relativePath, content, flags);
  }

  console.log(`
Next checklist for ${name}:
- Add routing to INTENTS.md.
- Add index entries to AGENTS.md, README.md, workflows/README.md, and tool-subagents/README.md.
- Run: npm run tool-configs:sync
- Run: npm run subagents:apply -- codex .
- Run: node scripts/validate-specialist-agent.js ${name}
- Run the repository validation and commit only intentional files.
`);
}

const argv = process.argv.slice(2);
if (argv.length === 0 || argv.includes("--help") || argv.includes("-h")) {
  usage();
  process.exit(0);
}

if (argv[0] === "--sync-tool-configs") {
  runToolkitSync(argv[1]);
  process.exit(0);
}

if (argv[0] === "--apply-subagents") {
  const rest = argv.slice(1);
  const targetIndex = rest.indexOf("--target");
  let targetValue;
  if (targetIndex !== -1) {
    targetValue = rest[targetIndex + 1];
    if (!targetValue || targetValue.startsWith("--")) {
      fail("--target requires a value");
    }
    rest.splice(targetIndex, 2);
  }
  applySubagents(rest[0], rest[1], targetValue);
  process.exit(0);
}

const flags = parseFlags(argv.slice(1));
scaffold(argv[0], flags);
