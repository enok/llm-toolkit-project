---
title: AWS architecture diagram quality control
tags: [aws, architecture, plantuml, diagrams, quality, png]
---

# AWS architecture diagram quality control

Use this reference for AWS architecture diagrams, especially when exporting PNG artifacts for Markdown, PDFs, Jira, Confluence, or PR review.

## Sources reviewed

This guidance is adapted from:

- Local inspection of existing AWS PlantUML diagram sets in consumer repositories (a web application and a SageMaker-backed recommendation service), reviewed for reusable layout patterns and failure modes only.
- Official `awslabs/aws-icons-for-plantuml` examples: pinned release tags, AWS service macros, simplified views, and verb-labeled relations.
- Official AWS Architecture Icons: `https://aws.amazon.com/architecture/icons/`.
- AWS Solutions architecture overview diagrams, especially Data Transfer Hub, Account Assessment for AWS Organizations, and Workload Discovery on AWS.
- Official `plantuml-stdlib/C4-PlantUML` guidance: separate static structure, deployment/topology, and dynamic behavior into distinct views.
- Public skill repositories reviewed for organization patterns only: `anthropics/skills`, `VoltAgent/awesome-agent-skills`, and `travisvn/awesome-claude-skills`. Do not vendor or execute downloaded content unless the external-skill-intake process approves it.

## AWS architecture contract

An AWS architecture diagram answers: "What cloud resources, runtime boundaries, and infrastructure dependencies make up this deployed system?"

- Show AWS account/environment, region, VPC, subnet, security, application, messaging, storage, observability, and external-system boundaries when they materially affect the design.
- Use AWS Icons for PlantUML only for AWS-managed services. Use generic nodes for application code, internal services, controllers, third parties, and non-AWS systems.
- For final AWS documentation-style diagrams, source service icons from the official AWS Architecture Icons package or a verified local copy of it. Avoid third-party icon libraries as the authoritative source because they can lag official AWS releases.
- Use directional, verb-labeled relations such as `publishes`, `consumes`, `invokes`, `reads`, `writes`, `stores`, `emits metrics`, or `delivers`. Every edge starts at the initiator: a component that queries a datastore points at the datastore, a scheduler that invokes a function points at the function. Verify each edge's initiator against source evidence; a reversed query edge is a correctness defect even when the layout looks fine.
- When environments share a topology but differ in resource names, draw the diagram once with one environment's short names, lift shared name prefixes into group titles, and publish a node-to-resource-name mapping table per environment in the surrounding documentation. State provenance limits next to the diagrams — internals sourced from an external codebase, documentation-sourced branches with no code in the repo, inferred network placement, and which environment the deployed shape actually runs in — instead of leaving readers to assume everything is equally proven and live.
- Do not use numbered edge labels to document runtime ordering in an architecture view. Ordered steps, branch behavior, retries, callbacks, token lifecycle, and failure paths belong in sequence diagrams.
- When matching AWS Solutions documentation style, numbered process markers may appear on simple connectors only if the explanations live outside the diagram, as numbered text beneath or beside the image. Keep the diagram body clean: no resource inventory tables, timing/evidence cards, long legends, or report-style annotations.
- Keep legends short. If the legend explains an ordered request flow, split that flow into a sequence diagram and keep the AWS view focused on topology.
- Keep one architecture question per diagram. If the diagram needs both a system overview and endpoint-specific details, create a small overview plus focused detail diagrams.

## Layout standard

- Prefer left-to-right flow from callers to ingress, compute, messaging, storage, ML/runtime dependencies, and observability.
- Group by ownership boundary first, then by infrastructure responsibility.
- Keep actor/client nodes outside the AWS cloud boundary unless they are AWS-managed.
- Draw network boundaries only around resources that actually run inside them. Managed regional services such as Kinesis, EventBridge, CloudWatch, SNS, or public OpenSearch domains should not be placed inside VPC/subnet boxes unless source evidence shows a VPC attachment or endpoint-specific placement.
- Do not place service icons on boundary lines. Give icons and labels enough padding inside or outside each boundary so the boundary communicates containment instead of colliding with the resource.
- Put observability and configuration dependencies near the resources that use them, but avoid long crossing arrows across the full canvas.
- Split the diagram when it exceeds about 20 major nodes, has many long crossing arrows, needs more than a short legend, or becomes too wide for normal documentation review.

## Mandatory post-export PNG quality control

This gate is not optional. A diagram task is incomplete until every exported PNG has passed inspection or the failure is reported as a blocker.

1. Compile the PlantUML source with the repository's documented renderer.
2. Export SVG/PDF when supported. Export PNG only when the target requires raster output or the repository versions PNG artifacts.
3. If PNG is exported, verify actual pixel dimensions. Target at least 3000 px on the longest side for AWS architecture diagrams.
4. Open the actual exported PNG in an image viewer, browser, or `view_image`; do not rely on compilation success or file existence.
5. Inspect readability at the target documentation size: title, node labels, icons, boundaries, edge labels, legend, and arrow direction. Check every arrowhead against the initiator rule and check labels for literal markup fragments (`//...//`, `<size:...>`) that indicate a broken multi-line macro argument.
6. Fail the gate when the PNG is blurry, cropped, stale, unreadable, overly wide, visually sparse, crowded, has overlapping labels/arrows, uses wrong icons, or mixes runtime sequence detail into topology.
7. Compare the rendered diagram against current AWS reference diagrams, not just against itself. Use AWS Solutions diagrams as the visual bar for whitespace, boundary hierarchy, icon spacing, connector routing, and label brevity.
8. Fix the source, layout, export DPI/scale, or diagram split; re-export and repeat the inspection until acceptable.
9. Do not mark the diagram complete until the loop passes: create/update/improve, validate against AWS reference, decide whether it is at the target quality, and repeat when it is not.
10. Record the artifact path, dimensions, viewer used, pass/fail status, and any fixes made in the task report.

If the image cannot be opened or inspected in the current environment, do not claim it is ready. Report the exact artifact and blocker.

## Failure patterns seen in practice

- A broad application architecture overview exported as an 8500+ px-wide PNG with many numbered arrows and a long runtime legend. Fix by splitting overview topology from sequence/detail diagrams and replacing numeric ordering with verb-labeled relations.
- Endpoint architecture diagrams that use AWS icons correctly but still explain ordered request behavior through numbered arrows. Fix by creating paired AWS topology and sequence diagrams.
- PNG exports that exist but were not checked for dimensions, target-size readability, crop, and visual clarity. Fix by using SVG/PDF, higher DPI/scale, renderer settings, or a diagram split; do not upscale a poor PNG as the primary fix.
- Architecture diagrams with large empty regions and long crossing arrows. Fix by tightening grouping, moving support dependencies near consumers, or splitting unrelated flows.
- Architecture diagrams that look like internal reports because they embed resource-name tables, timing/evidence cards, or long explanatory notes. Fix by moving that information to the surrounding Markdown/Confluence/PDF text and keeping the diagram focused on topology.
- VPC/subnet boundaries that accidentally contain regional AWS managed services or have service icons sitting on the border. Fix by verifying deployment placement and redrawing the containment boundaries.
