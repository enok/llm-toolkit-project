---
title: Maven Release Plugin Reference
tags: [maven, release, nexus, deploy, scm, git]
---

# Maven Release Plugin — Detailed Reference

Comprehensive reference for the `maven-release-plugin`, sourced from the official Apache Maven documentation and enriched with enterprise patterns.

## Plugin Overview

The Maven Release Plugin automates the release lifecycle in two main phases:

1. **`release:prepare`** — transforms the POM, tags in SCM, and advances to next SNAPSHOT
2. **`release:perform`** — checks out the tag and deploys to the remote repository

## POM Requirements

### SCM Configuration

```xml
<scm>
  <connection>scm:git:git@github.com:org/repo.git</connection>
  <url>https://github.com/org/repo</url>
  <developerConnection>scm:git:git@github.com:org/repo.git</developerConnection>
</scm>
```

- `developerConnection` is **required** — the plugin uses it to commit and tag
- The `scm:git:` prefix tells the plugin which SCM provider to use
- For SSH-based Git URLs, ensure SSH keys are configured and the agent is running

### Distribution Management

```xml
<distributionManagement>
  <repository>
    <id>internal-releases</id>
    <name>internal-releases</name>
    <url>https://nexus.example.com/nexus/content/repositories/releases/</url>
  </repository>
  <snapshotRepository>
    <id>internal-snapshots</id>
    <name>internal-snapshots</name>
    <url>https://nexus.example.com/nexus/content/repositories/snapshots/</url>
  </snapshotRepository>
</distributionManagement>
```

### Maven Settings (credentials)

The `<server><id>` in `~/.m2/settings.xml` must match the `<repository><id>` in the POM:

```xml
<!-- ~/.m2/settings.xml -->
<settings>
  <servers>
    <server>
      <id>internal-releases</id>
      <username>deploy-user</username>
      <password>encrypted-password</password>
    </server>
  </servers>
</settings>
```

Use `mvn --encrypt-password` to encrypt credentials.

## release:prepare — Detailed Phases

The `release:prepare` goal executes these phases in order:

| Phase | Description |
|-------|-------------|
| 1. Check local modifications | Fails if uncommitted changes exist |
| 2. Check SNAPSHOT dependencies | Fails if any dependency is a SNAPSHOT |
| 3. Transform POM for release | Changes `X-SNAPSHOT` → `X.Y.Z` |
| 4. Transform SCM info | Updates SCM URLs to point to the tag location |
| 5. Run preparation goals | Executes `clean verify` (configurable) to test the release POM |
| 6. Commit release POM | Commits the transformed POM with message `[maven-release-plugin] prepare release <tag>` |
| 7. Tag in SCM | Creates a Git tag with the configured name |
| 8. Transform POM for development | Changes version to next SNAPSHOT (`X.Y.W-SNAPSHOT`) |
| 9. Commit development POM | Commits the SNAPSHOT POM with message `[maven-release-plugin] prepare for next development iteration` |

### Key Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `-DreleaseVersion` | The release version to set | `2.0.0` |
| `-DdevelopmentVersion` | The next development version | `2.0.1-SNAPSHOT` |
| `-Dtag` | The SCM tag name | `root-2.0.0` |
| `-DdryRun` | Simulate without committing | (flag only) |
| `-Dresume=false` | Restart from scratch | (flag only) |
| `--batch-mode` / `-B` | Non-interactive mode | (flag only) |
| `-DautoVersionSubmodules=true` | All modules get parent version | (for multi-module) |
| `-DpreparationGoals` | Goals to run during prepare | Default: `clean verify` |
| `-DtagNameFormat` | Tag name pattern | `v@{project.version}` |

### Tag Name Format

The `tagNameFormat` supports these placeholders (using `@{}` to avoid premature Maven interpolation):

- `@{project.groupId}`
- `@{project.artifactId}`
- `@{project.version}` — the **release** version (not SNAPSHOT)

Default tag name: `${artifactId}-${version}` (e.g., `root-2.0.0`).

## release:perform — Detailed Phases

| Phase | Description |
|-------|-------------|
| 1. Checkout tagged source | Clones the tag into `target/checkout` |
| 2. Run perform goals | Executes `deploy` (and optionally `site-deploy`) |
| 3. Deploy artifacts | Pushes to the remote repository in `<distributionManagement>` |
| 4. Clean up | Removes `release.properties` after success |

### Key Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `-DconnectionUrl` | Override SCM URL | `scm:git:git@github.com:org/repo.git` |
| `-Dgoals` | Override perform goals | Default: `deploy` |
| `-DreleaseProfiles` | Profiles to activate | `release` |
| `-DlocalCheckout=true` | Use local repo instead of remote checkout | (faster, same machine) |

