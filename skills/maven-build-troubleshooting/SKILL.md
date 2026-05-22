---
name: maven-build-troubleshooting
description: "Diagnose Maven build, test, OWASP dependency-check, Jetty/Tomcat, Windows shell, plugin, and Java runtime failures. Use when mvn commands fail or Java webapp local startup breaks."
license: MIT
metadata:
  author: dev-tools
  version: "1.0.0"
---

# Maven Build Troubleshooting

## Triage order

1. Capture the full failing command and exit code.
2. Save complete output to a log file when errors are long or multi-cause.
3. Identify the first root-cause error, not only the last stack trace.
4. Check local JDK/Maven versions against `pom.xml`, toolchains, and plugin requirements.
5. Inspect effective POM and active profiles before changing dependencies.
6. Verify exact artifact versions exist before proposing upgrades.
7. Separate local-development bypasses from final validation gates.

## Common failure classes

| Symptom | Check |
| --- | --- |
| Shell path errors on Windows | Maven antrun/exec plugins assuming `/bin/sh` |
| `UnsupportedClassVersionError` | Dependency compiled for newer Java than runtime |
| OWASP dependency-check fail | Upgrade path, suppression justification, exploitability evidence |
| Jetty/Tomcat startup failure | Missing system properties, filtered resources, classpath-only runtime deps |
| Duplicate classes | Bridge libraries, shaded/unpacked jars, dependency exclusions |
| Plugin version warnings | Parent/pluginManagement versions and reproducible build policy |

## Validation discipline

- Use skip flags only for local isolation while debugging.
- Final validation must run the project’s required tests and security gates unless the user explicitly approves a documented exception.
- For webapps, validate both build and runtime startup when the bug is runtime-only.
- Document non-obvious fixes as a learning if multiple failed approaches were needed.

## Useful commands

```bash
mvn -version
mvn help:effective-pom -Doutput=target/effective-pom.xml
mvn dependency:tree -Dverbose
mvn clean verify
```

## Related

- `skills/maven-release/SKILL.md`
- `rules/code-rules.md`
- `rules/security-check-required.md`
- `learnings/` for project-specific Maven gotchas
