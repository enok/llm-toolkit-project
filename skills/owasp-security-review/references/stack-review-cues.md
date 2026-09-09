---
title: Stack-specific OWASP review cues
tags: [owasp, java, javascript, typescript, nodejs, python, react]
---

# Stack Review Cues

Use these cues to focus the audit after identifying the active stack.

## Java

- Check Spring/Security filters, controller authorization, validation annotations, XML/YAML parsing, deserialization, logging, Maven dependencies, and CI profiles.
- Prefer parameterized queries and framework encoders. Verify server-side authorization even when UI routes hide actions.
- For dependency CVE remediation in legacy Java webapps, verify runtime compatibility and classpath behavior before accepting a suppression or bridge library. Log4j 1.x compatibility, Quartz Java 8 pins, and Jetty/Tomcat startup should be validated with runtime evidence, not compile success alone.

## JavaScript, TypeScript, Node.js

- Check route middleware ordering, schema validation, SSRF-prone HTTP clients, command execution, file upload paths, dependency scripts, and secret handling.
- Verify type guards at trust boundaries; TypeScript types do not validate runtime input.

## Python

- Check Flask/FastAPI/Django auth decorators, ORM query construction, subprocess calls, pickle/YAML parsing, notebook credentials, and requirements locks.
- Confirm debug mode and admin endpoints are disabled outside local development.

## React

- Check DOM sinks, `dangerouslySetInnerHTML`, URL redirects, token storage, CSRF assumptions, and client-only authorization.
- Distinguish presentation bugs from server enforcement gaps; server-side controls carry the security fix.
