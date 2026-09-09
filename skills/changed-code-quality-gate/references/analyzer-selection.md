---
title: Analyzer selection for the changed-code quality gate
tags: [static-analysis, semgrep, sonar, spotbugs, quality-gate, changed-code]
---

# Analyzer selection

Use the narrowest analyzer already configured by the target project.

The shipped executable adapter is Semgrep for Java, Python, JavaScript, and
TypeScript, plus trusted syntax/policy checks for Bash and PowerShell. Sonar and
SpotBugs are selection guidance for project-native integrations; this toolkit
does not claim to ship those adapters.

| Analyzer | Suitable changed-code evidence | Constraint |
| --- | --- | --- |
| Semgrep | Explicit scoped Java, Python, JavaScript, and TypeScript files plus findings filtered to Git-added lines | Use a reviewed local ruleset; pin CI actions and install dependencies from a hash-locked file |
| SonarQube/SonarCloud | Pull-request analysis with a quality gate defined on new code | Verify the server result belongs to the exact head; do not expose tokens to untrusted forks |
| SpotBugs | Existing Maven/Gradle report filtered to changed Java source and lines | SpotBugs is the maintained successor to FindBugs. It normally analyzes compiled project classes, so an unfiltered report is broader-run evidence, not a replacement for the shipped Java gate |

## Normalizing project-native results

A project-native analyzer result counts as this gate only when every finding
is mapped back to a changed file and an added/modified line range from the
same base/head diff the gate computed. Record the analyzer, the head SHA it
analyzed, and the filtering method in the validation report. A whole-project
scan, a stale head, or a result without line mapping is supporting evidence
only.

## Reviewed sources

- SonarSource, `sonarqube-quality-gate-action` and Sonar pull-request analysis
  documentation: <https://github.com/SonarSource/sonarqube-quality-gate-action>
- SpotBugs official project: <https://github.com/spotbugs/spotbugs>
- Semgrep official skill repository and CI documentation:
  <https://github.com/semgrep/skills/tree/main/skills/semgrep>

These sources were reviewed for documented concepts only. The external-source
URL check required by `skills/external-skill-intake/SKILL.md` did not return a
`SAFE` result at review time; that is an unvalidated result, not evidence of
maliciousness. Direct import remains blocked until a later check passes, and
only generic documented concepts were independently implemented.
