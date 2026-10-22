# Architecture diagrams

Diagrams of the agent orchestrator and of the toolkit around it. Each figure ships as Mermaid source (`.mmd`, diffable), a vector `.svg` and a high-resolution `.png`; the `.svg` and `.png` are rendered from the `.mmd`, so edit the source and re-render.

| Figure | Files | What it shows | Used in |
| --- | --- | --- | --- |
| Fig 1, full | `fig1-orchestrator-architecture.{mmd,svg,png}` | The whole orchestrator: rules and router, thin root, three model tiers, validator loop, ledger, write gate, retrospective | Root `README.md`, long-form articles |
| Fig 1, hero | `fig1-orchestrator-hero.{mmd,svg,png}` | Nine-node summary of Fig 1 for small frames | Social and preview images |
| Fig 2 | `fig2-daily-job-scan.{mmd,svg,png}` | A scheduled job-search scan: lanes search and check, the root writes the tracker, rows are submitted only after the owner approves them | Long-form articles |
| Fig 3 | `fig3-one-source-many-tools.{mmd,svg,png}` | One canonical source linked or exported to the paths of eight tools | Long-form articles |

## Fig 1, full

Alt text: Agent-orchestrator flow: a prompt passes AGENTS.md rules and the INTENTS.md router to a thin root, which tiers tasks to haiku, sonnet or opus lanes, validates returns, keeps TASKS_TABLE.md and CONTEXT_STATE.md, and gates external writes.

Caption: Figure 1. The orchestrator in full: one thin root routes and tiers tasks, lanes return evidence, a validator loop checks it, and the root owns every write. Green = root, light orange = rules, routing and process steps, orange = lanes and validator, blue = ledger; thick = main path, dashed = read, feedback or optional.

## Fig 1, hero

Alt text: Simplified orchestrator flow: a prompt passes AGENTS.md rules and the INTENTS.md router to a thin root, which sends light, standard and deep tasks to lanes and a validator; the root writes and keeps a ledger; external writes need user instruction.

Caption: Figure 1 (summary). Prompt, rules and router, thin root, three model tiers, validator, root write and the write gate; the ledger sits beside the root. Green = root, orange = lanes and validator, blue = ledger; dashed = read.

## Fig 2, daily job scan

Alt text: Daily job scan flow: a schedule starts the root, which builds a known-ids list, runs inbox, board-search and board-status lanes, re-checks and appends postings, submits only rows the owner approved earlier, and sends a digest every run.

Caption: Figure 2. The daily job scan: lanes search and check, the root writes the tracker, and a row is submitted only on the next run after the owner marks it approved. Green = root, orange = lanes, blue = tracker_ops calls; dashed = digest.

## Fig 3, one source, many tools

Alt text: One source, many tools: canonical rules, workflows, skills, agent prompts and learnings feed per-repo and per-machine scripts, which write the paths of eight tools: Claude Code, Codex, Cursor, Windsurf, Copilot, Gemini CLI, OpenCode, Antigravity.

Caption: Figure 3. One source, many tools: shared assets (blue) are linked or exported by per-repo and per-machine scripts (orange) onto each tool's own paths (dashed boxes); thick = per repo, dashed = per machine. Per machine installs only skills/ and tool-subagents/; rules/ and workflows/ are linked for Cursor and Windsurf, and concatenated into Copilot's instructions file.

## Regenerate

Needs mermaid-cli (`mmdc`); the border step needs ImageMagick. Run from this folder, with `<name>` the file stem:

```bash
mmdc -i <name>.mmd -o <name>.svg -b white -w 2400
mmdc -i <name>.mmd -o <name>.png -b white -w 2400 -s 3    # hero: -s 4
magick <name>.png -bordercolor white -border 72 <name>.png    # optional; hero: 96
```

- The `.mmd` sources follow `skills/diagram-authoring/references/publication-diagram-style.md` plus two keys: `htmlLabels: false` at the top level and `flowchart.wrappingWidth`. Together they make SVG labels real `<text>` (no `foreignObject`) and keep long names such as `CONTEXT_STATE.md` on one line.
- The committed files were rendered with mermaid-cli 11.16.0. Path coordinates in the committed SVGs are rounded to two decimals; a fresh render keeps the full-precision fractions.
- PNG anti-aliasing is not byte-deterministic between renders: review a re-render by eye, not by hash.
