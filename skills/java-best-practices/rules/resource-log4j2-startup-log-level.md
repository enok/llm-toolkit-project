---
title: Feed Early Log4j2 Levels from Startup Properties
impact: MEDIUM
impactDescription: Log4j2 initializes before application property sources are reliable
tags: java, log4j2, logging, configuration, startup, deployment
---

## Feed early Log4j2 levels from startup properties

When logger levels must vary by deployment, pass a validated JVM system
property before the process starts instead of relying on application property
files or classpath resource lookups.

**Incorrect (ambiguous classpath lookup):**

```xml
<Property name="LOG_LEVEL">${bundle:app:LOG_LEVEL:-INFO}</Property>
```

Servlet containers and shaded applications can resolve packaged defaults before
external deployment files, and Log4j2 parses its configuration before many
framework property sources are available.

**Correct (startup-owned value):**

```bash
LOG_LEVEL="${LOG_LEVEL:-INFO}"
case "$LOG_LEVEL" in TRACE|DEBUG|INFO|WARN|ERROR) ;; *) LOG_LEVEL=INFO ;; esac
JAVA_OPTS="$JAVA_OPTS -DLOG_LEVEL=$LOG_LEVEL"
```

```xml
<Property name="LOG_LEVEL">${sys:LOG_LEVEL:-INFO}</Property>
<Logger name="com.example.service" level="${LOG_LEVEL}"/>
```

Keep the accepted values narrow, default to `INFO`, and scope dynamic levels to
the packages or classes that need runtime control. Do not use this pattern to
log PII or secrets at lower levels.
