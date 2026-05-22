---
description: Cut a Maven release — prepare, perform, verify in Nexus, and update downstream client projects
---

# Maven Release Workflow

Release a Maven artifact using `maven-release-plugin`. Covers PR merge (squash), dry run, prepare, perform, Nexus verification, and downstream parent version updates.

The user provides: **release version**, **next dev version**, **tag name**, and the **list of downstream repos** to update. Replace placeholders below with those values.

---

## Phase 1 — PR Merge (Squash and Merge)

### 1. Merge the approved PR

**The PR MUST be merged by a human via the GitHub UI — never merged programmatically.** Wait for the approver to complete this step.

Merge strategy: **Squash and Merge** only — not a regular merge commit or rebase merge.

> In GitHub UI: click the merge button dropdown and select **"Squash and merge"**.

- [ ] PR has at least one human approval
- [ ] All CI checks are green
- [ ] Merge strategy is **Squash and Merge**
- [ ] PR is now closed and merged into the base branch (done by a human approver)

### 2. Pull the squashed base branch

```bash
git checkout <BASE_BRANCH>
git pull origin <BASE_BRANCH>
```

- [ ] Local base branch matches remote
- [ ] `pom.xml` version is the expected SNAPSHOT

---

## Phase 2 — Pre-flight Checks

### 3. Confirm branch and workspace

```bash
git status
git branch --show-current
```

- [ ] On the base branch (e.g., `master` or `main`)
- [ ] No uncommitted changes
- [ ] Branch is up to date with remote

### 4. Validate POM configuration

Read the project `pom.xml` and verify:

- [ ] `<version>` is the expected SNAPSHOT
- [ ] `<scm><developerConnection>` is correct
- [ ] `<distributionManagement><repository>` points to the correct Nexus releases URL
- [ ] No SNAPSHOT dependencies in `<dependencies>` or `<dependencyManagement>`

### 5. Validate Nexus credentials

```bash
grep -A3 '<id>internal-releases</id>' ~/.m2/settings.xml
```

- [ ] `<server><id>` matches `<distributionManagement><repository><id>` in the POM
- [ ] Credentials (username/password or encrypted password) are present

If credentials are missing, **stop** and ask the user to configure `~/.m2/settings.xml`.

---

## Phase 3 — Dry Run

### 6. Execute dry run

```bash
mvn release:prepare -DdryRun \
  -DreleaseVersion=<RELEASE_VERSION> \
  -DdevelopmentVersion=<NEXT_DEV_VERSION> \
  -Dtag=<TAG_NAME>
```

### 7. Review transformed POMs

Check the generated files:
- `pom.xml.tag` — the POM as it will be committed for the release (version = `<RELEASE_VERSION>`)
- `pom.xml.next` — the POM as it will be committed for next development (version = `<NEXT_DEV_VERSION>`)

Verify:
- [ ] Release version is correct in `pom.xml.tag`
- [ ] Next dev version is correct in `pom.xml.next`
- [ ] SCM tag URL looks correct in `pom.xml.tag`

### 8. Clean dry-run artifacts

```bash
mvn release:clean
```

---

## Phase 4 — Prepare Release

### 9. Run release:prepare

```bash
mvn --batch-mode release:prepare \
  -DreleaseVersion=<RELEASE_VERSION> \
  -DdevelopmentVersion=<NEXT_DEV_VERSION> \
  -Dtag=<TAG_NAME>
```

This creates **2 commits** and **1 tag** in Git:
1. Commit: `[maven-release-plugin] prepare release <TAG_NAME>` (version = `<RELEASE_VERSION>`)
2. Tag: `<TAG_NAME>` on commit #1
3. Commit: `[maven-release-plugin] prepare for next development iteration` (version = `<NEXT_DEV_VERSION>`)

### 10. Verify prepare results

```bash
git log --oneline -3
git tag -l '<TAG_NAME>'
```

- [ ] Two new commits from `[maven-release-plugin]`
- [ ] Tag `<TAG_NAME>` exists
- [ ] Current POM version is `<NEXT_DEV_VERSION>`

If anything is wrong, rollback:
```bash
mvn release:rollback
```

---

## Phase 5 — Perform Release (Deploy to Nexus)

### 11. Run release:perform

```bash
mvn release:perform
```

This:
1. Checks out the tagged source into `target/checkout`
2. Runs `mvn deploy` on the checked-out project
3. Deploys the artifact to Nexus (the `<distributionManagement>` releases repo)

> **Note**: On Windows, the antrun plugin may log a `/bin/sh` error — this is non-blocking (`failifexecutionfails="false"`). Verify the final build outcome, not individual plugin lines.

### 12. Verify deployment in Nexus

Open the Nexus releases repository in a browser or use curl:

```bash
curl -s -o /dev/null -w "%{http_code}" \
  "https://<NEXUS_HOST>/nexus/content/repositories/releases/<GROUP_PATH>/<ARTIFACT_ID>/<RELEASE_VERSION>/<ARTIFACT_ID>-<RELEASE_VERSION>.pom"
```

- [ ] HTTP 200 — artifact exists in Nexus
- [ ] Git tag is pushed to remote: `git ls-remote --tags origin | grep <TAG_NAME>`

---

## Phase 6 — Downstream Client Updates

### 13. List downstream projects

Identify all projects whose `<parent><version>` references the old SNAPSHOT. These must be updated to the released version.

### 14. Update each client project

For each downstream repo:

```bash
# Clone or navigate to the client repo
cd <client-repo>
git fetch origin
git checkout -b update-parent-<RELEASE_VERSION> origin/<BASE_BRANCH>

# Option A: Manual edit
# Change <parent><version> from SNAPSHOT to <RELEASE_VERSION> in pom.xml

# Option B: versions-maven-plugin
mvn versions:update-parent \
  -DparentVersion=<RELEASE_VERSION> \
  -DgenerateBackupPoms=false

# Verify build
mvn clean verify

# Commit and push
git add pom.xml
git commit -m "Update parent POM to <RELEASE_VERSION>"
git push origin update-parent-<RELEASE_VERSION>
```

### 15. Open PRs for each client

```bash
gh pr create --draft \
  --title "Update parent POM to <RELEASE_VERSION>" \
  --body "Parent POM released as <RELEASE_VERSION>. Updating parent version from SNAPSHOT."
```

- [ ] Each client project builds successfully against the released parent
- [ ] PRs opened for all downstream repos

---

## Phase 7 — Post-Release Verification

### 16. Final checklist

- [ ] Artifact is in Nexus releases repo
- [ ] Git tag `<TAG_NAME>` exists on remote
- [ ] Base branch has version `<NEXT_DEV_VERSION>`
- [ ] All downstream PRs are open and building green
- [ ] No `release.properties` file left in the workspace

### 17. Notify stakeholders

Inform the team that the release is available:
- Released artifact coordinates: `<groupId>:<artifactId>:<RELEASE_VERSION>`
- Nexus URL where the artifact can be found
- List of downstream PRs that need review

---

## Rollback Procedures

### If release:prepare failed or was interrupted

```bash
mvn release:clean release:prepare -Dresume=false \
  -DreleaseVersion=<RELEASE_VERSION> \
  -DdevelopmentVersion=<NEXT_DEV_VERSION> \
  -Dtag=<TAG_NAME>
```

### If release:prepare completed but release:perform failed

```bash
# Option 1: Automatic rollback
mvn release:rollback

# Option 2: Manual cleanup
git tag -d <TAG_NAME>
git push origin :refs/tags/<TAG_NAME>
git reset --hard HEAD~2
git push --force-with-lease
mvn release:clean
```

---

## Final Step — Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
