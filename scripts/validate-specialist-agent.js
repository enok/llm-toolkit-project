#!/usr/bin/env node
"use strict";

const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
let failures = 0;

function fail(message) {
  failures += 1;
  console.error(`FAIL: ${message}`);
}

function warn(message) {
  console.warn(`WARN: ${message}`);
}

function pass(message) {
  console.log(`PASS: ${message}`);
}

function read(relativePath) {
  return fs.readFileSync(safeRepoPath(relativePath), "utf8");
}

function exists(relativePath) {
  return fs.existsSync(safeRepoPath(relativePath));
}

function listFiles(dir, predicate) {
  const root = safeRepoPath(dir);
  if (!fs.existsSync(root)) {
    return [];
  }
  return fs.readdirSync(root).filter(predicate).sort();
}

function safeRepoPath(relativePath) {
  if (path.isAbsolute(relativePath) || relativePath.split(/[\\/]+/).includes("..")) {
    fail(`refusing path outside repository: ${relativePath}`);
    return ROOT;
  }
  // nosemgrep: javascript.lang.security.audit.path-traversal.path-join-resolve-traversal.path-join-resolve-traversal
  const resolved = path.resolve(ROOT, relativePath);
  if (resolved !== ROOT && !resolved.startsWith(`${ROOT}${path.sep}`)) {
    fail(`refusing path outside repository: ${relativePath}`);
    return ROOT;
  }
  return resolved;
}

