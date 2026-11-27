#!/usr/bin/env node
"use strict";

const { spawnSync } = require("child_process");
const fs = require("fs");
const os = require("os");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const { REQUIRED_TOML_FIELDS, renderCodexToml, renderCodexDir } = require("./subagent-render");
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
    assertContains("skills/README.md", `**${skill}**`, `skill index entry ${skill}`);
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
  for (const dir of [".windsurf/rules", ".windsurf/workflows", ".cursor/rules"]) {
    if (!exists(dir)) {
      // Provider overlays are generated links (gitignored); a fresh clone has none until sync runs.
      warn(`provider rules/workflows overlay missing: ${dir} (run ./scripts/sync-tool-configs.sh . --skip-agents-md --skip-github)`);
    }
  }
  pass("rules redirect/client overlay check completed");
}

const VALID_SUBAGENT_MODELS = new Set(["inherit", "haiku", "sonnet", "opus"]);
const VALID_SUBAGENT_TIERS = new Set(["light", "standard", "deep"]);

function checkSubagents() {
  for (const file of listFiles("tool-subagents", (name) => name.endsWith(".md") && name !== "README.md")) {
    const agent = file.replace(/\.md$/, "");
    const mdPath = `tool-subagents/${file}`;
    const meta = parseFrontmatter(read(mdPath));
    if (meta.name !== agent) {
      fail(`${mdPath} frontmatter name '${meta.name || ""}' does not match file`);
    }
    if (!meta.description) {
      fail(`${mdPath} missing description`);
    }
    if (!VALID_SUBAGENT_MODELS.has(meta.model)) {
      fail(`${mdPath} frontmatter model '${meta.model || ""}' must be one of inherit|haiku|sonnet|opus`);
    }
    if (meta.tier !== undefined && !VALID_SUBAGENT_TIERS.has(meta.tier)) {
      fail(`${mdPath} frontmatter tier '${meta.tier}' must be one of light|standard|deep`);
    }
    // The Codex TOML is generated from the .md (never committed): the check is
    // that the .md renders and carries every required TOML field.
    const rendered = renderCodexToml(read(mdPath), agent);
    if (rendered.error) {
      fail(`${mdPath} cannot be rendered to Codex TOML: ${rendered.error}`);
    } else {
      for (const field of REQUIRED_TOML_FIELDS) {
        if (tomlValueAfterKey(rendered.toml, field) === null) {
          fail(`${mdPath} renders without required TOML field ${field}`);
        }
      }
      const description = parseTomlBasicString(rendered.toml, "description");
      if (description !== meta.description) {
        fail(`${mdPath} description does not survive the TOML render`);
      }
    }
    assertContains("tool-subagents/README.md", `\`${agent}\``, `subagent catalog entry ${agent}`);
  }

  const canonicalReal = realpathOrNull(safeRepoPath("tool-subagents"));

  // Render in a temp dir and compare with the generated folder when present
  // (CI has none: rendering alone proves the sources are renderable).
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), "codex-agents-"));
  try {
    const result = renderCodexDir(safeRepoPath("tool-subagents"), tempRoot);
    for (const error of result.errors) {
      fail(`Codex render failed: ${error}`);
    }
    for (const generatedDir of ["tool-subagents/.generated/codex", ".codex/agents"]) {
      if (!exists(generatedDir)) {
        continue;
      }
      const generatedReal = realpathOrNull(safeRepoPath(generatedDir));
      if (canonicalReal && generatedReal && generatedReal === canonicalReal) {
        continue; // legacy link onto tool-subagents/: nothing generated to compare
      }
      for (const file of fs.readdirSync(tempRoot)) {
        const generatedFile = path.join(safeRepoPath(generatedDir), file);
        if (!fs.existsSync(generatedFile)) {
          fail(`${generatedDir}/${file} missing; run npm run subagents:render`);
        } else if (fs.readFileSync(generatedFile, "utf8") !== fs.readFileSync(path.join(tempRoot, file), "utf8")) {
          fail(`${generatedDir}/${file} is stale; run npm run subagents:render`);
        }
      }
    }
  } finally {
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }

  const providerExpectations = [
    { dir: ".cursor/agents", extension: ".md" },
    { dir: ".claude/agents", extension: ".md" },
  ];
  for (const { dir: providerDir, extension } of providerExpectations) {
    if (!exists(providerDir)) {
      continue;
    }
    const providerReal = realpathOrNull(safeRepoPath(providerDir));
    if (canonicalReal && providerReal && providerReal === canonicalReal) {
      // A provider directory that is itself a symlink/junction onto
      // tool-subagents/ is canonical by construction; nothing to render.
      continue;
    }
    for (const file of listFiles("tool-subagents", (name) => name.endsWith(extension))) {
      if (!exists(`${providerDir}/${file}`)) {
        fail(`${providerDir}/${file} missing; run npm run subagents:apply -- all .`);
      }
    }
  }
  pass("subagent check completed");
}

