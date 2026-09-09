---
title: Legacy Java webapp runtime troubleshooting
tags: [maven, jetty, tomcat, log4j, quartz, surefire, spring-boot, powermock, windows]
---

# Legacy Java Webapp Runtime Troubleshooting

Use this reference when Maven builds, Jetty startup, legacy Log4j compatibility,
or Java 8 dependency upgrades fail in ways compile-only checks do not expose.

## Maven Output Capture

- For long Maven runs, prefer Maven's own log file flag over shell pipes:
  `mvn ... -l target/build.log <goal>`.
- Keep the log path outside directories Maven will clean during the command, or
  create it under the module being run after `clean` has finished.
- Poll the log file directly for root-cause markers such as `Caused by:`,
  `BeanCreationException`, `ClassNotFoundException`, `NoClassDefFoundError`,
  `Started Jetty`, and `Context initialization failed`.
- Avoid relying only on agent or IDE terminal buffers for noisy Jetty runs; they
  can truncate the actual exception behind annotation-scan warnings.

## Windows and Cross-Repo Maven Validation

Windows file locking can turn healthy Maven builds into local-repository cleanup
failures when sibling repos validate in parallel. If one repo produces an
artifact consumed by another repo, validate the producer first and consumers
after the local artifact is stable.

- Treat `Cannot delete ...\.m2\repository\...` during
  `build-helper-maven-plugin:remove-project-artifact` as a validation
  orchestration issue until a serial rerun proves otherwise.
- Do not run producer `clean install` and consumer `clean install` in the same
  parallel batch on Windows when they share local artifacts.
- If a serial producer rerun passes, avoid code changes for the original
  locking failure.

## Jetty `run` Double Lifecycle

Some Maven Jetty setups bind `jetty:start` and `jetty:stop` to integration-test
phases while also allowing manual `jetty:run`. Invoking `mvn jetty:run` can
therefore start a transient integration-test server, stop it, and only then
start the persistent `default-cli` server.

- Do not treat the first `Started Jetty Server` line as sufficient readiness.
- Wait for the `jetty:...:run (default-cli)` marker, then use the following
  `Started Jetty Server` line as the local runtime target.
- Validate runtime-only dependency changes with the actual Jetty/Tomcat startup
  path, not only `mvn compile` or `mvn install`.

## CI Profiles Run Locally

CI Maven profiles are often useful for local reproduction, but local shells and
IDEs usually do not provide Jenkins-only environment variables.

- Keep local-safe defaults for `http.port`, `stop.port`, and similar Jetty
  properties in normal module properties.
- Put CI environment overrides behind profile activation that requires the
  corresponding environment variable, such as `env.HTTP_PORT` or
  `env.STOP_PORT`.
- When local `mvn ... -Denv=ci` fails with missing or invalid Jetty `stopPort`,
  evaluate the effective property before changing plugin versions:
  `mvn -pl <module> -Denv=ci help:evaluate -Dexpression=stop.port -q -DforceStdout`.

## Spring Boot Maven Start and Dynamic CI Ports

For Spring Boot services that bind `spring-boot:start` and `spring-boot:stop`
into the Failsafe lifecycle, Maven properties such as `http.port` do not change
the embedded server unless Spring itself reads them.

- If Jenkins allocates `HTTP_PORT`, bind Spring's runtime port directly:
  `server.port=${HTTP_PORT:8080}`.
- Keep the fallback local-safe, usually `8080`, so normal local runs still work.
- Do not remove `spring-boot:start` just to avoid a port collision; that can
  stop integration tests from exercising a live application.
- Validate with a non-8080 `HTTP_PORT` while 8080 is blocked, and confirm logs
  show Tomcat or Jetty initialized on the allocated port and `spring-boot:stop`
  completes.

## Local Jetty Startup Cascades

Legacy webapps often assume a deployed Tomcat runtime where startup scripts set
system properties, external files live under `${catalina.base}/lib`, and
container-level libraries are present. A local Jetty run can expose these
missing assumptions one at a time.

When startup fails with a chain of unrelated-looking errors, verify the whole
local runtime surface before treating the last stack trace as the root cause:

- Local-safe properties select local or no-op integrations for AWS, metrics,
  queues, streams, and host-name parsing. Avoid stage/prod values for local
  startup unless the task explicitly requires live cloud access.
