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
4. Check local JDK/Maven versions against `pom.xml`, toolchains, CI tool names, and plugin requirements.
5. Inspect effective POM and active profiles before changing dependencies.
6. Verify exact artifact versions exist before proposing upgrades or parent properties.
7. Separate local-development bypasses from final validation gates.

## Common failure classes

| Symptom | Check |
| --- | --- |
| Shell path errors on Windows | Maven antrun/exec plugins assuming `/bin/sh` |
| `UnsupportedClassVersionError` | Dependency compiled for newer Java than runtime |
| OWASP dependency-check fail | Effective POM, active profiles, analyzer errors vs. confirmed CVEs |
| OpenClover dependency-check resolver error | Whether coverage instrumentation is contaminating the security-scan dependency graph |
| Jetty/Tomcat startup failure | Missing system properties, filtered resources, classpath-only runtime deps |
| Local Jetty startup cascade | Local-safe properties, Tomcat `-D` values, Log4j bridge coverage, lazy AWS/KPL beans |
| Stage/prod config ignored at runtime | WAR-packaged generated properties shadowing external `${catalina.base}/lib` config |
| Duplicate classes | Bridge libraries, shaded/unpacked jars, dependency exclusions |
| Plugin version warnings | Parent/pluginManagement versions and reproducible build policy |
| Parent property has no effect | Whether child POMs reference the property or the parent enforces it through `dependencyManagement` |
| Framework version cannot resolve | Published artifact coordinates, not legacy suffix conventions |
| Long Maven or Jetty output hides the root cause | Maven `-l <file>` logs and runtime markers in `references/legacy-java-webapp-runtime.md` |
| Local `-Denv=ci` Jetty run fails | Local-safe default ports and env-var-activated overrides |
| Spring Boot CI start binds to `8080` | `server.port` must read Jenkins `HTTP_PORT`, not only Maven plugin properties |
| Windows `.m2` artifact delete fails | Serial producer/consumer validation for sibling repos sharing local artifacts |
| Surefire fork says goodbye unexpectedly | Tests that leak thread interrupt status after asserting interruption behavior |
| Legacy dependency security upgrade breaks runtime | Java bytecode level, bridge class coverage, CVE suppression evidence, and runtime startup |
| Empirically correct fix still fails `mvn test` | Stale incremental/Clover-instrumented classes; `javap -c -p` the class the test loads, then `mvn clean test` (timestamps prove nothing) |
| `mvn clean install` appears to hang after tests pass | Lifecycle-bound `spring-boot:start` polling readiness; run the no-skip gate with the repository's documented CI profile |
| PowerMock test fails on Log4j2 XML init under JDK 17 | `@PowerMockIgnore` must delegate the full Java XML type family; see `references/legacy-java-webapp-runtime.md` |
| JDK 17 migration of a legacy Java 8 / Spring 4.3 / Maven 3.6 / Clover / PowerMock project | Audit Lombok, PowerMock CGLIB, Clover forked lifecycle, default plugin versions, Hamcrest, servlet API, and Spring URL behavior; see `references/jdk17-legacy-migration.md` |

## Maven security scanner triage

- Verify scanner prerequisites before changing CI. For OWASP dependency-check 12.x, CI Maven must be 3.6.3+; older Maven tool names such as `maven-3.3.9` need to be upgraded before the plugin can be trusted.
- Treat `failOnError` and vulnerability thresholds as separate controls. Thresholds such as `failBuildOnCVSS` fail on confirmed CVEs; `failOnError` decides whether analyzer/runtime errors also fail the build.
- For final CI gates, keep analyzer failures blocking unless the project has an explicit, reviewed exception with compensating evidence.
- If OpenClover or another instrumentation plugin injects phantom `provided` dependencies that break dependency-check, first isolate the scan from the instrumented profile, remove stale coverage artifacts, or run dependency-check against the normal dependency graph.
- Use `failOnError=false` only for local triage or an explicitly documented project exception; never silently weaken the final security gate. If a parent POM needs a Clover-specific exception, document the exception and let children that do not use Clover opt back into `failOnError=true`.

## Parent and framework version checks

- Maven parent POM version properties are inherited but opt-in. They affect children only when child dependencies reference the property, or when the parent also provides `dependencyManagement` such as an imported BOM.
- When the intent is only to expose a shared version, document that children must use the property explicitly. When the intent is enforcement, use `dependencyManagement` and verify the effective POM.
- Do not infer artifact names from old conventions. Spring Framework 5.3.x+ GA artifacts use versions such as `5.3.39`, not `5.3.39.RELEASE`; verify Maven Central or the configured repository before committing.

## Validation discipline

- Use skip flags only for local isolation while debugging.
- Final validation must run the project’s required tests and security gates unless the user explicitly approves a documented exception.
- For webapps, validate both build and runtime startup when the bug is runtime-only. See `references/legacy-java-webapp-runtime.md` for Maven log capture, Jetty lifecycle markers, CI/local port defaults, Windows local-repository locking, Surefire interrupt cleanup, Log4j 1.x bridge coverage, and Quartz Java 8 compatibility checks.
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
- `references/legacy-java-webapp-runtime.md`
- `references/jdk17-legacy-migration.md`
- `learnings/` for project-specific Maven gotchas
