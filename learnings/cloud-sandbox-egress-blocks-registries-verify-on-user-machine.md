---
title: Cloud sandbox egress blocks registries, so verify builds on the user's machine
category: environment
created: 2026-10-07
tags: [sandbox, egress, registries, http-403, verification, windows, powershell, toolchain]
---

# Problem

In the cloud sandbox, outbound requests to npm, Maven Central, GitHub web and releases,
YouTube and Medium returned HTTP 403. Dependencies could not be installed there, and the
sandbox toolchains (JDK 21, Node 22 and tsc 6) lagged the study repo's targets (Java 25,
Node 24 and TypeScript 7). A passing sandbox run could therefore not be the final verdict.

# Failed Approaches

None recorded in the session notes; the default behaviour produced the failure described above.

# Solution

1. In the sandbox, run best-effort checks with whatever is installed and report them as
   partial.
2. Run the definitive build and tests on the user's machine (through the root session's
   device bridge; lanes cannot reach it), after installing missing toolchains
   user-locally: no admin rights and no global PATH change.
3. Set `JAVA_HOME` and `PATH` per run inside a verification script, so only that script's
   process sees the new tools.
4. Log each step's name and exit code plus the toolchain versions as the evidence.

Windows PowerShell 5.1 syntax for steps 2 and 3 (placeholders for the URL and the Maven
folder; not executed in the authoring sandbox). The extracted JDK folder carries a version
in its name, so look it up instead of hard-coding it:

```powershell
$jdkRoot = Join-Path $env:USERPROFILE '.jdks'
New-Item -ItemType Directory -Force $jdkRoot | Out-Null
Invoke-WebRequest '<jdk-zip-url>' -OutFile (Join-Path $jdkRoot 'jdk.zip')
Expand-Archive (Join-Path $jdkRoot 'jdk.zip') -DestinationPath $jdkRoot -Force
$jdkHome = (Get-ChildItem $jdkRoot -Directory | Where-Object { $_.Name -like 'jdk-25*' } |
  Select-Object -First 1).FullName
$mvnHome = Join-Path $env:USERPROFILE '.m2\tools\<extracted-maven-folder>'
$env:JAVA_HOME = $jdkHome
$env:Path = "$env:JAVA_HOME\bin;$mvnHome\bin;$env:Path"
java -version
mvn -v
```

Unpack the Maven binary zip into `.m2\tools` the same way. The full `verify.ps1` loop
(one `Step` per language, each logging its exit code) is in the durable reference.

Durable guidance: skills/multi-language-study-repo/references/toolchain-notes.md

# Why

The sandbox's network policy, not the code under test, produced the 403s. Inference:
results from older toolchains can differ from the target versions, so only a run on the
target toolchain counts as a pass. Installing into the user profile and setting variables
per run leaves the machine's other tools untouched.
