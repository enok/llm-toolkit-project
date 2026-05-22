---
name: maven-release
description: >
  Maven release process using the maven-release-plugin. Covers release:prepare,
  release:perform, dry runs, rollback, Nexus deployment, parent POM releases,
  and downstream consumer updates. Use when cutting a Maven release, deploying
  to Nexus, tagging a version in Git, or updating child project parent versions.
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Maven Release

Structured process for releasing Maven artifacts using the `maven-release-plugin`.

## When to Apply

- Cutting a release from a SNAPSHOT version
- Deploying released artifacts to a Nexus or Maven repository
- Tagging a release version in Git
- Bumping to the next development SNAPSHOT
- Releasing a parent POM and updating downstream children
- Troubleshooting a failed or partial release

## Reference Files

| File | Description |
|------|-------------|
| [maven-release-plugin.md](references/maven-release-plugin.md) | Detailed plugin phases, commands, flags, rollback, and troubleshooting |

## Quick Reference

### Prerequisites

1. **POM requirements** — `<scm><developerConnection>` and `<distributionManagement>` must be configured.
2. **Credentials** — `~/.m2/settings.xml` must have a `<server>` entry matching the `<repository><id>` in `<distributionManagement>`.
3. **Clean workspace** — no uncommitted changes, on the correct branch (usually `main`).
4. **No SNAPSHOT dependencies** — `release:prepare` will fail if the project depends on other SNAPSHOTs.

### Core Commands

```bash
# 1. Dry run (review without committing)
mvn release:prepare -DdryRun \
  -DreleaseVersion=X.Y.Z \
  -DdevelopmentVersion=X.Y.W-SNAPSHOT \
  -Dtag=<tag-name>

# 2. Clean dry-run artifacts
mvn release:clean

# 3. Prepare (commits version change, tags, bumps to next SNAPSHOT)
mvn --batch-mode release:prepare \
  -DreleaseVersion=X.Y.Z \
  -DdevelopmentVersion=X.Y.W-SNAPSHOT \
  -Dtag=<tag-name>

# 4. Perform (checks out tag, builds, deploys to Nexus)
mvn release:perform

# 5. Rollback (if prepare succeeded but perform failed)
mvn release:rollback
```

### What release:prepare Does

1. Checks for uncommitted changes
2. Checks for SNAPSHOT dependencies
3. Rewrites POM version from `X-SNAPSHOT` → `X.Y.Z`
4. Transforms SCM URLs to point to the tag
5. Runs tests against the release POM
6. Commits the release POM
7. Tags the commit in Git
8. Bumps POM version to `X.Y.W-SNAPSHOT`
9. Commits the development POM

### What release:perform Does

1. Checks out the tagged source from SCM into `target/checkout`
2. Runs `deploy` (and optionally `site-deploy`) on the checked-out project
3. Deploys the artifact to the remote repository defined in `<distributionManagement>`

### Parent POM Releases

When releasing a parent POM:

- The released POM is deployed to Nexus as a `.pom` artifact (no JAR for `<packaging>pom</packaging>`)
- All child projects referencing the parent via `<parent><version>X-SNAPSHOT</version>` must be updated to the released version
- Update children **after** the parent artifact is confirmed in Nexus
- Each child update is a separate PR in its respective repository

### Rollback

If `release:prepare` completed but something went wrong before or during `release:perform`:

```bash
# Revert POM changes and remove tag
mvn release:rollback

# If rollback fails, manual cleanup:
git tag -d <tag-name>
git push origin :refs/tags/<tag-name>
git revert HEAD~2    # revert the 2 commits from prepare
```

### Troubleshooting

- **"Cannot run program /bin/sh"** on Windows — run from Git Bash or WSL, not CMD/PowerShell
- **Authentication failures** — verify `<server><id>` in `settings.xml` matches `<repository><id>` in POM
- **SNAPSHOT dependency detected** — resolve or release the dependency first
- **Tag already exists** — either delete the old tag or use a different tag name
