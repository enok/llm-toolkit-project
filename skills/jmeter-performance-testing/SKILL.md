---
name: jmeter-performance-testing
description: Plan, run, monitor, analyze, and report Apache JMeter load and performance tests against any HTTP service. Use when executing `.jmx` test plans, sizing Thread Group and Constant Throughput Timer load profiles, parameterizing a target URL or auth token, summarizing `.jtl` results, comparing a candidate build against a baseline, or deciding whether a change improved or regressed latency, throughput, and error rate.
license: MIT
metadata:
  author: llm-toolkit-project
  version: "1.0.0"
---

# JMeter Performance Testing

Use this skill for load and performance work against any HTTP service or API
with Apache JMeter. It assumes JMeter Thread Groups with an optional Constant
Throughput Timer (CTT), plus whatever observability the target stack exposes
(application metrics, logs, traces, cloud dashboards).

Everything project-specific — base URLs, endpoint paths, credentials, the
documented load plan, log group or metric names, and pass/fail thresholds —
comes from the request or the consumer repo's `docs/llm/`. This skill holds the
method only.

## Safety Defaults

- Treat load tests as environment-changing operations. Confirm the target
  environment and base URL before generating any traffic.
- Never run load against production unless the user explicitly asks and the test
  window is approved by whoever owns the service.
- Use synthetic identifiers and synthetic payloads. Do not send real PII.
- Never hardcode credentials in a `.jmx` file, a script, or a chat message.
  Obtain a token out of band and inject it as a JMeter property at run time.
- If another load run is already active against the same target, do not add
  traffic unless the user asks to overlap; if runs overlap, report each run's
  volume and the combined volume separately.
- Prefer a short smoke probe before any long run, and re-verify the target is
  healthy before and after.

## Workflow

1. **Establish context.**
   - Identify the service under test, environment, branch or build, base URL,
     endpoints, test window, and whether the ask is a smoke probe, a full
     profile run, a baseline comparison, or monitoring/reporting only.
   - Confirm access to the environment (network path, VPN, auth) and to the
     observability surface before starting.
   - Record the exact time window in UTC plus local time; every later metric
     query depends on it.

2. **Pick or define the load profile.**
   - Use `references/load-profiles.md` to choose a profile shape and to size
     threads, ramp-up, duration, and throughput.
   - If the project documents an official plan, preserve its threads, ramp-up,
     duration, and CTT values exactly unless the user says to change them.
   - Distinguish *business flows per hour* from *endpoint requests per minute*
     and state the requests-per-flow ratio you assumed.

3. **Parameterize the plan.**
   - Pass the target base URL, endpoint paths, and any auth token as JMeter
     properties (`-J`) rather than editing the `.jmx` per environment.
   - Keep the `.jmx` in version control; keep run outputs out of it.

4. **Run or supervise the test.**
   - Prefer the cross-platform Python runner
     `skills/jmeter-performance-testing/scripts/run_jmeter.py`; the PowerShell
     wrapper is a Windows convenience only.
   - Always dry-run first: it patches a copy of the `.jmx`, writes
     `manifest.json`, and prints the command without generating load or
     requiring JMeter to be installed.
   - Use non-GUI execution for repeatable runs and save `results.jtl`,
     `jmeter.log`, and `manifest.json` from the timestamped results
     directory each run produces.
   - Configure the CTT (when the plan uses one) as samples per minute with
     the intended target scope ("all active threads (shared)" for a
     plan-wide rate), applied per Thread Group as the plan requires. The
     runner overrides Thread Group threads/ramp-up/duration directly; it
     does not patch a Constant Throughput Timer. If a run needs to vary the
     CTT rate, have the plan read it as a property
     (`${__P(throughput_per_minute,60)}`) and pass
     `--property throughput_per_minute=<value>`.

5. **Monitor the service while the test runs.**
   - Use `references/metrics-checklist.md` for the client-side, service-level,
     and infrastructure signals to collect.
   - Watch latency percentiles, throughput, error and timeout rates, saturation
     (CPU, memory, connection/thread pools), and downstream dependency health.