function realpathOrNull(target) {
  try {
    return fs.realpathSync.native(target);
  } catch (_err) {
    return null;
  }
}

function checkSpecialist(agent) {
  if (!/^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$/.test(agent)) {
    fail(`agent name must be kebab-case: ${agent}`);
    return;
  }
  // A missing skill twin passes only when the value-check ledger records its
  // removal; otherwise the twin and its index entries are required.
  const removed = removedLedgerPaths();
  const twinRemoved = !exists(`skills/${agent}`)
    && (removed.has(`skills/${agent}`) || removed.has(`skills/${agent}/SKILL.md`));
  const required = [`tool-subagents/${agent}.md`];
  if (!twinRemoved) {
    required.push(`skills/${agent}/SKILL.md`);
  }
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
      const rendered = renderCodexToml(read(`tool-subagents/${agent}.md`), agent);
      const toml = rendered.toml || "";
      if (!toml.includes("readonly = false")) {
        fail(`rendered Codex TOML for ${agent} lacks the writable LOA manifest (readonly = false)`);
      }
      if (!toml.includes("external_side_effects = true")) {
        fail(`rendered Codex TOML for ${agent} lacks the LOA side-effect capability`);
      }
    } else if (meta.readonly !== "true") {
      fail(`tool-subagents/${agent}.md should declare readonly: true for validator-style specialists`);
    }
    assertContains(`tool-subagents/${agent}.md`, "## Related Specialists", `related specialist handoffs for ${agent}`);
    assertContains(`tool-subagents/${agent}.md`, "Learning/token efficiency", `learning/token efficiency output for ${agent}`);
  }
  // A missing companion workflow passes only when the ledger records the
  // removal of that workflow; when one exists it must be indexed and linked.
  const validationWorkflow = findCompanionWorkflow(agent, "validation");
  const evolutionWorkflow = findCompanionWorkflow(agent, "evolution");
  if (!validationWorkflow && !companionRemoved(agent, "validation", removed)) {
    fail(`validation workflow missing for ${agent}`);
  }
  if (!evolutionWorkflow && !companionRemoved(agent, "evolution", removed)) {
    fail(`evolution workflow missing for ${agent}`);
  }
  assertContains("INTENTS.md", agent, `routing for ${agent}`);
  if (!twinRemoved) {
    assertContains("skills/README.md", `**${agent}**`, `skills catalog index for ${agent}`);
    assertContains("README.md", `**${agent}**`, `README skill index for ${agent}`);
  }
  if (validationWorkflow) {
    assertContains("docs/catalog/workflows.md", path.basename(validationWorkflow), `workflow index for ${agent}`);
  }
  if (evolutionWorkflow) {
    assertContains("docs/catalog/workflows.md", path.basename(evolutionWorkflow), `evolution workflow index for ${agent}`);
    assertContains(`tool-subagents/${agent}.md`, evolutionWorkflow, `evolution workflow link for ${agent}`);
  }
  assertContains("tool-subagents/README.md", `\`${agent}\``, `subagent index for ${agent}`);
  pass(`specialist ${agent} check completed`);
}

const LEDGER = "docs/llm/value-checks.csv";
let cachedRemoved;

// Paths whose ledger decision is `remove`. The resource is the first CSV field
// and the decision the tenth; the note field may hold quoted commas, so only
// the unquoted leading fields are split.
function removedLedgerPaths() {
  if (cachedRemoved !== undefined) {
    return cachedRemoved;
  }
  cachedRemoved = new Set();
  if (!exists(LEDGER)) {
    return cachedRemoved;
  }
  const lines = read(LEDGER).split(/\r?\n/).slice(1);
  for (const line of lines) {
    const fields = line.split(",");
    if (fields.length >= 10 && !fields.slice(0, 10).some((field) => field.startsWith('"')) && fields[9] === "remove") {
      cachedRemoved.add(fields[0]);
    }
  }
  return cachedRemoved;
}

// Companion workflows whose file name does not follow `<agent>-<kind>.md`.
const COMPANION_ALIASES = {
  "java-change-validator/evolution": "workflows/java-validator-evolution.md",
};

// A missing companion passes only when the ledger has a `remove` row for its
// exact path: `workflows/<agent>-<kind>.md`, or the alias listed above.
function companionRemoved(agent, kind, removed) {
  const target = COMPANION_ALIASES[`${agent}/${kind}`] || `workflows/${agent}-${kind}.md`;
  return removed.has(target) && !exists(target);
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
