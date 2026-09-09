# Jenkins Integration

Check job and build status, read console logs, and trigger builds from any LLM agent.

---

## Option 1: Jenkins CLI (`jenkins-cli.jar`) - Recommended

The Jenkins CLI is served by your Jenkins controller, so it always matches the server version. Requires Java 11+.

### Install

Download the jar from the Jenkins controller:

```bash
curl -fsSL -o jenkins-cli.jar "$JENKINS_URL/jnlpJars/jenkins-cli.jar"
```

Verify: `java -jar jenkins-cli.jar -s "$JENKINS_URL" version`

### Authenticate

The CLI reads these environment variables (native Jenkins convention):

| Variable | Purpose |
|----------|---------|
| `JENKINS_URL` | Base URL of the Jenkins controller |
| `JENKINS_USER_ID` | Your Jenkins username |
| `JENKINS_API_TOKEN` | API token from `<JENKINS_URL>/user/<username>/configure` |

Store them per project secret conventions - `.env` (gitignored) locally, secret manager elsewhere; see `skills/security/rules/secrets-no-hardcoded.md`. Never print the token in chat, logs, or command echoes.

Verify auth:

```bash
java -jar jenkins-cli.jar -s "$JENKINS_URL" who-am-i
```

### Common Commands

```bash
# List jobs (optionally inside a folder)
java -jar jenkins-cli.jar -s "$JENKINS_URL" list-jobs
java -jar jenkins-cli.jar -s "$JENKINS_URL" list-jobs <FOLDER>

# Read console output of a build (what the agent typically uses)
java -jar jenkins-cli.jar -s "$JENKINS_URL" console <JOB_NAME> <BUILD_NUMBER>

# Trigger a parameterized build and follow output
java -jar jenkins-cli.jar -s "$JENKINS_URL" build <JOB_NAME> -p KEY=VALUE -f -v

# Inspect job configuration (XML)
java -jar jenkins-cli.jar -s "$JENKINS_URL" get-job <JOB_NAME>
```

Tail or limit console output before adding it to context - full build logs are large.

### Agent Detection and Setup

When the agent needs Jenkins and the CLI is not available:

1. **Detect:** Check `jenkins-cli.jar` exists and `java -version` works. If not, CLI is not set up.
2. **Install if missing:** Offer the `curl` download command above (requires `JENKINS_URL`).
3. **Authenticate if needed:** If `who-am-i` fails, guide the user to create an API token and set the three env vars.
4. **Fallback:** Use the REST API (Option 2), or ask the user to paste the build log / job status.

### Guardrails

- Status checks and log reads are safe by default.
- **Triggering builds, and especially deploy/release jobs, requires explicit user approval first** - same rule as other mutating actions in this toolkit.

---

## Option 2: REST API (Fallback)

Jenkins exposes JSON endpoints; API-token auth avoids CSRF crumb handling.

```bash
# Last build status of a job
curl -fsSL --user "$JENKINS_USER_ID:$JENKINS_API_TOKEN" \
  "$JENKINS_URL/job/<JOB_NAME>/lastBuild/api/json?tree=number,result,timestamp,durationMillis"

# Console text of a specific build
curl -fsSL --user "$JENKINS_USER_ID:$JENKINS_API_TOKEN" \
  "$JENKINS_URL/job/<JOB_NAME>/<BUILD_NUMBER>/consoleText"

# Trigger a parameterized build
curl -fsSL -X POST --user "$JENKINS_USER_ID:$JENKINS_API_TOKEN" \
  "$JENKINS_URL/job/<JOB_NAME>/buildWithParameters" --data "KEY=VALUE"
```

Use `?tree=` filters to keep responses small.

---

## Option 3: User Paste (No setup)

If neither CLI nor REST is available, ask the user to paste the job status or the relevant portion of the console log.

---

## Typical Agent Uses

- **CI status for a change** - check the job for a branch/PR when CI runs on Jenkins instead of (or in addition to) GitHub checks
- **Build failure triage** - pull the failing build's console tail, then apply `skills/maven-build-troubleshooting/SKILL.md` for Maven diagnostics
- **Release verification** - confirm the release/deploy job result after release workflows complete

---

## Pipeline Authoring Notes