6. **Analyze and report.**
   - Use `references/result-analysis.md` for thresholds, baseline comparison
     arithmetic, multi-hop or asynchronous trace reconstruction, and the
     improved/regressed/stable decision rule.
   - Summarize the `.jtl` with `scripts/summarize_jmeter_jtl.py`.

## Output Shape

Return a concise performance summary with:

- Test profile, environment, base URL, and time window
- Traffic volume, duration, and achieved vs. target throughput
- Latency (avg, p50, p95, p99, max) and success rate, overall and by label
- Status-code distribution and representative error examples
- Service, log, and infrastructure findings
- Baseline comparison with the direction and formula stated before any table
- Decision: improved, regressed, stable, or inconclusive
- Residual risks (partial observability, expired session, overlapping load,
  client-side saturation) and follow-ups only when necessary

## Cross-Platform Execution

Python is the source-of-truth interface because it works on Windows, Linux, and
macOS (`rules/cross-platform-scripts.md`):

```bash
python3 skills/jmeter-performance-testing/scripts/run_jmeter.py \
  --jmx path/to/test.jmx --base-url https://api.example.com \
  --threads 15 --ramp-up 300 --duration 1800 --dry-run
python3 skills/jmeter-performance-testing/scripts/run_jmeter.py \
  --jmx path/to/test.jmx --base-url https://api.example.com \
  --threads 15 --ramp-up 300 --duration 1800
python3 skills/jmeter-performance-testing/scripts/summarize_jmeter_jtl.py \
  --jtl perf-runs/<run>/results.jtl --out-md perf-runs/<run>/summary.md
```

On Windows, `python` is usually the right command, and the PowerShell wrapper is
available:

```powershell
python skills\jmeter-performance-testing\scripts\run_jmeter.py `
  --jmx path\to\test.jmx --base-url https://api.example.com `
  --threads 15 --ramp-up 300 --duration 1800 --dry-run
.\skills\jmeter-performance-testing\scripts\Invoke-JMeter.ps1 `
  -JmxPath path\to\test.jmx -BaseUrl https://api.example.com `
  -Threads 15 -RampUp 300 -Duration 1800 -DryRun
```

### Injecting an auth token

Obtain the token with the service's own auth flow, export it to an
environment variable, and pass the variable's *name* with `--auth-token-env`
so the value itself never appears in your shell history. The runner injects
it as the JMeter property `auth_token` and redacts it from every console
line and from `manifest.json`. `--auth-token` (the value directly) also
works but is visible in shell history and the local process list, so prefer
the `-env` form when you can:

```bash
export API_TOKEN="$(curl -sS -X POST "$AUTH_URL/oauth/token" \
  -d grant_type=client_credentials -u "$CLIENT_ID:$CLIENT_SECRET" | jq -r .access_token)"

python3 skills/jmeter-performance-testing/scripts/run_jmeter.py \
  --jmx path/to/test.jmx --base-url https://api.example.com \
  --auth-token-env API_TOKEN
```

In the `.jmx`, read the property in an HTTP Header Manager value:
`Bearer ${__P(auth_token,)}`. Never commit the token, echo it, or paste it into
chat. For a token that expires mid-run, refresh it inside the plan (a JSR223
pre-processor or a login sampler) rather than lengthening its lifetime.

## References

- `references/load-profiles.md` - profile shapes, CTT mechanics, and how to size
  threads, ramp-up, duration, and throughput.
- `references/jmeter-execution.md` - cross-platform install, dry run, execution,
  and summarization examples.
- `references/metrics-checklist.md` - client, service, and infrastructure signals
  to collect during and after a run.
- `references/result-analysis.md` - thresholds, baseline comparison, multi-hop
  and asynchronous trace reconstruction, and the decision rule.

## Related Toolkit Capabilities

- `skills/testing/SKILL.md` for acceptance-criteria traceability and coverage
  expectations around a performance change.
- `skills/log-analysis/SKILL.md` for extracting evidence from service logs
  during and after a run.
- `skills/aws-alarm-investigator/SKILL.md` when a run trips a cloud alarm.
- `skills/cli-creator/SKILL.md` when promoting these scripts into a durable CLI.
- `rules/cross-platform-scripts.md` for the portability contract these scripts
  follow.
- `rules/command-safety.md` before running any command that generates load
  against a shared environment.
