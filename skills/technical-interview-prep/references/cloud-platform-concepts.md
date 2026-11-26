---
title: Cloud platform concepts and honest-bridge material for backend interviews
tags: [interview, aws, elastic-beanstalk, load-balancer, auto-scaling, kubernetes, eks, hpa, karpenter, api-gateway, apigee, observability, latency]
---

# Cloud Platform Concepts For Backend Interviews

Use this to explain concepts the candidate is unsure about and to build
honesty-bridge blocks. Every bridge starts with the honest scope sentence; the
mapping shows fluency, it never replaces the scope sentence.

## Load Balancing And Scaling Layers On AWS

- **Elastic Load Balancer (ALB/NLB).** One component: distributes traffic across
  healthy targets. It neither creates instances nor deploys code.
- **Auto Scaling Group.** Adds and removes EC2 instances from CloudWatch alarm
  thresholds; it is what actually scales.
- **Elastic Beanstalk.** A PaaS layer above both: provisions EC2 + Auto Scaling
  Group + load balancer and deploys the application. Scaling thresholds live in
  the environment's capacity settings or in versioned `.ebextensions` YAML; under
  the hood they are Auto Scaling policies driven by CloudWatch alarms.

## The Same Layers In Kubernetes

| Concern | Kubernetes object | AWS analogue |
| --- | --- | --- |
| Run N copies of an image | Deployment | Auto Scaling Group launch template |
| Stable address + balancing across pods | Service | internal load balancer |
| External entry | Service `LoadBalancer` or Ingress (AWS Load Balancer Controller) | provisions an NLB/ALB |
| Scale pods on CPU/memory/custom metrics | HorizontalPodAutoscaler | scaling policy on an alarm |
| Scale nodes when pods are `Pending` | Cluster Autoscaler or Karpenter | Auto Scaling Group size |

Cluster Autoscaler grows fixed-instance-type node groups; Karpenter chooses the
instance type at provisioning time to fit the pending pods, which usually packs
better and costs less.

**Portability bridge.** Deployment, Service, probe, resource, and HPA manifests
are the same on any conformant cluster (on-premises distributions included), so
moving to EKS is mainly a change of control plane and cloud integrations
(load-balancer controller, IAM, storage classes), not a rewrite. Say it only
after the honest scope sentence.

## Spring Boot On EKS - Checklist

- Image built in CI, pushed to ECR; deployed with Helm or Kustomize.
- Deployment + Service + Ingress through the AWS Load Balancer Controller (ALB).
- Readiness, liveness, and startup probes on Spring Boot Actuator health groups.
- Resource requests and limits; HPA on CPU or a custom metric.
- Rolling update with `maxUnavailable: 0` plus a PodDisruptionBudget.
- IAM Roles for Service Accounts (IRSA) instead of node-wide credentials.
- JVM sized to the container: `-XX:MaxRAMPercentage`.
- Debugging: `kubectl describe`, `logs`, `top`, events, `rollout undo`;
  recognise `CrashLoopBackOff` and `OOMKilled`.

## API Gateways

**AWS API Gateway in front of Kubernetes.** The gateway does not reach pods
directly: a private integration goes through a VPC Link to an NLB/ALB, which
forwards to the pods. HTTP API is cheaper and has a native JWT authorizer; REST
API adds usage plans, API keys, request validation, caching, and WAF. Stages are
managed as code (for example Terraform), with CloudWatch access logs.

**Status codes to explain.** 429 means throttling - the client retries with
exponential backoff and jitter. 504 means the integration timed out (REST API
integrations default to about 29 seconds).

**Apigee -> AWS API Gateway mapping** (for candidates whose production gateway
experience is Apigee):

| Apigee | AWS API Gateway |
| --- | --- |
| API proxy | API (resources, methods, integrations) |
| Environment | Stage |
| API product + quota | Usage plan + API key |
| Spike arrest | Throttling (429) |
| OAuth / VerifyAPIKey policies | JWT (Cognito/OIDC) authorizer or Lambda authorizer |
| Target endpoint | Integration (Lambda, HTTP, VPC Link) |

Honest bridge shape: "My production gateway depth is in Apigee; on AWS API
Gateway my production exposure is limited (for example fronting Lambda). The
concepts map one to one: ..." - then the table, then a realistic ramp-up claim.

## Reusable Architecture Talking Points

Generic shapes that recur in backend experience stories. Fill them only with the
candidate's confirmed facts.

- **Asynchronous request-reply.** The first call triggers slow work (enrichment
  from several services, model inference) and persists the result; a later call
  fetches it. Start the work when the user reaches an earlier step of the UX so
  the final call feels instant; the latency target then applies end to end.
- **Graceful degradation.** When the slow result is not ready or a dependency
  fails, return a sensible default (for example a non-personalised ranking)
  instead of an error, so the revenue path never dead-ends.
- **Measuring end-to-end latency (p95, not average).** Take a business key that
  exists from the first request (an order ID beats a random correlation ID
  because it carries meaning), propagate it in headers through every service,
  queue, and async step, and close the timing in the last hop. Start with a
  hand-built implementation, evolve to distributed tracing (for example AWS
  X-Ray); aggregate logs by the same key (for example CloudWatch) to read one
  request's chronology across services, queues included.
- **Legacy-to-microservices integration migration.** Contract-first (WSDL/XSD
  for SOAP, OpenAPI for REST), SOAP and REST coexisting during the migration, an
  API gateway in a hybrid on-premises plus cloud setup, and business rules
  orchestrated as BPMN process flows with an internal view where business teams
  follow each process instance.
- **CI/CD ownership.** When platform teams owned the pipelines, say so and state
  the hands-on part ("I worked with them daily and know how both pipelines
  work"); do not claim ownership.