- Maven resource filtering supplies Tomcat-only placeholders such as
  `catalina.base`, application name, version, instance id, host name, and log
  group values before Spring loads property files.
- Jetty plugin `systemProperties` mirrors the JVM properties normally provided
  by Tomcat startup scripts.
- Log4j 1.x compatibility jars cover the actual legacy classes referenced at
  runtime, including SPI, rolling appender, extras, and pattern parser classes.
- Expensive or cloud-backed beans are lazy at both the bean declaration and the
  injection site when a no-op local publisher should avoid constructing the real
  dependency graph.

Partial fixes are expected to reveal later startup failures. Keep validating
with the full local Jetty/Tomcat startup path until the final server-start
marker appears and a small request reaches the dispatcher.

## Stale Incremental Classes Mask Source Fixes

Maven incremental compilation can decide an edited class is up to date and keep
running tests against bytecode compiled from the pre-edit source — especially in
modules with source-instrumenting plugins (OpenClover, AspectJ, annotation
processors) that maintain their own compiled copies such as
`target/clover/classes`. Class-file timestamps prove nothing: a stale class can
carry a timestamp newer than the edit because the build touched or copied it
without recompiling. Checking the instrumented *source* copy is also not enough;
it can contain the fix while the compiled instrumented *class* does not.

When a test failure contradicts behavior you have empirically verified in
isolation (same input, same resolved dependency jar), stop debugging the code
and suspect stale build artifacts:

1. Decompile the class the test actually loads and look for the fix at bytecode
   level:

   ```bash
   javap -c -p target/classes/.../MyClass.class | grep -B5 "theMethodCall"
   ```

   If the bytecode still shows the old call signature, the class is stale
   regardless of timestamps.
2. Run `mvn clean test` scoped to the module; only draw further conclusions
   from the clean rebuild.

## Lifecycle-Bound Spring Boot Start Looks Like an Install Hang

A no-skip `mvn clean install` that passes every test, packages the artifact,
then appears to hang may be executing a `spring-boot:start` bound to
`pre-integration-test`: local startup fails (for example while loading
cloud-backed beans without credentials) and the plugin keeps polling for its
JMX readiness marker until the configured timeout. Increasing the command
timeout only waits longer.

- Inspect the lifecycle before changing code: `mvn help:effective-pom` shows
  the bound `spring-boot:start`/`stop` executions and active profiles.
- If the repository documents a CI profile that disables live start/stop
  executions, use it for the no-skip final gate (for example
  `mvn clean install -Denv=ci`), and run the project's mock/local Spring
  profile as a separate startup check.
- Do not invent credentials, and do not skip unit/integration tests to get
  past the apparent hang.

## PowerMock + Log4j2 XML on JDK 17

A JDK 17 test using `PowerMockRunner` can pass with Log4j 1 but fail as soon as
an SLF4J call initializes Log4j2 XML configuration, first as an
`IllegalAccessError` involving the JDK Xerces implementation and
`jdk.xml.internal.XMLSecurityManager`. Partial ignores are insufficient:
ignoring only `javax.xml.*` leaves the internal Xerces classes mis-loaded, and
adding only the Xerces package shifts the symptom to a loader-constraint
violation for `org.xml.sax.InputSource`, because related Java XML API types are
still loaded by different classloaders.

Delegate the complete Java XML API and implementation type family used by
Log4j2 to the platform classloader:

```java
@PowerMockIgnore({
    "javax.xml.*",
    "org.w3c.dom.*",
    "org.xml.sax.*",
    "com.sun.org.apache.xerces.*"
})
```

Keep existing unrelated ignore entries such as `javax.net.ssl.*`. Prove the fix
against the failing PowerMock test first, then run the full suite. Root cause:
PowerMock's custom classloader can define JDK XML implementation or API classes
in an unnamed module; Log4j2 initializes XML configuration through those types,
producing module-access violations or incompatible copies of the same API
class. Delegating the full XML family keeps them all in the JDK's `java.xml`
module and one classloader.

## Surefire and Interrupted Tests

When production code correctly catches `InterruptedException` and calls
`Thread.currentThread().interrupt()`, tests that trigger that path must clear
the interrupt flag before returning control to JUnit/Surefire.

