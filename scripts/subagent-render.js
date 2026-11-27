"use strict";
// Renders the Codex agent TOML from the canonical tool-subagents/<name>.md
// source. The TOML is a generated artifact (tool-subagents/.generated/codex/,
// gitignored); it is never committed.

const fs = require("fs");
const path = require("path");

const REQUIRED_TOML_FIELDS = ["name", "description", "developer_instructions"];

function splitFrontmatter(text) {
  const match = text.replace(/\r\n/g, "\n").match(/^---\n([\s\S]*?)\n---\n/);
  if (!match) {
    return { meta: {}, body: text.replace(/\r\n/g, "\n"), hasFrontmatter: false };
  }
  const meta = {};
  for (const line of match[1].split("\n")) {
    const colon = line.indexOf(":");
    if (colon === -1) {
      continue;
    }
    meta[line.slice(0, colon).trim()] = line.slice(colon + 1).trim().replace(/^["']|["']$/g, "");
  }
  return { meta, body: text.replace(/\r\n/g, "\n").slice(match[0].length), hasFrontmatter: true };
}

function tomlBasicString(value) {
  // JSON string escapes are a valid subset of TOML basic-string escapes.
  return JSON.stringify(value);
}

function tomlMultilineBody(body) {
  const escaped = body
    .replace(/\\/g, "\\\\")
    .replace(/"""/g, '\\"\\"\\"')
    .replace(/[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/g, (ch) => `\\u${ch.charCodeAt(0).toString(16).padStart(4, "0")}`);
  return `"""\n${escaped}"""`;
}

// Returns { toml } or { error } so callers (apply and check) share one path.
function renderCodexToml(mdText, expectedName) {
  const { meta, body, hasFrontmatter } = splitFrontmatter(mdText);
  if (!hasFrontmatter) {
    return { error: "missing YAML frontmatter" };
  }
  if (!meta.name) {
    return { error: "frontmatter is missing name" };
  }
  if (expectedName && meta.name !== expectedName) {
    return { error: `frontmatter name '${meta.name}' does not match file name '${expectedName}'` };
  }
  if (!meta.description) {
    return { error: "frontmatter is missing description" };
  }
  const instructions = body.replace(/^\n+/, "").replace(/\s+$/, "");
  if (!instructions) {
    return { error: "prompt body is empty" };
  }
  const lines = [`name = ${tomlBasicString(meta.name)}`, `description = ${tomlBasicString(meta.description)}`];
  // The Codex file carries only the keys Codex agent files are known to use.
  // `readonly` is emitted only when the .md declares `codex_readonly`; the
  // toolkit-side `readonly` / `external_side_effects` contract stays in the .md.
  if (meta.codex_readonly === "true" || meta.codex_readonly === "false") {
    lines.push(`readonly = ${meta.codex_readonly}`);
  }
  lines.push(`developer_instructions = ${tomlMultilineBody(`${instructions}\n`)}`);
  return { toml: `${lines.join("\n")}\n` };
}

function listAgentSources(sourceRoot) {
  return fs
    .readdirSync(sourceRoot)
    .filter((entry) => entry.endsWith(".md") && entry !== "README.md")
    .sort();
}

// Renders every agent into outDir. Returns { rendered, changed, errors }.
// A ".generated" folder ignores itself: a one-line .gitignore inside it keeps
// the rendered files out of git without a root .gitignore entry.
function ignoreGeneratedDir(outDir) {
  let dir = path.resolve(outDir);
  while (path.basename(dir) !== ".generated") {
    const parent = path.dirname(dir);
    if (parent === dir) {
      return;
    }
    dir = parent;
  }
  const marker = path.join(dir, ".gitignore");
  if (!fs.existsSync(marker)) {
    fs.writeFileSync(marker, "*\n");
  }
}

// Writes only files whose content changes. With dryRun nothing is written.
function renderCodexDir(sourceRoot, outDir, options = {}) {
  const errors = [];
  let rendered = 0;
  let changed = 0;
  if (!options.dryRun) {
    fs.mkdirSync(outDir, { recursive: true });
    ignoreGeneratedDir(outDir);
  }
  for (const entry of listAgentSources(sourceRoot)) {
    const name = entry.replace(/\.md$/, "");
    const result = renderCodexToml(fs.readFileSync(path.join(sourceRoot, entry), "utf8"), name);
    if (result.error) {
      errors.push(`tool-subagents/${entry}: ${result.error}`);
      continue;
    }
    rendered += 1;
    const destination = path.join(outDir, `${name}.toml`);
    let current = null;
    try {
      current = fs.readFileSync(destination, "utf8");
    } catch (_err) {
      current = null;
    }
    if (current !== result.toml) {
      changed += 1;
      if (!options.dryRun) {
        fs.writeFileSync(destination, result.toml);
      }
    }
  }
  return { rendered, changed, errors };
}

module.exports = { REQUIRED_TOML_FIELDS, renderCodexToml, renderCodexDir, listAgentSources, splitFrontmatter };
