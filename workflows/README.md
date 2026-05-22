# Workflows

Step-by-step instructions for repeatable work. Use workflows when the user asks for a process or outcome that benefits from a sequenced checklist. Use skills when the agent should auto-select an on-demand capability from metadata.

## Core Engineering

| Workflow | Use when |
| --- | --- |
| `project-execution-main.md` | Orchestrating broad technical work in this data-science toolkit context |
| `project-discovery.md` | Understanding a repo, architecture, flows, and setup |
| `review.md` | Reviewing a diff for correctness, security, architecture, and tests |
| `review-and-fix.md` | Reviewing, fixing, and validating a change loop |
| `ticket-review.md` | Ticket/PR/branch review with structured findings |
| `ticket-review-and-fix.md` | Review plus scoped fixes and verification |
| `pre-pr-check.md` | Full validation gate before PR or push |
| `run-tests.md` | Selecting and running the smallest meaningful checks |
| `update-docs.md` | Keeping docs aligned with a code or workflow change |
| `commit-and-push.md` | Commit structure, rebase, duplicate gate, and push |
| `capture-learning.md` | Capturing a reusable trial-and-error discovery |
| `cross-repo-impact.md` | Mapping impact across sibling repos or downstream consumers |
| `new-backend-feature.md` | Adding a backend endpoint, service, or API capability |
| `self-improvement.md` | Capturing mistakes and turning repeated value into toolkit capability |
| `toolkit-maintenance.md` | Maintaining this shared toolkit safely |

## Tickets, CI, Releases

| Workflow | Use when |
| --- | --- |
| `ticket-research.md` | Researching a ticket before implementation |
| `ticket-implementation.md` | Implementing from a research brief |
| `ticket-research-and-implementation.md` | Research then implement in one session |
| `ticket-research-and-implementation-and-validation.md` | Research, implement, review, fix, and validate |
| `gh-address-comments.md` | Addressing PR review comments |
| `gh-fix-ci.md` | Diagnosing and fixing failing GitHub Actions or CI |
| `pr-automation-review.md` | Handling PR automation or bot findings |
| `dependency-upgrade.md` | Upgrading libraries, runtimes, or dependency constraints |
| `ticket-release.md` | Maven release preparation, deployment verification, and downstream updates |
| `security-check-required.md` | Minimum security review gate for risky changes |
| `security-report.md` | OWASP-style or application security report |

## Documentation And Diagrams

| Workflow | Use when |
| --- | --- |
| `document-creation.md` | Architecture docs, diagrams, or technical documentation |
| `confluence-documentation.md` | Safe Confluence page CRUD and sync |
| `markdown-pdf-export.md` | Generating and verifying PDFs from Markdown |
| `documentation-sync-project.md` | Syncing project-specific documentation |
| `bilingual-doc-sync.md` | Keeping bilingual docs synchronized |
| `paired-doc-sync.md` | Keeping paired documents aligned |
| `translation-sync.md` | Translation consistency and drift checks |

## Data Science, Thesis, And Notebooks

| Workflow | Use when |
| --- | --- |
| `notebook-analysis.md` | Notebook EDA, analysis, cleanup, or reporting |
| `notebook-analysis-update.md` | Updating an existing notebook analysis |
| `notebook-to-script.md` | Promoting notebook logic into scripts |
| `notebook-latex-polish.md` | Polishing math and LaTeX in notebooks |
| `ml-experiment.md` | Running an ML experiment |
| `ml-experiment-update.md` | Updating an ML experiment |
| `experiment-result-update.md` | Refreshing experiment conclusions and artifacts |
| `research-analysis-cycle.md` | Iterative evidence-heavy research analysis |
| `analysis-validation.md` | Validating analysis outputs and claims |
| `thesis-writing-main.md` | Thesis writing orchestration |
| `thesis-completion-guide.md` | Final thesis completion guidance |
| `thesis-bibliography-integration.md` | Integrating bibliography into thesis decisions |
| `thesis-plagiarism-check.md` | Similarity/plagiarism review workflow |
| `tcc-method-selection.md` | Selecting thesis methods |
| `tcc-analysis-and-writing-sync.md` | Keeping analysis and TCC narrative aligned |
| `tcc-formatting-abnt-review.md` | ABNT formatting review |
| `refresh-usp-mba-course-context.md` | Refreshing local course context |
| `course-material-grounding.md` | Grounding decisions in course material |

## Data Pipelines And Governance

| Workflow | Use when |
| --- | --- |
| `data-source-ingestion.md` | Onboarding or updating data sources |
| `dataset-onboarding.md` | Documenting a new dataset |
| `data-pipeline-change.md` | Shared data pipeline changes |
| `pipeline-change-project.md` | Project-specific pipeline changes |
| `aws-data-pipeline-ops.md` | AWS data pipeline operations |
| `aws-data-platform-ops.md` | AWS data platform operations |
| `aws-airflow-terraform-change.md` | Airflow/Terraform changes |
| `aws-airflow-terraform-project.md` | Project-specific Airflow/Terraform guidance |
| `bilingual-notebook-sync.md` | Notebook translation synchronization |

## How To Invoke

- Ask naturally: "run the pre-PR check", "review and fix this branch", "export this Markdown to PDF".
- Use `INTENTS.md` for routing.
- Reference the file directly when you want a specific workflow.

Many workflows can fan out independent read-only lanes; follow `rules/multi-agent-orchestration.md` when doing so.
