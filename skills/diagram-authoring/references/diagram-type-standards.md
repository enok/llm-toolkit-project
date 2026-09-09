---
title: Standard diagram type selection
tags: [diagrams, c4, aws, sequence, architecture, plantuml, mermaid]
---

# Standard diagram type selection

Use this reference when creating or updating architecture documentation. The goal is a consistent diagram set that separates static software structure, cloud topology, and runtime behavior.

## Required view set

| View | Diagram type | Primary question | Preferred notation |
| --- | --- | --- | --- |
| Components | C4 component diagram | What software components exist, who owns them, and how do they depend on each other? | C4-PlantUML when PlantUML is available; Mermaid C4 only when the repo standardizes on Mermaid |
| Architecture | AWS architecture diagram | Which AWS-managed resources, networks, data stores, queues/topics, compute, and observability services make up the deployed system? | AWS Icons for PlantUML with a pinned release tag |
| Details | Sequence diagram | What happens at runtime, in what order, including branches, retries, failures, async handoffs, and callbacks? | PlantUML sequence if the repo uses PlantUML; Mermaid sequence for Markdown-first repos |

When a feature or system has evidence for all three views, create or update all three. If one view is not applicable, add a short note in the surrounding Markdown explaining why.

## Type boundaries

- C4 component diagrams show code-level service/application structure, static dependencies, ownership, and trust boundaries. Do not include step numbers or retry branches there.
- AWS architecture diagrams show deployment topology and managed infrastructure. Use AWS icons only for AWS-managed services; use generic nodes for app code, third parties, and non-AWS systems.
- AWS architecture diagrams must not explain runtime ordering with numbered arrows or long step legends. Use verb-labeled relations in the topology view and move ordered runtime behavior to sequence diagrams.
- Sequence diagrams show behavior over time. Include success, branch, retry, timeout, failure, async publish/consume paths, and material stateful systems such as token/session, cache, calibration, mapping, or association tables.
- Flowcharts are optional summaries for business processes or onboarding. They do not replace C4, AWS, or sequence views for architecture documentation.

## Minimum content by view

| View | Required content |
| --- | --- |
| C4 component | `Person` or caller, `System_Boundary`/`Container_Boundary` as applicable, internal `Component` nodes, external systems, storage/queue dependencies, trust boundaries, ownership/technology labels, relationship labels, and a short legend when stereotypes/tags are used |
| AWS architecture | AWS account/environment boundary, region/VPC/subnet/security boundaries when relevant, compute, API ingress, messaging, storage, observability, external systems, and directional data/control flow |
| Sequence detail | Caller, entry point, internal services, AWS/downstream dependencies touched by the flow, stateful upstream/downstream stores that explain lifecycle context, `alt`/`else` for branches, `par` for concurrency, retry/timeout/failure paths, async handoffs, and final response/result |

## Evidence requirements

Before drawing, collect evidence for:

- Component names, entry points, packages/modules, owners, and dependencies from source code, build files, API definitions, or existing docs.
- AWS resources from infrastructure code, deployment templates, runtime config, environment variables, CloudFormation/Terraform/SAM/CDK, or verified operational docs.
- Runtime order from controllers, handlers, jobs, consumers, retry policies, queue/topic subscriptions, SDK calls, logs, tests, or traced behavior.
- Data stores that materially affect the runtime story, even when populated by
  an adjacent service. Mark indirect ownership with a note rather than omitting
  the state.

If a node cannot be proven, omit it or label the uncertainty in the surrounding documentation. Do not invent services to make a diagram look complete.

## Quality standard

- One diagram should answer one level of question. Split dense diagrams by boundary, feature, endpoint, job, or runtime path.
- Titles must include the system/feature name and view type, for example `Billing Sync - AWS Architecture`.
- Labels should use real service/resource names when approved for the destination repo. Shared toolkit examples must stay generic.
- Keep ticket IDs and issue-tracker references out of diagram titles, labels, and notes; put ticket context in the surrounding documentation. Diagram text ends up in page attachments and captions, and publish pipelines can reject ticket-ID patterns in page content.
- Relationships should be verb-based: `invokes`, `publishes`, `subscribes`, `reads`, `writes`, `emits`, `redirects`.
- Include a legend when notation, icons, colors, or relationship styles are not obvious.
- Compile/export the diagram, inspect every generated/exported image after export, and iterate until labels, spacing, grouping, and arrow direction are readable. This post-export quality-control step is mandatory.
- Generated images must follow `skills/diagram-authoring/references/diagram-export-quality.md` and `skills/image-quality-inspection/references/image-quality-gate.md`: prefer vector output, verify dimensions for required raster output, and fix/re-render until acceptable.

## External patterns reviewed

This standard is informed by:

- Official Anthropic Agent Skills examples for concise skill instructions and progressive disclosure.
- Public Mermaid skill patterns that classify diagram types explicitly, including C4, architecture, and sequence views.
- C4-PlantUML component and layout guidance for software structure diagrams.
- AWS Icons for PlantUML release-pinning and AWS icon usage guidance for infrastructure diagrams.
- Mermaid CLI and Kroki documentation for source-driven SVG/PNG export behavior.

Do not vendor third-party examples or scripts from these sources without following `skills/external-skill-intake/SKILL.md`.
