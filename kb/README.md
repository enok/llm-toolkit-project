# Knowledge base runtime

Local vector index of this toolkit. A Chroma server and a small Python
service run in Docker; the CLI is `scripts/kb.py` (wrappers `scripts/kb.sh`,
`scripts/kb.ps1`).

- `docker-compose.yml` - the `llm-toolkit-kb` stack (`chroma`, `service`, `ingest`).
- `service/` - service image sources (`kb_core.py`, `store.py`, `ingest.py`, `service.py`).

Setup, configuration, CLI and API reference, security model, troubleshooting
and uninstall are in [docs/knowledge-base.md](../docs/knowledge-base.md).
Data (index, inbox, models, state) is never stored in this folder.
