---
description: Diagnose local environment, auth, dependency, and container issues safely
---

# Environment diagnose workflow

Use for local setup failures, broken builds, missing auth, or service boot issues.

## Skill handoffs

- Setup or repair procedure needed -> `skills/local-env-bootstrap/SKILL.md`.
- Maven, OWASP dependency-check, Jetty/Tomcat, or Java webapp startup failures -> `skills/maven-build-troubleshooting/SKILL.md`.
- First-time machine setup (installing CLIs/binaries) -> `scripts/bootstrap-dev.sh` / `scripts/bootstrap-dev.ps1`.

## Steps

1. Classify the failure surface: toolchain, auth, containers or local services, dependency install, build cache, or repo-specific setup.
2. Gather concrete evidence first, per surface:
   - toolchain: `git --version`, `node --version`, `python --version` / `python3 --version`, `java -version`, `mvn -version`, `bash --version` (>= 4.4 needed by toolkit sync scripts; stock macOS ships 3.2 — `brew install bash`);
   - auth: `gh auth status`, `acli jira auth status`, `aws sts get-caller-identity`;
   - containers/services: `docker ps` or the service's own health endpoint; port conflicts via `netstat`/`Get-NetTCPConnection`;
   - dependency install/build cache: the failing command's full output, lockfile presence, and cache paths.
3. Once the failure surface is known, split independent environment checks **immediately by default**.
4. Do not pause before internal fanout unless there is a user-visible tradeoff or risky external side effect.
5. Cluster likely causes and test the lowest-risk fixes first.
6. Re-run the failing workflow and confirm the environment is healthy before stopping.

See `rules/multi-agent-orchestration.md`.

## Report contract

Close with: root cause (with evidence), fix applied (exact commands/edits), verification command that now passes, and anything left unverified.

---

## Final Step — Self-improvement

Run the **self-improvement** workflow (`workflows/self-improvement.md`) before closing this workflow.
