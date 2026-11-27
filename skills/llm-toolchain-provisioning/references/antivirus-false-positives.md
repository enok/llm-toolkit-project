# Antivirus false positives on scanner fixtures and encoded commands

Endpoint antivirus can quarantine scanner test fixtures (they contain attack samples as plain text) from a tool cache and report the scanner as broken. Triage by evidence; do not disable the antivirus.

- Folder allowlist: every folder the access log shows in use (work repos, tool cache, temp scratch). Exclude `.ssh` and the tool's own config folder: a session able to write the tool config can lift its own limits.
- Restore fixtures with the AV on. The checks prove the tree matches the tag before restoring: confirm the checked-out tag; `git fsck`; `git diff <tag>` shows only the fixture files; installed package intact; then `git checkout <tag> -- <fixtures>`.
- Encoded one-liners (gzip plus base64, `FromBase64String`) are flagged as malicious command lines; write files as plain text instead (see `rules/command-safety.md`).
