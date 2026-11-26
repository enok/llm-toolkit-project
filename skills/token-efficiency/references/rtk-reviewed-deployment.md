# RTK reviewed deployment

The only RTK deployment approved for explicit use. Any other version or platform needs its own review (`skills/external-skill-intake/SKILL.md`). Constraint set: `rules/command-safety.md`.

- Reviewed: RTK **1.2.1**, native Windows, explicit `rtk <cmd>` wrapper only. Static source review plus a runtime smoke test on a Windows PC (2026-11-26).
- Installer SHA-256 `08671cb746e779c50dc530eec0114a7cd6cbbd1ea4f66c98dd9f0572f5f96c43` matched the release `checksums.txt`.

## Install and pin (PowerShell)

```powershell
winget install --id rtk-ai.rtk --version 1.2.1 --exact
winget pin add --id rtk-ai.rtk --version 1.2.1
```

`scripts/bootstrap-dev.ps1 -Rtk` does exactly this (opt-in; off by default).

## Environment (User scope, new shell afterwards)

```powershell
[Environment]::SetEnvironmentVariable('RTK_TELEMETRY_DISABLED','1','User')
[Environment]::SetEnvironmentVariable('RTK_TEE','0','User')
[Environment]::SetEnvironmentVariable('RTK_RECALL','0','User')
[Environment]::SetEnvironmentVariable('RTK_DB_PATH','NUL','User')
[Environment]::SetEnvironmentVariable('RTK_SUPPRESS_HOOK_WARNING','1','User')
```

`RTK_DB_PATH` is the only effective tracking control: `[tracking] enabled = false` is parsed but not honoured.

## `%APPDATA%\rtk\config.toml`

Every key of a section that is present is required.

```toml
[tracking]
enabled = false        # not honoured; kept for intent only
history_days = 1

[retriever]
mode = "disabled"      # no recall store, no tee files

[telemetry]
enabled = false
consent_given = false

[hooks]
suppress_hook_warning = true
```

## Never

- Run `rtk init`, `rtk trust`, `rtk telemetry enable`, `rtk llm-proxy`, `rtk claude`, `rtk pipeline add` or `rtk plugins`.
- Create `%APPDATA%\rtk\pipeline.toml` or `%APPDATA%\rtk\pipelines\`; set `RTK_TRUST_PROJECT_FILTERS` or `RTK_HOOK_AUDIT`.

## Smoke test (PowerShell, scratch git repo, new shell)

```powershell
$dirs = "$env:LOCALAPPDATA\rtk","$env:APPDATA\rtk",(Get-Location).Path
$before = $dirs | % { if (Test-Path $_) { Get-ChildItem $_ -Recurse -Force -File | % FullName } }
rtk telemetry status    # expect: blocked by RTK_TELEMETRY_DISABLED
rtk git status;  $a=$LASTEXITCODE; git status *> $null; "$a vs $LASTEXITCODE"
rtk git log --oneline -n 2000 | Out-Null
rtk git show does-not-exist *> $null; $c=$LASTEXITCODE; git show does-not-exist *> $null; "$c vs $LASTEXITCODE"
$after = $dirs | % { if (Test-Path $_) { Get-ChildItem $_ -Recurse -Force -File | % FullName } }
Compare-Object @($before) @($after)     # expect: no output
'history.db*','recall.db*','tee','hook-audit*','*.log','.device_salt','.telemetry_last_ping','.hook_warn_last','NUL-*' |
  % { Get-ChildItem $dirs -Recurse -Force -Filter $_ -ErrorAction SilentlyContinue }   # expect: nothing
```

Result on the reviewed PC: no `history.db`, `recall.db`, tee directory or markers; exit codes 0, 0 and 128, equal to raw git; telemetry reported blocked. If any `NUL-*` file appears, use a plain file as the parent of the DB paths (macOS variant below).

## Licence

RTK 1.0.0 and later link the `rtk-engine` crate under BUSL-1.1 (change date 2030-09-09) into the default binary; `LICENSE-ENGINE` ships beside it. If that is unacceptable, use the Apache-only `rtk-oss` zip from the same GitHub release (not in winget; verify its SHA-256 against `checksums.txt`, and the smoke test applies unchanged), or stay on the last Apache-only winget build 0.44.2, which has a stderr-swallowing defect and an unswitchable `.hook_warn_last` file. Either needs its own sign-off.

## `rtk mvn` caveat

`rtk mvn` silently runs a repository-local `mvnw.cmd` when one exists, and that wrapper may download a Maven distribution from the URL in `.mvn/wrapper/maven-wrapper.properties`. Treat `rtk mvn` in an untrusted repository as running that repository's code; use the raw `mvn` there.

## macOS variant (not yet verified on a Mac)

Version 1.2.1 and the privacy controls are the same; the platform was not reviewed or smoke-tested. `NUL` does not exist on macOS and `/dev/null` is not a usable SQLite parent, so point the DB paths at a plain file used as a directory parent:

```bash
brew install rtk              # formula name and version unverified: `rtk --version` must print 1.2.1, otherwise stop and remove it
touch "$HOME/.rtk-off"        # a regular file: paths below can never be created beneath it
export RTK_DB_PATH="$HOME/.rtk-off/history.db"
export RTK_RECALL_DB="$HOME/.rtk-off/recall.db"
export RTK_TELEMETRY_DISABLED=1 RTK_TEE=0 RTK_RECALL=0 RTK_SUPPRESS_HOOK_WARNING=1
```

Run the smoke test equivalent (`~/Library/Application Support/rtk` and `~/.config/rtk` instead of the Windows folders) before relying on it. `scripts/bootstrap-dev.sh --rtk` refuses to continue unless `rtk --version` reports 1.2.1.