### What Gets Deployed

For a parent POM (`<packaging>pom</packaging>`):
- `groupId/artifactId/version/artifactId-version.pom` — the POM file itself
- No JAR is produced (POM-only artifact)

For a library (`<packaging>jar</packaging>`):
- The JAR file
- The POM file
- Sources JAR (if `maven-source-plugin` is configured)
- Javadoc JAR (if `maven-javadoc-plugin` is configured)

## Batch Mode (Non-Interactive)

For scripted or CI-driven releases, use `--batch-mode` with explicit version parameters:

```bash
mvn --batch-mode release:prepare \
  -DreleaseVersion=2.0.0 \
  -DdevelopmentVersion=2.0.1-SNAPSHOT \
  -Dtag=root-2.0.0
```

Without `--batch-mode`, the plugin prompts interactively for:
1. Release version (default: current version minus `-SNAPSHOT`)
2. SCM tag name (default: `${artifactId}-${releaseVersion}`)
3. Next development version (default: incremented patch + `-SNAPSHOT`)

## Dry Run

Always do a dry run first, especially for first-time releases:

```bash
mvn release:prepare -DdryRun \
  -DreleaseVersion=2.0.0 \
  -DdevelopmentVersion=2.0.1-SNAPSHOT \
  -Dtag=root-2.0.0
```

This creates files with `.tag` and `.next` suffixes for review without committing. Clean up with:

```bash
mvn release:clean
```

## Rollback

### Automatic Rollback

If `release:prepare` completed but something went wrong:

```bash
mvn release:rollback
```

This reverts the POM changes and removes the tag. The `release.properties` file must still exist.

### Manual Rollback

If automatic rollback fails:

```bash
# Delete the Git tag locally and remotely
git tag -d <tag-name>
git push origin :refs/tags/<tag-name>

# Revert the 2 commits created by release:prepare
git revert HEAD~2..HEAD

# Or hard reset if the commits are the latest
git reset --hard HEAD~2
git push --force-with-lease

# Clean release artifacts
mvn release:clean
```

## Troubleshooting

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| `Cannot run program "/bin/sh"` | Windows environment | Use Git Bash or WSL |
| `Unable to tag SCM` | Tag already exists | Delete old tag or use different name |
| `There are still some missing releases` | SNAPSHOT dependencies | Release or pin dependencies first |
| `401 Unauthorized` on deploy | Bad Nexus credentials | Check `settings.xml` server ID matches POM |
| `409 Conflict` on deploy | Artifact already exists in releases repo | Nexus releases repos are usually immutable; use a new version |
| `The working copy is not clean` | Uncommitted changes | Commit or stash changes first |

### Windows-Specific Issues

- The `maven-antrun-plugin` may invoke `/bin/sh` for version.properties generation — this is expected to fail on Windows but does not block the release (the antrun task has `failifexecutionfails="false"`)
- Prefer running Maven release commands from Git Bash to ensure Git operations work correctly
- Verify `core.autocrlf` settings do not cause unexpected file modifications

### Plugin Version Compatibility

| Plugin Version | Minimum Maven | Notes |
|----------------|---------------|-------|
| 2.1 | Maven 2.x+ | Legacy, widely used in enterprise |
| 2.5.x | Maven 3.x+ | Last 2.x line, stable |
| 3.x | Maven 3.8.8+ | Major rewrite, different default behavior |

When upgrading from 2.x to 3.x, note that 3.x no longer activates a default release profile. See the [migration guide](https://maven.apache.org/maven-release/maven-release-plugin/migrate.html).

## Parent POM Release Pattern

Releasing a parent POM follows the same `prepare` → `perform` cycle but has additional downstream considerations:

1. **Pre-release**: Ensure all child projects build against the current SNAPSHOT parent
2. **Release**: Run `release:prepare` + `release:perform` on the parent POM repo
3. **Verify**: Confirm the POM artifact is in the Nexus releases repository
4. **Downstream update**: Update each child project's `<parent><version>` from SNAPSHOT to the released version
5. **Child PRs**: Open PRs in each child repo with the parent version update
6. **Child verification**: Each child project must build successfully against the released parent

### Downstream Update Example

In each child project's `pom.xml`:

```xml
<!-- Before -->
<parent>
  <groupId>com.example</groupId>
  <artifactId>parent-pom</artifactId>
  <version>2.0-SNAPSHOT</version>
</parent>

<!-- After -->
<parent>
  <groupId>com.example</groupId>
  <artifactId>parent-pom</artifactId>
  <version>2.0.0</version>
</parent>
```

Or use the `versions-maven-plugin`:

```bash
mvn versions:update-parent -DparentVersion=2.0.0 -DgenerateBackupPoms=false
```
