---
title: Cross-platform JMeter execution
tags: [jmeter, performance, cross-platform, cli, automation]
---

# Cross-Platform JMeter Execution

This skill must work from Windows, Linux, and macOS. Prefer the Python script
in `scripts/run_jmeter.py`; the PowerShell wrapper
(`scripts/Invoke-JMeter.ps1`) is an optional Windows convenience that forwards
to the same script.

## Prerequisites

- Python 3. `scripts/run_jmeter.py` is standard-library only — no
  third-party packages to install.
- A Java runtime compatible with the installed JMeter version.
- Apache JMeter on `PATH`, via `JMETER_HOME`, or passed with `--jmeter-bin`.
  Install it with your platform's package manager (Homebrew's `jmeter` on
  macOS, Chocolatey's or winget's `Apache.JMeter` on Windows, `apt`/`dnf` on
  Linux) or download it from the Apache JMeter site and point `JMETER_HOME`
  at the extracted folder. `--dry-run` works with no JMeter installation at
  all, so you can validate a plan before setting one up.

## Dry Run First

A dry run patches a copy of the `.jmx`, writes `manifest.json`, and prints the
command it would execute — without generating any load and without requiring
JMeter to be installed. Do this before every first run against a new target.

Linux/macOS:

```bash
python3 skills/jmeter-performance-testing/scripts/run_jmeter.py \
  --jmx /path/to/test.jmx \
  --base-url https://api.example.com \
  --threads 15 --ramp-up 300 --duration 1800 \
  --results-dir /tmp/perf-runs \
  --dry-run
```

Windows:

```powershell
python skills\jmeter-performance-testing\scripts\run_jmeter.py `
  --jmx "C:\path\to\test.jmx" `
  --base-url https://api.example.com `
  --threads 15 --ramp-up 300 --duration 1800 `
  --results-dir "C:\temp\perf-runs" `
  --dry-run
```

Read the printed command and `manifest.json` before removing `--dry-run`: the
command shows every `-J` flag with its value redacted, so confirm the
*keys* are the ones you expect (`base_url`, `auth_token`, and anything from
`--property`) even though the values are hidden.

## Execute A Run

```bash
python3 skills/jmeter-performance-testing/scripts/run_jmeter.py \
  --jmx /path/to/test.jmx --base-url https://api.example.com \
  --threads 15 --ramp-up 300 --duration 1800
```

Use `python` instead of `python3` on Windows when that is the available
command. The PowerShell wrapper takes the same options in PowerShell form:

```powershell
.\skills\jmeter-performance-testing\scripts\Invoke-JMeter.ps1 `
  -JmxPath C:\path\to\test.jmx -BaseUrl https://api.example.com `
  -Threads 15 -RampUp 300 -Duration 1800
```

`-Property` takes a PowerShell array — pass more than one value as
`-Property "a=1","b=2"`, not by repeating `-Property`; PowerShell's parameter
binder rejects a named parameter passed twice in one call.

The script exits with JMeter's own exit code, so a non-zero exit means the
run failed; check `jmeter.log` in the results directory first.

## Overriding Thread Group Numbers

`--threads`, `--ramp-up`, and `--duration` patch the Thread Group fields
(`ThreadGroup.num_threads`, `ThreadGroup.ramp_time`, `ThreadGroup.duration`)
directly in the *copy* of the `.jmx`; see `references/load-profiles.md` for
how to size these numbers. This works on existing plans that hardcode those
fields — no `${__P(...)}` property needed in the plan itself. Enable the
plan's Scheduler for `--duration` to take effect. If a requested override has
nothing to patch (for example `--duration` on a plan whose Scheduler was
never enabled in the GUI, so the field is absent), the runner fails loudly
instead of silently doing nothing.

The runner does not patch a Constant Throughput Timer. If a run needs to vary
the CTT rate, have the plan read it as a property
(`${__P(throughput_per_minute,60)}`) and pass
`--property throughput_per_minute=<value>` instead.

## Parameterizing The Plan

`--base-url` is injected as the JMeter property `base_url`
(`-Jbase_url=VALUE`), so one `.jmx` serves every environment. Read it in the
plan as `${__P(base_url,http://localhost:8080)}`.

Pass anything else — endpoint paths, tenant IDs, data-file paths, a CTT
throughput number — with repeatable `--property KEY=VALUE`. Every `-J`
value (`base_url`, every `--property`, and the auth token) is redacted in
console output and in `manifest.json`, so secrets do not land in the run
record; only the property *keys* stay visible there. They are still visible
in the local process list while the run is active, so prefer short-lived
tokens and `--auth-token-env` over `--auth-token`.

## Outputs

Each run writes into `<results-dir>/run-<timestamp>/`:

- `patched-<name>.jmx` — the plan actually executed; the source `.jmx` is
  never modified
- `manifest.json` — resolved settings and the exact (redacted) jmeter
  command; always written, including on `--dry-run`
- `results.jtl`, `jmeter.log` — written by JMeter itself; only produced on a
  real run, not on `--dry-run`

Keep run outputs out of version control; commit the `.jmx` instead. Summarize
the JTL:

```bash
python3 skills/jmeter-performance-testing/scripts/summarize_jmeter_jtl.py \
  --jtl perf-runs/<run>/results.jtl \
  --out-json perf-runs/<run>/summary.json \
  --out-md perf-runs/<run>/summary.md
```

## Notes And Pitfalls

- The runner patches literal Thread Group values, so it works whether or not
  the plan uses `${__P(...)}` properties elsewhere for those fields.
- `--auth-token` and every `--property` value can contain anything, so the
  runner treats all of them as sensitive by default and redacts them
  uniformly; it cannot tell which ones actually are secrets.
- Do not run long profiles from a laptop where sleep settings, Wi-Fi, or a
  VPN can interrupt the run. Use a stable host near the target.
- Compare like with like: the same plan revision, the same settings, the
  same environment, and a client that was not itself saturated (see
  `references/result-analysis.md`).
