---
title: AWS PlantUML style guide
tags: [aws, plantuml, diagrams, architecture]
---

# AWS PlantUML style guide

Use this reference when a repository already uses PlantUML for AWS architecture diagrams, or when the requested diagram needs AWS service icons.

## Source and attribution

This guide adapts reusable patterns from:

- Existing AWS-style PlantUML diagrams in consumer repositories.
- Official `awslabs/aws-icons-for-plantuml` documentation.
- Official `plantuml-stdlib/C4-PlantUML` documentation for C4 diagram scope and hierarchy.
- Public PlantUML skill patterns reviewed for validation/troubleshooting ideas only; do not vendor or execute third-party scripts without the external-skill-intake process.

## Include strategy

Prefer a pinned AWS Icons for PlantUML release tag, not `main`:

```plantuml
!define AWSPuml https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v23.0/dist
!include AWSPuml/AWSCommon.puml
!include AWSPuml/AWSSimplified.puml
```

If maintaining an existing diagram set, keep the existing pinned release unless intentionally upgrading the whole set. Do not mix release tags in related diagrams without a reason.

Include only the AWS service icon files actually used by the diagram:

```plantuml
!include AWSPuml/ApplicationIntegration/SimpleNotificationService.puml
!include AWSPuml/Compute/EC2.puml
!include AWSPuml/Compute/Lambda.puml
!include AWSPuml/Database/DynamoDB.puml
!include AWSPuml/General/Client.puml
!include AWSPuml/General/Users.puml
!include AWSPuml/ManagementGovernance/CloudWatch.puml
!include AWSPuml/Storage/SimpleStorageService.puml
```

## Standard component diagram skeleton

```plantuml
@startuml System_Component_View

!define AWSPuml https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v23.0/dist
!include AWSPuml/AWSCommon.puml
!include AWSPuml/AWSSimplified.puml
!include AWSPuml/ApplicationIntegration/SimpleNotificationService.puml
!include AWSPuml/Compute/Lambda.puml
!include AWSPuml/Database/DynamoDB.puml
!include AWSPuml/General/Users.puml
!include AWSPuml/ManagementGovernance/CloudWatch.puml

skinparam backgroundColor #FAFAFA
skinparam defaultFontName "Amazon Ember"
skinparam defaultFontSize 12
skinparam roundCorner 10
skinparam shadowing false
skinparam componentStyle rectangle
skinparam nodesep 60
skinparam ranksep 90
skinparam packageBorderColor #2E86AB
skinparam packageBackgroundColor transparent
skinparam componentBorderColor #F18F01
skinparam arrowColor #2E86AB
skinparam arrowFontColor #2E86AB
skinparam arrowFontSize 10
skinparam packageFontSize 14
skinparam packageFontStyle bold

title **System - Component View**\n**Short purpose statement**

Users(user, "Primary User", "Role")

package "Application / Service Boundary" as app #E8F4FD {
    rectangle "Controller / Entry Points" as entrypoints #FFE082 {
        component "Endpoint or Handler" as endpoint
    }
    rectangle "Business Logic" as logic #FFE082 {
        component "Service" as service
    }
}

package "Messaging" as messaging #E8F5E9 {
    SimpleNotificationService(topic, "topic-name", "SNS Topic")
}

package "Storage" as storage #E8F0FF {
    DynamoDB(table, "table_name", "DynamoDB Table")
}

CloudWatch(cloudWatch, "CloudWatch", "Metrics & Logs")

user --> endpoint : **HTTP / Event**\nkey inputs
endpoint --> service : **Process**
service --> topic : **Publish**
service --> table : **Read/Write**
service --> cloudWatch : **Metrics / Logs**

note right of endpoint
  **Endpoint Details:**
  • Method or trigger
  • Required inputs
  • Response / output
end note

@enduml
```

## Standard sequence diagram skeleton

