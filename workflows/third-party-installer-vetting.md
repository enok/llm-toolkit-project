---
description: Vet a desktop app a third party asks the user to install (interview, proctoring, client, or vendor tool) with read-only signature, hash, antivirus, and hash-lookup checks, weigh privacy risk, ask for alternatives, and leave the decision to the user
---

# Third-Party Installer Vetting Workflow

Use this when a `<requester>` (recruiter, interview or proctoring platform,
client, vendor) asks the user to install a desktop app and the user asks "is
this safe?", "does it contain malware?", or says they are uncomfortable
installing it. If the requester itself is unverified, run
`workflows/recruiter-legitimacy-check.md` first.

The outcome is evidence and options. Installing is always the user's call.

---

## Phase 0 - Hard limits

1. Never execute, open, mount, or "test install" the file, not even in a VM
   or sandbox you control.
2. Never open one-time links (assessment invites, tokenized download links).
   Opening one may start or consume the attempt or register the device. Ask
   the user where the file is instead.
3. Downloading a file to the user's computer, or copying it off the computer,
   needs their explicit OK. Prefer the copy they already have.
4. Read-only checks only: signature, hash, an antivirus scan of that one
   file, a hash lookup. Never upload the file anywhere.
5. Commands follow `rules/command-safety.md`: one file, quoted literal paths,
   no elevation on the user's behalf. If a step asks for admin rights, the
   user decides and runs it.
6. Any message to the requester follows `rules/human-comment-reply-gate.md`
   and `rules/external-write-authorization.md`.

## Phase 1 - Identify

1. **Requester**: who asked, on which channel, and whether the request fits
   the process so far.
2. **Documented vendor domain**: take it from the vendor's own site and the
   requester's earlier messages, never from the download link alone.
3. **What the app claims to do**: read the vendor docs, FAQ, privacy policy,
   and system requirements. Record what it scans (processes, windows,
   clipboard, screen, camera, mic), the permissions it requests (admin,
   accessibility, screen recording), supported OS versions, whether it
   self-uninstalls, and what data it keeps. Undocumented means "not
   documented", never assumed.
4. **Source**: the URL host the user downloaded from must match the
   documented domain. A link shortener, file-sharing site, chat attachment, or
   different domain is a stop: ask the requester.
5. **File**: name, type, size, path. The type must match the docs (MSI or EXE
   on Windows, DMG or PKG on macOS). A double extension (`.pdf.exe`), a script
   (`.bat`, `.ps1`, `.vbs`, `.js`), or a shortcut (`.lnk`) is a stop.

## Phase 2 - Static checks on the user's machine

1. **Where to run**: if a native OS shell on the user's computer is linked,
   run the blocks there. A Linux VM or container that only mounts the folder
   can compute the SHA-256 (`sha256sum`) but cannot run Authenticode or
   Defender checks. Otherwise give the user the exact block to paste into a
   normal (non-admin) PowerShell or Terminal and ask for the full output. When
   passing PowerShell through Bash, escape `$`.
2. **Windows** (replace the path; keep the single quotes):

   ```powershell
   $f = 'C:\Users\<user>\Downloads\<installer>.exe'
   Get-Item -LiteralPath $f | Select-Object Name, Length, LastWriteTime
   Get-Content -LiteralPath $f -Stream Zone.Identifier -ErrorAction SilentlyContinue
   Get-AuthenticodeSignature -LiteralPath $f | Select-Object Status, StatusMessage,
     @{n='Signer';e={$_.SignerCertificate.Subject}},
     @{n='TimeStamper';e={$_.TimeStamperCertificate.Subject}}
   Get-FileHash -LiteralPath $f -Algorithm SHA256
   & "$env:ProgramFiles\Windows Defender\MpCmdRun.exe" -Scan -ScanType 3 -File $f
   # or: Start-MpScan -ScanType CustomScan -ScanPath $f; Get-MpThreatDetection
   ```

   `Zone.Identifier` may show the browser's `HostUrl` and `ReferrerUrl`; compare
   only the host and do not repeat the full URL, which may carry a token. A
   detection may quarantine the file; that is expected.
3. **macOS**:

   ```bash
   f="$HOME/Downloads/<installer>.pkg"
   ls -l "$f"; shasum -a 256 "$f"
   mdls -name kMDItemWhereFroms "$f"
   pkgutil --check-signature "$f"     # .pkg
   spctl -a -vv -t install "$f"       # .pkg: Gatekeeper and notarization
   codesign -dv --verbose=4 "$f"      # .dmg or .app: signer, Team ID, timestamp
   ```

   An unsigned DMG is common (the app inside is signed); report "container
   unsigned, app not checked" unless the user mounts it themselves.
4. **VirusTotal hash lookup only**: search the SHA-256
   (`https://www.virustotal.com/gui/file/<sha256>`). Do not upload. Uploaded
   files are shared with paying subscribers, and per-user installers may embed
   invite tokens, names, or email addresses. "Not found" is common for
   per-user builds and means unknown, not clean.
5. **Optional host extraction** (most installers are compressed, so an empty
   result proves nothing):

   ```powershell
   [regex]::Matches([IO.File]::ReadAllText($f, [Text.Encoding]::ASCII),
     'https?://[A-Za-z0-9.-]+') | ForEach-Object Value | Sort-Object -Unique
   ```

   On macOS: `strings -a "$f" | grep -Eo 'https?://[A-Za-z0-9.-]+' | sort -u`.
   Never visit the hosts. Raw IPs, paste sites, or file-sharing hosts are
   questions for the requester.
