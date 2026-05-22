# Claude layout

`rules/`, `workflows/`, and `skills/` remain canonical for shared knowledge. The project subagent prompts live in `tool-subagents/`.

`.claude/agents` is a symlink to `../tool-subagents`. Do not add or edit files under `.claude/agents`; edit `tool-subagents/` instead.
