---
name: llm-toolchain-provisioning
description: Capture, review, and restore the set of LLM assistant extensions installed on a workstation — Claude Code plugins and marketplaces, Cursor and Windsurf extensions, Codex and Gemini configuration — as a portable manifest. This skill should be used when onboarding a new machine or teammate, reproducing another developer's assistant setup, auditing which extensions are installed and where they came from, or diagnosing why an assistant behaves differently across machines.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.0.0"
---

# LLM Toolchain Provisioning

Assistant extensions — Claude Code plugins, Cursor and Windsurf extensions, Codex and Gemini config — are installed per workstation and recorded in per-tool state files that no repository tracks. That state is invisible to code review and silently divergent between machines, so "it works on my machine" for an agent workflow is usually an extension the other machine never installed.

This skill treats that state as a reproducible input: export it to a manifest, review the manifest as evidence, and restore it elsewhere.

## When to Apply

- Onboarding a new workstation or teammate and needing the same assistant capabilities.
- An agent workflow behaves differently on two machines and the extension set is suspect.
- Auditing what is installed, at what version, and from which upstream source.
- Before a machine rebuild or OS reinstall, to capture the current toolchain.
- Reviewing whether an installed extension is first-party, vendor, or organization-published.

## The Manifest Is Generated, Never Committed

A manifest records one workstation's state: absolute install paths, pinned commit SHAs, enablement flags, and the operator's own tool selection. None of that is shared project configuration, and committing it invites three failures — it drifts the moment anyone installs anything, it pins other developers to one person's choices, and paths that are valid on one host are wrong everywhere else.

Write the manifest to a path the repository ignores, or outside the repository entirely. Share it as an artifact (attachment, bucket object, onboarding ticket) when reproducing a setup. What belongs in version control is this skill and its scripts — the *procedure* — not the captured state.

## Read the Source of Truth, Not the Cache

Every assistant keeps several overlapping records of what is installed, and they disagree routinely. Distinguish them before trusting any one:

- **Installed** — the inventory of what is present on disk, with version or commit pin.
- **Enabled** — a separate flag set. An extension can be installed and disabled, or enabled and missing; neither state is an error, and only the pair explains observed behavior.
- **Registered sources** — the marketplaces or registries the tool will install from, independent of what has been installed from them.
- **Catalog cache** — a snapshot of what is *available* upstream. Never treat it as installed state; it is the largest file and the least meaningful.
- **Transient clone directories** — in-progress checkout scratch space from an interrupted install. Exclude them; the tool recreates and cleans them.

Report the installed/enabled pair together. An inventory that lists only what is on disk will misexplain a machine where half the extensions are switched off.

## Distinguish Upstream Content From Local Authorship

Before treating an extension set as something to migrate into a repository, establish where each item came from. The distinction decides whether there is anything to migrate at all:

- **Upstream, pinned** — installed from a public or vendor registry at a recorded version or commit. Reproduce by re-installing at that pin. Copying the content into a repository vendors third-party code, taking on drift and maintenance for no gain.
- **Organization-published** — installed from an internal registry or bucket. Reproduce by registering that source; publish new organization capabilities *there*, not into an unrelated repository.
- **Locally authored** — written by hand on this machine and present in no registry. This is the only category that genuinely needs a home in version control, and it is usually far smaller than the raw extension count suggests.

Run this classification before proposing a migration. An inventory of dozens of extensions that are all upstream means the correct deliverable is a pin list, not a copy.

## Symlinks Are Already-Tracked Content

An extension directory that is a symlink or junction into a git working copy is not workstation state — it is a checkout of a repository that already has history. Record the repository and revision it points to and stop there; copying through the link duplicates tracked content into a second place, and following it during a recursive delete destroys the target.

Check for reparse points before any recursive removal, and resolve links before computing sizes so shared targets are not counted repeatedly.

## Normalize Aliases Across Config Layers

The same registry is frequently recorded under different names by different layers — a centrally managed policy file and the local state file often disagree on casing or use a short alias. Key the manifest on the **source URL**, which is stable, and carry names as metadata. Report alias mismatches as findings: they are harmless until someone writes automation that matches on the name.

Centrally managed configuration is also authoritative and not yours to rewrite. Read it, record what it declares, and if it registers a source that is not installed, surface that as a finding rather than installing on your own initiative.

## Restore Is a Proposal, Not an Action

Restoration installs software and mutates the operator's tooling, so the default is a plan the operator approves:

1. **Diff first.** Report what the manifest declares against what is present: missing, extra, version-mismatched, source-mismatched.
2. **Never remove by default.** An extension present on the machine but absent from the manifest is almost always a deliberate local addition, not drift to clean up. Report extras; remove only on an explicit instruction naming them.
3. **Install at the recorded pin**, not at latest. "Reproduce the setup" means the recorded version; a floating install produces a different machine and hides the drift being diagnosed.
4. **Register sources before installing** from them, and expect authenticated private registries to need credentials the manifest must never contain.
5. **Re-export and compare** after restoring. The post-restore manifest should match the input; anything that did not take is a finding, not a rounding error.

Credentials, tokens, and signed URLs are out of scope for both directions. Redact any value that looks like one on export, and require the operator to supply it at restore time.

## Scripts

Both entrypoints wrap the same portable implementation, per `rules/cross-platform-scripts.md`:

| Task | Portable entrypoint | Windows wrapper |
|---|---|---|
| Export a manifest | `python scripts/export_toolchain.py --out <path>` | `scripts/Export-Toolchain.ps1 -Out <path>` |
| Diff / plan a restore | `python scripts/restore_toolchain.py --manifest <path>` | `scripts/Restore-Toolchain.ps1 -Manifest <path>` |
| Apply a restore | add `--apply` (prints the commands it would run without it) | add `-Apply` |

Export is read-only. Restore defaults to a dry-run diff and prints the exact install commands rather than shelling out blind, so the operator can inspect them.

## Related

- `rules/cross-platform-scripts.md` — portability requirements these scripts follow.
- `rules/external-write-authorization.md` — authorization gate for mutating an operator's environment.
- `skills/local-env-bootstrap/SKILL.md` — repository and runtime setup, the project-side counterpart to this workstation-side skill.
- `skills/external-skill-intake/SKILL.md` — evaluating and adapting a capability sourced from a public registry.
