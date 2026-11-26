# Onboarding script contract

Read this when the request is "write a script that sets up the whole dev
environment for the other developers" (one project or several). A setup script
that only works on the author's machine, or that cannot say what is missing,
turns every new teammate into a support ticket. The contract below keeps the
script re-runnable and its failures actionable.

## Contents

1. Parameters
2. Idempotence
3. The `--doctor` mode
4. Versions come from the repos
5. What the script cannot reach
6. Keep the loop short
7. Checklist

## 1. Parameters

- A project selector that accepts one project or several (`--project a` or
  `--project a,b`; default: all known projects).
- `--dry-run`: print every action without executing it, so the user reviews the
  plan before anything changes.
- Skip flags per step (`--skip-containers`, `--skip-registry-auth`) so a
  developer who already has a piece does not have to fight the script.
- Exit non-zero when any required step fails; print a one-line summary last.

## 2. Idempotence

Every step is "check, then act": test whether the tool, config line, login or
container already satisfies the requirement and skip with a visible
`already ok` message. Running the script twice must be a no-op the second
time. This is also what makes it safe to re-run after a partial failure.

## 3. The `--doctor` mode

`--doctor` changes nothing and prints a pass/fail checklist. Each failing line
names the exact missing item and the exact fix command:

```text
[ok]   node 20.11 (required 20.x)
[FAIL] container runtime memory 2 GB (required >= 6 GB)
       fix: raise the limit in the container runtime settings, then restart it
[warn] optional: ripgrep not found
       fix: <package-manager install command>
```

- Separate required tools from optional ones; only required failures fail the
  run.
- Check runtime versions the runbooks demand (language runtimes, build tools),
  container resource limits, registry and cloud logins, and required env files.
- Keep each check a plain command the user can re-run alone and paste back.
  The setup then becomes a loop (run, paste output, fix the named item) that
  works even when you cannot see their machine.

## 4. Versions come from the repos

Read tool and runtime versions from the repositories at run time (version
files, build config, runbooks) instead of hardcoding them in the script. A
hardcoded version is correct the day it is written and wrong a month later.

## 5. What the script cannot reach

State plainly, in the script's help and in its final output, which sources it
cannot reach: chat tools, trackers, wikis, anything behind a login the script
does not hold. Those stay with a scheduled task or a manual step; do not let
the script imply it verified them.

## 6. Keep the loop short

Drop steps the user judges unnecessary instead of keeping them "just in case".
Each extra step is one more thing that can fail on someone else's machine.

## 7. Checklist

- [ ] Project selector, `--dry-run`, skip flags
- [ ] Every step check-then-skip
- [ ] `--doctor` with required vs optional and exact fix commands
- [ ] Versions read from the repos
- [ ] Unreachable sources named in the output
- [ ] No project codenames, hosts or ids baked in; they come from config

Related: [environment-diagnose](../../environment-diagnose/SKILL.md) for a
setup that used to work, and
[cloud-cli-permission-denied-triage-and-admin-request](../../../learnings/cloud-cli-permission-denied-triage-and-admin-request.md)
when a doctor check fails on missing cloud roles.