function parseFrontmatter(text) {
  const match = text.match(/^---\n([\s\S]*?)\n---\n/);
  if (!match) {
    return {};
  }
  const data = {};
  for (const line of match[1].split(/\n/)) {
    const colon = line.indexOf(":");
    if (colon === -1) {
      continue;
    }
    const key = line.slice(0, colon).trim();
    const value = line.slice(colon + 1).trim().replace(/^["']|["']$/g, "");
    data[key] = value;
  }
  return data;
}

// Locate `key = ` at the start of a line and return the text that follows it.
// String scanning (no dynamic RegExp) keeps the TOML key handling literal.
function tomlValueAfterKey(toml, key) {
  const prefix = `${key} = `;
  let searchFrom = 0;
  while (searchFrom <= toml.length) {
    const index = toml.indexOf(prefix, searchFrom);
    if (index === -1) {
      return null;
    }
    if (index === 0 || toml[index - 1] === "\n") {
      return toml.slice(index + prefix.length);
    }
    searchFrom = index + prefix.length;
  }
  return null;
}

function parseTomlBasicString(toml, key) {
  const rest = tomlValueAfterKey(toml, key);
  if (rest === null || !rest.startsWith('"') || rest.startsWith('"""')) {
    return null;
  }
  const match = rest.match(/^"((?:[^"\\]|\\.)*)"/);
  if (!match) {
    return null;
  }
  return match[1].replace(/\\(["\\])/g, "$1");
}

function parseTomlMultilineString(toml, key) {
  const rest = tomlValueAfterKey(toml, key);
  if (rest === null || !rest.startsWith('"""')) {
    return null;
  }
  let body = rest.slice(3);
  if (body.startsWith("\n")) {
    body = body.slice(1);
  }
  const close = body.indexOf('"""');
  return close === -1 ? null : body.slice(0, close);
}

function parseTomlStringArray(toml, key) {
  const rest = tomlValueAfterKey(toml, key);
  if (rest === null || !rest.startsWith("[")) {
    return [];
  }
  const close = rest.indexOf("]");
  if (close === -1) {
    return [];
  }
  const inner = rest.slice(1, close);
  return (inner.match(/"(?:[^"\\]|\\.)*"/g) || []).map((entry) =>
    entry.slice(1, -1).replace(/\\(["\\])/g, "$1"),
  );
}

function normalizeWhitespace(text) {
  return text.replace(/\s+/g, " ").trim();
}

function stripFrontmatter(text) {
  return text.replace(/^---\n[\s\S]*?\n---\n/, "");
}

function assertContains(file, needle, label = needle) {
  if (!exists(file)) {
    fail(`${file} missing`);
    return;
  }
  const text = read(file);
  if (!text.includes(needle)) {
    fail(`${file} missing ${label}`);
  }
}

function checkWorkflowSizes() {
  const limit = 12000;
  for (const file of listFiles("workflows", (name) => name.endsWith(".md") && name !== "README.md")) {
    const text = read(`workflows/${file}`);
    if (text.length > limit) {
      fail(`workflows/${file} is ${text.length} characters; limit is ${limit}`);
    }
  }
  pass("workflow size check completed");
}

function checkSkillsIndex() {
  for (const skill of listFiles("skills", (name) =>
    /^[a-z0-9-]+$/.test(name) && fs.existsSync(safeRepoPath(`skills/${name}/SKILL.md`)),
  )) {
    const skillFile = `skills/${skill}/SKILL.md`;
    const meta = parseFrontmatter(read(skillFile));
    if (meta.name !== skill) {
      fail(`${skillFile} frontmatter name '${meta.name || ""}' does not match folder`);
    }
    assertContains("AGENTS.md", `**${skill}**`, `skill index entry ${skill}`);
    assertContains("README.md", `**${skill}**`, `skill index entry ${skill}`);
  }
  pass("skill index check completed");
}

function checkRulesRedirects() {
  const selectionFile = "docs/llm/toolkit-selection.txt";
  if (exists(selectionFile)) {
    for (const rawLine of read(selectionFile).split(/\r?\n/)) {
      const line = rawLine.trim();
      if (!line || line.startsWith("#")) {
        continue;
      }
      if (!exists(line)) {
        fail(`${selectionFile} references missing path: ${line}`);
      }
    }
  }
  for (const dir of [".windsurf/rules", ".windsurf/workflows", ".cursor/rules", ".cursor/workflows"]) {
    if (!exists(dir)) {
      // Provider overlays are generated links (gitignored); a fresh clone has none until sync runs.
      warn(`provider rules/workflows overlay missing: ${dir} (run ./scripts/sync-tool-configs.sh . --skip-agents-md --skip-github)`);
    }
  }
  pass("rules redirect/client overlay check completed");
}

function checkSubagents() {
  for (const file of listFiles("tool-subagents", (name) => name.endsWith(".md") && name !== "README.md")) {
    const agent = file.replace(/\.md$/, "");
    const mdPath = `tool-subagents/${file}`;
    const tomlPath = `tool-subagents/${agent}.toml`;
    const meta = parseFrontmatter(read(mdPath));
    if (meta.name !== agent) {
      fail(`${mdPath} frontmatter name '${meta.name || ""}' does not match file`);
    }
    if (!meta.description) {
      fail(`${mdPath} missing description`);
    }
    if (!exists(tomlPath)) {
      fail(`${tomlPath} missing`);
    } else {
      const toml = read(tomlPath);
      if (!toml.includes(`name = "${agent}"`)) {
        fail(`${tomlPath} missing matching name`);
      }
      const tomlDescription = parseTomlBasicString(toml, "description");
      if (tomlDescription === null) {
        fail(`${tomlPath} missing description`);
      } else if (meta.description && tomlDescription !== meta.description) {
        fail(`${tomlPath} description differs from ${mdPath} frontmatter description`);
      }
      const instructions = parseTomlMultilineString(toml, "developer_instructions");
      if (instructions !== null) {
        const mdBody = normalizeWhitespace(stripFrontmatter(read(mdPath)));
        if (normalizeWhitespace(instructions) !== mdBody) {
          warn(`${tomlPath} developer_instructions diverge from ${mdPath} body`);
        }
      }
      for (const target of parseTomlStringArray(toml, "can_delegate_to")) {
        if (!exists(`tool-subagents/${target}.md`)) {
          fail(`${tomlPath} can_delegate_to references nonexistent tool-subagents/${target}.md`);
        }
      }
    }
    assertContains("tool-subagents/README.md", `\`${agent}\``, `subagent catalog entry ${agent}`);
  }

  for (const providerDir of [".codex/agents", ".cursor/agents", ".claude/agents"]) {
    if (!exists(providerDir)) {
      continue;
    }
    for (const file of listFiles("tool-subagents", (name) => name.endsWith(".md") || name.endsWith(".toml"))) {
      if (!exists(`${providerDir}/${file}`)) {
        fail(`${providerDir}/${file} missing; run npm run subagents:apply -- all .`);
      }
    }
  }
  pass("subagent check completed");
}

function checkSpecialist(agent) {
  if (!/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/.test(agent)) {
    fail(`agent name must be kebab-case: ${agent}`);
    return;
  }
  const required = [
    `tool-subagents/${agent}.md`,
    `tool-subagents/${agent}.toml`,
    `skills/${agent}/SKILL.md`,
  ];
  for (const file of required) {
    if (!exists(file)) {
      fail(`${file} missing`);
    }
  }
  if (exists(`tool-subagents/${agent}.md`)) {
    const meta = parseFrontmatter(read(`tool-subagents/${agent}.md`));
    if (meta.name !== agent) {
      fail(`tool-subagents/${agent}.md frontmatter name mismatch`);
    }
    if (agent === "agent-orchestrator") {
      if (meta.readonly !== "false") {
        fail(`tool-subagents/${agent}.md should declare readonly: false for explicit LOA mode`);
      }
      assertContains(`tool-subagents/${agent}.toml`, "readonly = false", `writable LOA manifest for ${agent}`);
      assertContains(`tool-subagents/${agent}.toml`, "external_side_effects = true", `LOA side-effect capability for ${agent}`);
    } else if (meta.readonly !== "true") {
      fail(`tool-subagents/${agent}.md should declare readonly: true for validator-style specialists`);
    }
    assertContains(`tool-subagents/${agent}.md`, "## Related Specialists", `related specialist handoffs for ${agent}`);
    assertContains(`tool-subagents/${agent}.md`, "Learning/token efficiency", `learning/token efficiency output for ${agent}`);
  }
  const validationWorkflow = findCompanionWorkflow(agent, "validation");
  const evolutionWorkflow = findCompanionWorkflow(agent, "evolution");
  if (!validationWorkflow) {
    fail(`validation workflow missing for ${agent}`);
  }
  if (!evolutionWorkflow) {
    fail(`evolution workflow missing for ${agent}`);
  }
  assertContains("INTENTS.md", agent, `routing for ${agent}`);
  assertContains("AGENTS.md", `**${agent}**`, `AGENTS skill index for ${agent}`);
  assertContains("README.md", `**${agent}**`, `README skill index for ${agent}`);
  if (validationWorkflow) {
    assertContains("workflows/README.md", path.basename(validationWorkflow), `workflow index for ${agent}`);
  }
  if (evolutionWorkflow) {
    assertContains("workflows/README.md", path.basename(evolutionWorkflow), `evolution workflow index for ${agent}`);
    assertContains(`tool-subagents/${agent}.md`, evolutionWorkflow, `self-improvement workflow link for ${agent}`);
  }
  assertContains("tool-subagents/README.md", `\`${agent}\``, `subagent index for ${agent}`);
  pass(`specialist ${agent} check completed`);
}

function findCompanionWorkflow(agent, kind) {
  const standard = `workflows/${agent}-${kind}.md`;
  if (exists(standard)) {
    return standard;
  }
  const workflows = listFiles("workflows", (name) => name.endsWith(".md") && name !== "README.md");
  for (const file of workflows) {
    if (!file.includes(kind)) {
      continue;
    }
    const relative = `workflows/${file}`;
    const text = read(relative);
    if (text.includes(agent) || text.includes(`tool-subagents/${agent}.md`)) {
      return relative;
    }
  }
  return "";
}

let cachedPython;

function resolvePython() {
  if (cachedPython !== undefined) {
    return cachedPython;
  }
  cachedPython = null;
  // `which` is an executable on POSIX systems (unlike the `command` shell builtin), so no shell is needed.
  const locator = process.platform === "win32" ? "where" : "which";
  const locatorArgs = [];
  for (const candidate of [
    { command: "python3", args: [] },
    { command: "python", args: [] },
    { command: "py", args: ["-3"] },
  ]) {
    // nosemgrep: javascript.lang.security.detect-child-process.detect-child-process
    const located = spawnSync(locator, [...locatorArgs, candidate.command], {
      encoding: "utf8",
      shell: false,
    });
    if (located.error || located.status !== 0) {
      continue;
    }
    const resolvedPath = (located.stdout || "").split(/\r?\n/).find((line) => line.trim());
    if (!resolvedPath || /windowsapps/i.test(resolvedPath)) {
      continue;
    }
    // nosemgrep: javascript.lang.security.detect-child-process.detect-child-process
    const probe = spawnSync(candidate.command, [...candidate.args, "-c", "import sys"], {
      stdio: "ignore",
      shell: false,
    });
    if (!probe.error && probe.status === 0) {
      cachedPython = candidate;
      break;
    }
  }
  return cachedPython;
}

function runPython(scriptArgs) {
  const python = resolvePython();
  if (!python) {
    fail("no usable python found (tried python3, python, py -3; WindowsApps stubs rejected)");
    return;
  }
  runAllowed(python.command, [...python.args, ...scriptArgs]);
}

function runAllowed(command, args) {
  if (!["python", "python3", "py", "powershell.exe", "bash"].includes(command)) {
    fail(`refusing unexpected command: ${command}`);
    return;
  }
  // nosemgrep: javascript.lang.security.detect-child-process.detect-child-process
  const result = spawnSync(command, args, {
    cwd: ROOT,
    stdio: "inherit",
    shell: false,
  });
  if (result.error) {
    fail(`${command} failed to start: ${result.error.message}`);
    return;
  }
  if (result.status !== 0) {
    fail(`${command} ${args.join(" ")} exited ${result.status}`);
  }
}

function runToolkitScript(baseName) {
  if (!["validate-toolkit-indexes", "security-check-toolkit"].includes(baseName)) {
    fail(`refusing unexpected toolkit script: ${baseName}`);
    return;
  }
  if (process.platform === "win32") {
    runAllowed("powershell.exe", [
      "-NoProfile",
      "-ExecutionPolicy",
      "Bypass",
      "-File",
      safeRepoPath(`scripts/${baseName}.ps1`),
    ]);
  } else {
    runAllowed("bash", [safeRepoPath(`scripts/${baseName}.sh`)]);
  }
}

function checkAll() {
  checkSkillsIndex();
  checkRulesRedirects();
  checkWorkflowSizes();
  checkSubagents();
  runPython(["scripts/scan-llm-surface-security.py", "--root", "."]);
  runToolkitScript("validate-toolkit-indexes");
  if (process.env.SKIP_SECURITY_CHECK_TOOLKIT === "1") {
    // CI runners lack the external scanners the toolkit gate requires; the
    // dependency-free LLM-surface scan above still runs unconditionally.
    console.log("SKIP: security-check-toolkit (SKIP_SECURITY_CHECK_TOOLKIT=1)");
  } else {
    runToolkitScript("security-check-toolkit");
  }
}

const args = process.argv.slice(2);
if (args.length === 0 || args.includes("--help") || args.includes("-h")) {
  console.log(`Usage:
  node scripts/validate-specialist-agent.js <agent-name>
  node scripts/validate-specialist-agent.js --skills-index-check
  node scripts/validate-specialist-agent.js --rules-redirects-check
  node scripts/validate-specialist-agent.js --workflows-size-check
  node scripts/validate-specialist-agent.js --subagents-check
  node scripts/validate-specialist-agent.js --llm-security-scan
  node scripts/validate-specialist-agent.js --changed-code-quality-gate [--base=<ref>]
  node scripts/validate-specialist-agent.js --skillspector-check
  node scripts/validate-specialist-agent.js --skillspector-check-all
  node scripts/validate-specialist-agent.js --all
`);
  process.exit(0);
}

for (const arg of args) {
  if (arg === "--skills-index-check") {
    checkSkillsIndex();
  } else if (arg === "--rules-redirects-check") {
    checkRulesRedirects();
  } else if (arg === "--workflows-size-check") {
    checkWorkflowSizes();
  } else if (arg === "--subagents-check") {
    checkSubagents();
  } else if (arg === "--llm-security-scan") {
    runPython(["scripts/scan-llm-surface-security.py", "--root", "."]);
  } else if (arg === "--skillspector-check") {
    runPython(["scripts/check-skillspector-skills.py", "--changed"]);
  } else if (arg === "--skillspector-check-all") {
    runPython(["scripts/check-skillspector-skills.py", "--all"]);
  } else if (arg === "--changed-code-quality-gate") {
    const baseArg = args.find((value) => value.startsWith("--base="));
    runPython(["scripts/changed_code_quality_gate.py", ...(baseArg ? ["--base", baseArg.slice(7)] : [])]);
  } else if (arg.startsWith("--base=")) {
    continue;
  } else if (arg === "--all") {
    checkAll();
  } else if (arg.startsWith("--")) {
    fail(`unknown option: ${arg}`);
  } else {
    checkSpecialist(arg);
  }
}

if (failures > 0) {
  process.exit(1);
}
console.log("All requested specialist-agent checks passed.");