6. **Interpret**:

   | Result | Meaning |
   | --- | --- |
   | `Valid`, signer matches the documented publisher, timestamp present, 0 Defender detections, 0 VirusTotal detections or not found | No known-malware signal |
   | `NotSigned`, `HashMismatch`, other non-`Valid` status, or signer is another company or a person | Stop |
   | Any Defender detection, or VirusTotal detections | Stop; report the engine names |
   | A check could not run | Incomplete; name it, never substitute an upload |

## Phase 3 - Privacy and residual risk

1. "No known-malware signal" is not "safe". A signature proves who built the
   file, not what it does.
2. Proctoring and monitoring apps are intrusive by design: process and window
   lists, screen capture, camera, mic, sometimes clipboard and network
   inspection. List what Phase 1 found.
3. Data: what is recorded, where it is stored, for how long, who sees it
   (requester, end client), and how to request deletion.
4. Footprint: admin rights, persistence (service, scheduled task, login
   item, system extension), and whether self-uninstall is documented.
5. On a work-issued or shared machine, the owner's policy may forbid it.
   Anything on screen is visible while the app runs.
6. Compare this against the user's stated comfort. Offer three options:
   install with Phase 5 prep, ask for an alternative (Phase 4), or decline.

## Phase 4 - Alternatives: ask, don't work around

1. Draft a short, polite request to the requester with `Posting status: NOT
   POSTED`, the exact target thread, and the exact text. Ask whether any of
   these is acceptable: a live interview with a person, a different format
   (shared editor, take-home), a different allowed device, or permission to
   run the app in a VM or Windows Sandbox. State a personal security
   preference; do not accuse the requester.
2. Tell the user the facts:
   - an unsupported OS (for example Linux) usually fails or is blocked;
   - VMs are often detected and flagged, which can void the attempt or read
     as misconduct, so never use one silently;
   - Windows Sandbox is disposable (wiped on close) and needs a supported
     Windows edition with the feature enabled. It is also a VM, so use it only
     if the requester allows it. Camera and mic must be enabled in the
     `.wsb` file:

   ```xml
   <Configuration>
     <AudioInput>Enable</AudioInput>
     <VideoInput>Enable</VideoInput>
     <MappedFolders>
       <MappedFolder>
         <HostFolder>C:\Users\USERNAME\installer-only</HostFolder>
         <ReadOnly>true</ReadOnly>
       </MappedFolder>
     </MappedFolders>
   </Configuration>
   ```

3. Never advise evading detection: no hiding VM artifacts, spoofing hardware
   IDs, renaming processes, or keeping hidden assistants running. If asked,
   decline that part and return to step 1.
4. Send only the approved text, then wait for the answer.

## Phase 5 - If the user decides to install

1. The user runs the installer themselves, from the exact file whose hash was
   checked. The agent does not click through it.
2. Optional: save service, scheduled-task, and startup lists first, to diff
   later.
3. Preparation checklist before the session:
   - quit AI assistants, desktop agents, automation browser extensions,
     remote-access tools, screen recorders, and transcription apps;
   - one monitor; close windows with personal data; notifications off;
   - pause any agent polling that opens browser tabs or windows on the
     machine (`workflows/conversation-monitoring.md` Phase 4); resume only
     when the user asks.
4. After the session, verify the uninstall:

   ```powershell
   $n = '<app word>'
   Get-ItemProperty 'HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*',
     'HKLM:\Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\*',
     'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\*' -ErrorAction SilentlyContinue |
     Where-Object DisplayName -like "*$n*" | Select-Object DisplayName, InstallLocation
   Get-Service | Where-Object { $_.Name -like "*$n*" -or $_.DisplayName -like "*$n*" }
   Get-ScheduledTask | Where-Object TaskName -like "*$n*"
   Get-CimInstance Win32_StartupCommand | Where-Object Command -like "*$n*"
   Get-ChildItem $env:ProgramFiles, ${env:ProgramFiles(x86)}, $env:LOCALAPPDATA, $env:APPDATA `
     -Directory -Filter "*$n*" -ErrorAction SilentlyContinue
   ```

   Also check Settings > Apps (Apps & features). On macOS:

   ```bash
   n='<app word>'
   ls /Applications ~/Library/LaunchAgents /Library/LaunchAgents /Library/LaunchDaemons 2>/dev/null | grep -i "$n"
   pkgutil --pkgs | grep -i "$n"
   ```

   Then check System Settings > General > Login Items and Privacy & Security
   (revoke screen recording, camera, mic, accessibility).
5. Report leftovers. Removal is the user's decision, through the vendor
   uninstaller or the OS app list; never delete files recursively yourself.

## Phase 6 - Report

1. One verdict line: `No known-malware signal (not a safety guarantee)`,
   `Stop: <reason>`, or `Incomplete: <missing check>`.
2. Evidence table:

   | Check | Command | Result |
   | --- | --- | --- |
   | Download host | `Zone.Identifier` / `kMDItemWhereFroms` | host only |
   | File type, size | `Get-Item` / `ls -l` | |
   | Signature, signer, timestamp | `Get-AuthenticodeSignature` / `pkgutil`, `codesign` | |
   | SHA-256 | `Get-FileHash` / `shasum -a 256` | |
   | Defender scan | `MpCmdRun.exe -Scan -ScanType 3` | |
   | VirusTotal hash | hash search, no upload | |
   | Embedded hosts (optional) | regex or `strings` | |
   | Vendor docs | scan scope, permissions, uninstall, retention | |

3. Add the Phase 3 privacy summary and any Phase 4 draft (NOT POSTED).
4. End with the options and leave the decision to the user. Never write "you
   should install it". Keep tokens, full download URLs, and personal data
   from the file out of the report.
5. Capture reusable lessons with `workflows/capture-learning.md`, with no
   vendor or requester names.
