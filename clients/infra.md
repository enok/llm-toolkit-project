# New LLM Client Infrastructure Bootstrap

Use the repository-root INFRA entrypoint to configure a new workstation and,
optionally, link a consumer repository to the shared toolkit.

Plan on Linux, macOS, or Windows Git Bash:

```bash
./INFRA.sh --consumer /path/to/project
```

Apply after reviewing the plan:

```bash
./INFRA.sh --apply --consumer /path/to/project
```

Native Windows PowerShell:

```powershell
.\INFRA.ps1 -Consumer C:\path\to\project
.\INFRA.ps1 -Apply -Consumer C:\path\to\project
```

The bootstrap selects the full tool profile and all supported LLM agent
CLIs, then invokes the pinned Slack CLI installer. Authentication remains
manual: the scripts never run GitHub, Atlassian, AWS, Slack, or
LLM-provider login commands and never accept credentials.

The npm-based tools are exact-version pinned and installed with lifecycle
scripts disabled. If Python is not yet available, a plan still completes
and marks Slack installation as deferred; after an applied bootstrap
installs Python, open a new shell and rerun the apply command.

The operation is idempotent for commands already present. Slack CLI
installation is additionally overwrite-safe: an existing `slack` executable
is preserved.

Once the workstation and any linked consumer repo are bootstrapped, use
[`README.md`](README.md) for the day-to-day overlay sync commands
(`npm run tool-configs:sync`, `npm run subagents:apply`).
