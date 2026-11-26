---
title: A security filter that fails closed can block a mislabelled archive with Access denied
category: environment
created: 2026-11-26
tags: [windows, access-denied, antivirus, minifilter, fail-closed, gzip, magic-bytes, ntstatus, classifier]
---

# Problem
Opening one downloaded file returned "Access denied" although the owner and the NTFS ACL
looked healthy. The file was compressed data saved with a plain-data extension, and a
security product's file filter had failed its scan and was refusing every open.

# Failed Approaches
- Re-checking and resetting permissions (owner, ACL, inheritance): they were already fine, so
  nothing changed.
- Retrying the open or copying the file: each attempt hit the same filter.
- Restarting the security service from the agent with elevation: denied by the auto-mode
  classifier; do not retry.

# Solution
Diagnose from the outside in, then hand the fix to the user:
1. Owner and ACL healthy but "Access denied" on open: suspect a filter driver or security
   product, not permissions.
2. Probe the open with `CreateFileW` for `FILE_READ_ATTRIBUTES` and read the NTSTATUS
   (`RtlGetLastNtStatus`); `0xC0000022` (access denied) on attributes alone points at a filter.
3. Read the security product's own log for a line such as "scan status unknown" or a parser
   error on the file.
4. Read the first bytes (`1F 8B` is gzip) and check the browser's download history for the real
   content type.
5. User fix: toggle the threat protection off, restart its service as administrator, or reboot;
   then rename the file to `.gz` (or `.csv.gz`) and extract it.

# Why
Some filters fail closed: when a scan errors out (for example because the file's real type does
not match its extension and the scanner's parser breaks), they deny access instead of allowing
it. The block then looks like a permission problem. The agent can find the cause but should not
change security software, and an elevated restart is denied for that reason. Untested: other
security products; the log wording and status code are from one case.
