# Knowledge base runtime

Local vector index of this toolkit. A Chroma server and a small Python
service run in Docker; the CLI is `scripts/kb.py` (wrappers `scripts/kb.sh`,
`scripts/kb.ps1`).

- `docker-compose.yml` - the `llm-toolkit-kb` stack (`chroma`, `service`, `ingest`); only `service` publishes a port, on `127.0.0.1`.
- `service/` - service image sources (`kb_core.py`, `store.py`, `ingest.py`, `service.py`).

Sources: `repo` (the corpus checkout), `inbox` (pending items) and `plugins`
(capability cards of installed plugins written by `scripts/plugins.py catalog`,
status `external`). Search and dedupe cover `repo` and `inbox` unless a request
names `plugins` or `all`; the prompt hook serves `repo` only. See
[docs/plugins.md](../docs/plugins.md).

Setup, configuration, CLI and API reference, security model, troubleshooting
and uninstall are in [docs/knowledge-base.md](../docs/knowledge-base.md).
Data (index, inbox, models, state) is never stored in this folder.
