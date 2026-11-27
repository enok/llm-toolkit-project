"""Vector-store adapter: the only module that imports chromadb.

The chromadb import is deferred to :func:`connect` so the pure helpers here
(collection metadata, metadata filters) and the ``KBStore`` wrapper can be
unit-tested with a fake collection and no chromadb installed.
"""

from __future__ import annotations

import logging
import time

log = logging.getLogger("kb.store")

PAGE = 1000
UPSERT_BATCH = 64


def collection_metadata(sync_safe: bool) -> dict:
    """Cosine space; with ``sync_safe`` the HNSW index never syncs to disk (vectors stay in SQLite)."""
    meta = {"hnsw:space": "cosine"}
    if sync_safe:
        meta["hnsw:sync_threshold"] = 1000000
        meta["hnsw:batch_size"] = 100
    return meta


def build_where(kinds=None, source=None) -> dict | None:
    """Chroma ``where`` filter for optional kind(s) and source (one name or a list of names)."""
    clauses = []
    if kinds:
        kinds = [kinds] if isinstance(kinds, str) else list(kinds)
        clauses.append({"kind": kinds[0]} if len(kinds) == 1 else {"kind": {"$in": kinds}})
    if source:
        sources = [source] if isinstance(source, str) else list(source)
        clauses.append({"source": sources[0]} if len(sources) == 1 else {"source": {"$in": sources}})
    if not clauses:
        return None
    return clauses[0] if len(clauses) == 1 else {"$and": clauses}


def _first(result: dict, key: str) -> list:
    value = result.get(key) or [[]]
    return value[0] or []


class KBStore:
    """Thin wrapper over one collection. Every method takes and returns plain data."""

    def __init__(self, collection):
        self.collection = collection

    # ---------------------------------------------------------------- write side

    def existing_files(self, source: str) -> dict:
        """``{path: {"file_sha": str, "chunks": int}}`` for all files of ``source`` in the index."""
        files: dict = {}
        offset = 0
        while True:
            res = self.collection.get(where={"source": source}, include=["metadatas"], limit=PAGE, offset=offset)
            metas = res.get("metadatas") or []
            for meta in metas:
                meta = meta or {}
                path = meta.get("path")
                if not path:
                    continue
                sha = str(meta.get("file_sha", ""))
                entry = files.setdefault(path, {"file_sha": sha, "chunks": int(meta.get("chunks", 0) or 0)})
                if entry["file_sha"] != sha:
                    entry["file_sha"] = ""  # mixed generations: force a re-index
            if len(metas) < PAGE:
                break
            offset += PAGE
        return files

    def upsert_file(self, source: str, path: str, records: list) -> None:
        """Replace the chunks of one file. ``records`` = [(id, document, metadata)]."""
        for i in range(0, len(records), UPSERT_BATCH):
            batch = records[i:i + UPSERT_BATCH]
            self.collection.upsert(
                ids=[r[0] for r in batch],
                documents=[r[1] for r in batch],
                metadatas=[r[2] for r in batch],
            )
        # drop surplus chunks left by an older, longer version of the same file
        self.collection.delete(
            where={"$and": [{"source": source}, {"path": path}, {"chunk": {"$gte": len(records)}}]}
        )

    def delete_file(self, source: str, path: str) -> None:
        self.collection.delete(where={"$and": [{"source": source}, {"path": path}]})

    # ---------------------------------------------------------------- read side

    def count(self) -> int:
        return int(self.collection.count())

    def search(self, q: str, k: int = 5, max_distance: float | None = None, kinds=None, source=None) -> list:
        if self.count() == 0:
            return []
        res = self.collection.query(
            query_texts=[q],
            n_results=int(k),
            where=build_where(kinds, source),
            include=["documents", "metadatas", "distances"],
        )
        hits = []
        for doc, meta, dist in zip(_first(res, "documents"), _first(res, "metadatas"), _first(res, "distances")):
            if max_distance is not None and dist is not None and float(dist) > float(max_distance):
                continue
            meta = meta or {}
            hits.append({
                "source": meta.get("source", ""),
                "path": meta.get("path", ""),
                "kind": meta.get("kind", ""),
                "title": meta.get("title", ""),
                "heading": meta.get("heading", ""),
                "chunk": meta.get("chunk", 0),
                "chunks": meta.get("chunks", 0),
                "distance": round(float(dist), 4) if dist is not None else None,
                "text": doc or "",
            })
        return hits

    def nearest(self, texts: list, k: int = 3, source=None) -> list:
        """Nearest chunks over several query texts, best distance per (source, path, heading)."""
        if not texts or self.count() == 0:
            return []
        res = self.collection.query(
            query_texts=list(texts),
            n_results=int(k),
            where=build_where(None, source),
            include=["metadatas", "distances"],
        )
        best: dict = {}
        for metas, dists in zip(res.get("metadatas") or [], res.get("distances") or []):
            for meta, dist in zip(metas or [], dists or []):
                if dist is None:
                    continue
                meta = meta or {}
                key = (meta.get("source", ""), meta.get("path", ""), meta.get("heading", ""))
                if key not in best or float(dist) < best[key]:
                    best[key] = float(dist)
        ranked = sorted(best.items(), key=lambda kv: kv[1])[: int(k)]
        return [
            {"source": s, "path": p, "heading": h, "distance": round(d, 4)}
            for (s, p, h), d in ranked
        ]

    # ---------------------------------------------------------------- read-back check (/verify)

    def sample_embeddings(self, n: int = 3) -> list:
        """``[(id, [float, ...])]`` for up to ``n`` stored chunks (vectors never leave the service)."""
        res = self.collection.get(limit=int(n), include=["embeddings"])
        ids = list(res.get("ids") or [])
        embeddings = res.get("embeddings")
        if embeddings is None:
            embeddings = []
        out = []
        for rid, vec in zip(ids, list(embeddings)):
            out.append((rid, [float(x) for x in (vec if vec is not None else [])]))
        return out

    def query_vector(self, vector: list, k: int = 1) -> list:
        """``[(id, distance)]`` nearest to a raw vector."""
        res = self.collection.query(query_embeddings=[list(vector)], n_results=int(k), include=["distances"])
        return [(rid, float(d)) for rid, d in zip(_first(res, "ids"), _first(res, "distances")) if d is not None]


def connect(host: str, port: int, collection: str, sync_safe: bool = True) -> KBStore:
    import chromadb  # deferred: only this module ever imports it
    from chromadb.config import Settings

    client = chromadb.HttpClient(host=host, port=int(port), settings=Settings(anonymized_telemetry=False))
    col = client.get_or_create_collection(name=collection, metadata=collection_metadata(sync_safe))
    return KBStore(col)


def connect_with_retry(cfg, attempts: int = 60, delay: float = 2.0) -> KBStore:
    """Connect to the Chroma server, waiting for it to come up (container start order)."""
    last = None
    for _ in range(max(1, attempts)):
        try:
            return connect(cfg.chroma_host, cfg.chroma_port, cfg.collection, cfg.sync_safe_index)
        except Exception as exc:  # noqa: BLE001 - any connection failure is retried
            last = exc
            time.sleep(delay)
    raise RuntimeError(f"vector store unreachable ({type(last).__name__})")