Durable-task shell steps (`sh`, `bat`, `powershell`) create a `<dir>@tmp/` control directory next to the step's working directory. Running a step inside `dir('some/nested/path')` therefore drops `some/nested/path@tmp/` **inside the checked-out Git worktree** - a strict pre-apply workspace-integrity guard correctly treats those untracked files as a mutation and stops otherwise clean runs (common with nested Terraform roots). Excluding `@tmp` from the guard weakens the guarantee that every in-repository mutation stops the run; keep the guard strict and move the temp directory instead.

- Launch every shell for such steps from the workspace root, so durable-task files land in the sibling `${WORKSPACE}@tmp` directory outside Git scope.
- Change directory **inside the shell** with an anchored, validated path, immune to `CDPATH` redirection:

  ```sh
  CDPATH='' cd -- './terraform/stage' || exit 1
  ```

- Use the same wrapper for every command that must share that working root (for example AWS account/STS checks and the Terraform commands they gate), so verification and execution cannot diverge.
- Regression-test both sides: sibling `${WORKSPACE}@tmp` residue must pass the integrity guard, while identically named residue inside the Git tree must fail. Include a test with a hostile `CDPATH` to prove it cannot redirect the working directory or pollute captured stdout.

## Approving Short-Lived Pipeline Input Gates

Some Pipeline `input` steps stay open only seconds. Two facts decide success:

1. **`wfapi/pendingInputActions` is not authoritative** on every Jenkins/plugin combination - it can return an empty array while the gate is live. The build's core `InputAction.executions` collection is the direct record of live input steps; poll the build API for `actions[_class,waitingForInput,executions[id,settled,input[message,parameters]]]` and select an **unsettled** execution only after validating its exact message and expected parameter shape.
2. **Round-trip latency kills short gates.** Splitting trigger, queue resolution, watching, and approval across separate agent or tool turns can spend the entire window. Run trigger, discovery, and approval in one uninterrupted process:
   - Prepare authenticated request configuration and fetch the Jenkins crumb **before** triggering.
   - POST the build trigger, then poll the queue at 100 ms or less until the build number resolves.
   - Poll the build's `InputAction` executions as above.
   - For a parameterless gate, immediately POST `/input/<execution-id>/proceedEmpty` with the crumb (parameterized gates use `/input/<execution-id>/submit` with the expected parameters).
   - Emit only redacted timing, build, input, and HTTP-status evidence - never log credentials, authorization headers, or crumb values.

### Bind the approval to the build SHA and the gate's real shape

Queue resolution, SCM checkout, and input actions are separate, short-lived
states; an uncorrelated or shape-blind approval can advance the wrong code or
lose identity a later stage needs.

- Correlate `queue id -> build number -> checkout SHA -> unsettled input
  execution id` as one record, and verify the checkout SHA equals the intended
  remote branch SHA **before** approving. If the SHA is wrong, abort and remap
  immediately - never approve "the latest visible build."
- Inspect the core `InputAction.executions` message and parameter shape before
  choosing an endpoint. `proceedEmpty` is only for a truly parameterless gate.
  A gate configured with `submitterParameter` (for example `Build Approval?`
  with `submitterParameter: 'Approver'`) must be approved through the normal
  authenticated submit/classic form so the approver identity is recorded;
  `proceedEmpty` silently drops it. A job-specific
  `wfapi/inputSubmit?inputId=<id>` path is valid only after the gate's shape and
  expected parameters are confirmed.
- After submission, verify the input action disappeared and the console recorded
  the approval (and approver, when applicable). Treat a `302` to the canonical
  Jenkins hostname as potential success pending read-back; retry transient
  `500`/`503` only while the same execution is still unsettled.

Triggering builds and approving input gates are mutating actions - the explicit user approval rule from Guardrails applies before starting the sequence.

---

## Tips

- **Prefer `?tree=` / targeted commands** over dumping whole job objects - keeps context small.
- **Tail console logs** (last 100-200 lines) rather than fetching entire logs.
- **API tokens over passwords, minimal scope, rotated regularly**; store in env vars, never in code or chat.
- **Folder-style job paths** use `job/<folder>/job/<name>` in REST URLs and `<folder>/<name>` in the CLI.
