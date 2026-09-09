---
title: Agent evolution discovery sources
tags: [agents, orchestration, evaluation, self-improvement, intake, security]
---

# Agent Evolution Sources

Use these sources as discovery inputs for improving orchestrators, evaluator loops, subagent prompts, and agent-quality gates. Do not run downloaded code or vendor opaque content. Review source, license, risk, and applicability before adapting any pattern.

## Patterns to prefer

- Start simple, then add multi-step orchestration only when it improves outcomes enough to justify cost and latency.
- Use routing and orchestrator-worker patterns for separable work; use evaluator-optimizer loops when there are clear criteria and iterative refinement improves quality.
- Judge subagent results before reducing them: evidence, scope fit, conflicts, validation value, and actionability.
- Capture traces, scores, human feedback, and LLM-as-judge output as evidence, then promote only repeated, validated lessons.
- Keep self-improvement bounded: propose durable updates to skills, workflows, rules, subagents, references, scripts, or gates; root agents still own edits and validation.

## Published evidence sources

| Source | Useful pattern | Intake note |
| --- | --- | --- |
| `https://www.anthropic.com/engineering/building-effective-agents` | Simple composable workflows; routing, orchestrator-workers, evaluator-optimizer; human review for broader system fit | Official engineering guidance; adapt patterns, not implementation-specific wording. |
| `https://developers.openai.com/cookbook/examples/partners/self_evolving_agents/autonomous_agent_retraining` | Feedback loop using traces, evals, LLM-as-judge, human review, prompt refinement, and retry limits | Official cookbook example; use as process inspiration, not an automatic retraining mandate. |
| `https://www.superannotate.com/blog/llm-agents` | Agent components: planning, memory, tools, feedback, critique, and self-reflection | Blog source; verify claims against implementation needs. |
| `https://www.eigent.ai/blog/self-evolved-agents` | Self-evolved-agent framing and continuous improvement concepts | Blog source; use only generic, validated ideas. |
| `https://cameronrwolfe.substack.com/p/agent-evals` | Agent evaluation framing and regression-oriented eval thinking | Direct fetch may be blocked; use only if accessible and reviewed. |

Vendor whitepapers and conference PDFs can be useful for use-case framing (pick one measurable use case, document lessons, then scale), but do not commit or vendor the PDF itself — record the takeaway and the citation only.

## Community repo discovery shortlist

Use `gh repo view` or read-only web review before adapting anything:

| Repository | Why inspect | Intake note |
| --- | --- | --- |
| `https://github.com/openai/evals` | LLM and LLM-system evaluation registry and framework | Review license terms before copying; prefer eval patterns and terminology. |
| `https://github.com/Arize-ai/phoenix` | AI observability and evaluation patterns | Use for trace/eval concepts; avoid adding runtime dependencies unless requested. |
| `https://github.com/langchain-ai/langgraph` | Durable graph-based agent orchestration patterns | MIT-licensed at last review; still inspect exact files before reuse. |
| `https://github.com/microsoft/autogen` | Multi-agent orchestration and conversation patterns | License differs by content; inspect before adapting. |
| `https://github.com/crewAIInc/crewAI` | Collaborative multi-agent role/task patterns | Use as conceptual input only unless a concrete import passes security review. |
| `https://github.com/confident-ai/deepeval` | LLM evaluation patterns and metric naming | Apache-2.0 at last review; still inspect exact files before reuse. |

Star counts and "awesome" listings are not audits. Treat every listed repository as executable code until reviewed.

## Promotion checklist

- [ ] The source pattern maps to a real repeated failure or capability gap.
- [ ] The result can be made provider-neutral and project-neutral.
- [ ] A smaller existing rule, workflow, skill, subagent, reference, script, or validation gate cannot absorb it.
- [ ] External URLs are recorded and Trust Hub checked when applicable.
- [ ] New local skills are scanned by SkillSpector and Snyk Agent Scan when prerequisites are available.
- [ ] `scripts/validate-toolkit-indexes.sh` and `scripts/security-check-toolkit.sh` pass, or blockers are reported.