```plantuml
@startuml System_Runtime_Sequence

!define AWSPuml https://raw.githubusercontent.com/awslabs/aws-icons-for-plantuml/v23.0/dist
!include AWSPuml/AWSCommon.puml
!include AWSPuml/AWSSimplified.puml
!include AWSPuml/ApplicationIntegration/SimpleNotificationService.puml
!include AWSPuml/Database/DynamoDB.puml
!include AWSPuml/General/Users.puml

!theme aws-orange
skinparam backgroundColor #FAFAFA
skinparam linetype ortho
skinparam nodesep 150
skinparam ranksep 300

title **System - Runtime Sequence**

actor "User or Caller" as user
participant "Application\nEntry Point" as controller
participant "Business\nService" as service
participant "SNS Topic" as topic
participant "DynamoDB\nTable" as table
participant "CloudWatch" as cloudWatch

user -> controller: **Request / Event**\nimportant inputs
activate controller
controller -> service: **Process request**
activate service

alt synchronous success path
    service -> table: **Read/Write**
    table --> service: Result
else asynchronous publish path
    service -> topic: **Publish message**
    topic --> service: Message ID
else failure path
    service -> cloudWatch: **Log error / emit metric**
end

service --> controller: Response / result
deactivate service
controller --> user: Response
deactivate controller

note over user, cloudWatch
  **Key points:**
  • Main decisions
  • Async boundaries
  • Persistence points
  • Monitoring signals
end note

@enduml
```

## Layout conventions extracted from proven diagrams

- Use one high-level summary diagram for broad system/API surface.
- Use paired component + sequence diagrams for each endpoint or major flow.
- Group nodes by responsibility: application boundary, request processing, configuration, messaging, downstream services, storage, external services, monitoring.
- Use AWS macros for AWS-native infrastructure: SNS, Lambda, EC2, DynamoDB, S3, API Gateway, Systems Manager, CloudWatch, SageMaker.
- Use generic `Client(...)` or plain `component` nodes for non-AWS third-party services, internal libraries, controllers, helpers, and processors.
- Keep actor/client nodes at the left/top, application in the center, downstream messaging/storage/external services to the right/bottom.
- Use notes to capture endpoint contracts, decision logic, response shapes, security constraints, and operational signals.
- Label async boundaries explicitly: SNS publish, Lambda trigger, HTTP callback, queue/topic response.
- For parallel flows in sequence diagrams, use `par`/`else`; for branch behavior, use `alt`/`else`.
- Avoid hard-coded project names in shared examples. Consumer docs may use real production names after source verification.

## Compile, export, and visual review gate

Always compile changed PlantUML before completion. Example:

```bash
java -jar "$PLANTUML_JAR" docs/architecture/*.puml
```

If no `PLANTUML_JAR` is configured, use the repo-documented renderer path or a known local jar. If generated images are tracked, confirm PNG/SVG outputs changed only for diagrams whose source changed.

After export, open the rendered PNG/SVG/PDF and inspect the actual visual output. Do not rely on compilation success alone. Improve and re-export when:

- labels overlap or are too small to read,
- arrows cross excessively or imply the wrong direction,
- AWS icons or boundaries make ownership unclear,
- the diagram is too wide/tall for normal documentation viewing,
- a summary diagram hides important branch behavior that should be split into focused diagrams.

For syntax-only troubleshooting, use:

```bash
java -jar "$PLANTUML_JAR" --check-syntax path/to/diagram.puml
```

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Ghost participant appears | Alias typo between declaration and usage | Use stable aliases and search for every alias reference |
| Remote include fails | No network or unpinned/unavailable URL | Use pinned release tags or local includes |
| Wide/huge diagram fails | PlantUML image size limit | Use `-DPLANTUML_LIMIT_SIZE=16384`, split the diagram, or reduce participant count |
| Syntax error around notes | Unsupported note placement for diagram type | Convert to `legend`, `note over`, or attach note to a declared participant |
| Icons missing | Service include missing or wrong category | Add the specific `AWSPuml/<category>/<service>.puml` include |

## Security and privacy

- Do not embed secrets, credentials, tokens, or PII in diagrams.
- Avoid internal hostnames in shared toolkit examples; consumer repo docs may include approved internal names when needed.
- Do not run downloaded third-party scripts unless they have been reviewed and passed the toolkit security check.