```java
try {
    RuntimeException exception = assertThrows(RuntimeException.class, () -> subject.run());
    assertThat(exception.getCause(), instanceOf(InterruptedException.class));
} finally {
    Thread.interrupted();
}
```

Keep the production re-interrupt behavior. Clean up only the test runner
thread. A leaked interrupt flag can make the full suite fail later with a
misleading Surefire fork error even when the targeted test passes.

## Lightweight HTTP Client Tests

In older servlet stacks, WireMock or newer Jetty test utilities can conflict
with the application's pinned Jetty classes and fail before the client behavior
is exercised. For simple HTTP-client tests, prefer the JDK `HttpServer` first:
it is enough to return controlled status codes, headers, bodies, delays, and
empty responses without changing the webapp's dependency graph.

## Log4j 1.x Bridge Coverage

When migrating from Log4j 1.x APIs to Log4j2 runtime behavior, verify which jar
provides each legacy class.

- `org.slf4j:log4j-over-slf4j` covers common public Log4j 1.x API calls but not
  many SPI, appender, or extras classes.
- `org.apache.logging.log4j:log4j-1.2-api` covers the Apache-maintained Log4j
  1.x compatibility API backed by Log4j2.
- Legacy rolling appender classes under `org.apache.log4j.rolling.*` can require
  `log4j:apache-log4j-extras`; exclude transitive `log4j:log4j` so the unsafe
  original Log4j 1.x implementation is not reintroduced.
- If filtered-unpacking `apache-log4j-extras`, include rolling, extras, and the
  required pattern parser classes. Compile-only validation may miss missing
  `org.apache.log4j.pattern.*` classes that fail at Jetty startup.

## Packaged Local Properties Shadow Deployment Config

Generated local property files can accidentally be packaged inside
`WEB-INF/classes` and take precedence over the environment-specific files that
deployment scripts copy into `${catalina.base}/lib`. The symptom is a runtime
value that does not match the stage/prod config in source control, such as
metrics disabled while the deployed environment file enables them.

Inspect the deployable artifact, not only the repository file:

```powershell
tar -xOf $artifact envs/stage/lib/app.properties |
  Select-String 'DEPLOYMENT_GROUP_ID|ENABLE_CLOUDWATCH_METRICS|AWS_ENABLED'

jar tf $war |
  Select-String 'WEB-INF/classes/(app|brand|stream).*\\.properties'
```

Keep local generated properties for local Jetty, but exclude deploy-environment
property files from the WAR so servlet container classpath lookup cannot shadow
external config:

```xml
<packagingExcludes>
    WEB-INF/classes/app.properties,
    WEB-INF/classes/brand.properties,
    WEB-INF/classes/stream-config.properties
</packagingExcludes>
```

After packaging, confirm those exact files are absent from `WEB-INF/classes`
while the environment bundle still contains `envs/{env}/lib/*.properties`.

## Quartz on Java 8

Quartz 2.4.0 and newer require Java 11 bytecode. Java 8 runtimes must stay on a
Java 8-compatible Quartz version until the application runtime is upgraded.

- Treat `UnsupportedClassVersionError` as a runtime compatibility failure, not
  a Spring wiring failure.
- If a CVE fix is only available in Quartz 2.4.0+, pinning an older version on
  Java 8 requires a documented suppression with evidence that the vulnerable
  feature path is not used.
- For JNDI-related Quartz findings, verify scheduler properties, Spring
  `SchedulerFactoryBean` wiring, and datasource configuration before accepting
  the suppression.
- Once the app moves to Java 11+, remove the suppression and upgrade Quartz.

## Windows Shell and Security Upgrade Overlap

Legacy parent POMs can assume Unix shells in antrun or exec steps. On Windows,
fix or override those executions with portable Maven/Ant tasks before changing
application code. For example, use Ant `echo` to write generated properties
instead of shelling out to `/bin/sh`.

When dependency-security upgrades overlap with Windows shell, Jetty, Clover,
Log4j, or Quartz fixes:

- Verify proposed versions exist in the configured repositories before editing
  POMs.
- Prefer an upgrade or BOM pin when a patched version exists and is runtime
  compatible.
- Use an OWASP suppression only with concrete exploitability evidence, failed
  upgrade evidence, and a removal condition.
- Final validation must include compilation, tests, security scan, and runtime
  startup; skip flags are local triage tools, not proof.
