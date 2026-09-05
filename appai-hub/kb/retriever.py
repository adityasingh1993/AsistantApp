"""
kb/retriever.py
ChromaDB-based RAG retriever for per-app knowledge bases.

Each app gets its own ChromaDB collection.  Source-code chunks are tagged
with content_type="source_code" and are filtered out for non-developer roles
at retrieval time, enforcing the code-confidentiality policy.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

# content_type values that are only visible to developers / super-admins
_CODE_CONTENT_TYPES = {"source_code"}


class KBRetriever:
    """
    ChromaDB-backed knowledge base retriever.

    Args:
        chromadb_path:       Path where ChromaDB persists data.
        embedding_model:     Ollama embedding model name (e.g. "nomic-embed-text").
        embedding_base_url:  Base URL for the Ollama embedding endpoint.
    """

    def __init__(
        self,
        chromadb_path: str = "./data/chromadb",
        embedding_model: str = "nomic-embed-text",
        embedding_base_url: str = "http://localhost:11434",
    ):
        import chromadb
        from chromadb.config import Settings

        self._client = chromadb.PersistentClient(
            path=chromadb_path,
            settings=Settings(anonymized_telemetry=False),
        )

        # Use Ollama embeddings through langchain-community
        from langchain_community.embeddings import OllamaEmbeddings
        from chromadb.utils.embedding_functions import EmbeddingFunction

        # Wrap LangChain Ollama embeddings in a ChromaDB-compatible callable
        _lc_embedder = OllamaEmbeddings(
            model=embedding_model,
            base_url=embedding_base_url,
        )

        class _OllamaEmbeddingFn(EmbeddingFunction):
            def __call__(self, input: list[str]):
                return _lc_embedder.embed_documents(input)

        self._embedding_fn = _OllamaEmbeddingFn()
        logger.info(
            "KBRetriever initialised: chromadb_path=%s embedding=%s",
            chromadb_path, embedding_model,
        )

    # ── internal ─────────────────────────────────────────────────────────────

    def _collection_name(self, app_id: str) -> str:
        """Sanitise app_id for use as a ChromaDB collection name."""
        return f"app_{app_id.replace('-', '_')}"

    def get_or_create_collection(self, app_id: str, role: str = "app_user"):
        """
        Return (or create) the ChromaDB collection for the given app.

        Note: RBAC filtering is applied at query time (retrieve()), not here,
        because ChromaDB collections are shared across roles.
        """
        name = self._collection_name(app_id)
        collection = self._client.get_or_create_collection(
            name=name,
            embedding_function=self._embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )
        return collection

    # ── public API ───────────────────────────────────────────────────────────

    async def add_documents(self, app_id: str, documents: list[dict]):
        """
        Upsert documents into the app's ChromaDB collection.

        Args:
            app_id:    Target app identifier.
            documents: List of dicts with keys:
                         - content (str)
                         - metadata (dict with content_type, source, …)
        """
        import uuid as _uuid

        collection = self.get_or_create_collection(app_id)
        ids, texts, metadatas = [], [], []

        for doc in documents:
            doc_id = str(_uuid.uuid4())
            ids.append(doc_id)
            texts.append(doc["content"])
            meta = doc.get("metadata", {})
            # Ensure content_type is always present for filtering
            meta.setdefault("content_type", "user_doc")
            meta.setdefault("source", "unknown")
            metadatas.append(meta)

        collection.upsert(ids=ids, documents=texts, metadatas=metadatas)
        logger.info("KBRetriever: added %d docs to app=%s", len(documents), app_id)

    async def retrieve(
        self,
        app_id: str,
        query: str,
        role: str,
        n_results: int = 5,
        cloud_safe: bool = False,
    ) -> list[str]:
        """
        Retrieve the top-n relevant text chunks for the query.

        Two independent filters protect source code:

        1. **Role filter** (always active): source_code chunks are excluded
           for any role that does not have ``can_see_source_code`` permission.

        2. **Cloud-safe filter** (active when cloud_safe=True): source_code
           chunks are ALWAYS excluded, even for developers, when the Hub is
           configured to use a cloud LLM provider (OpenAI, Anthropic, etc.).
           This enforces the rule: *code never leaves the machine without
           explicit permission*.

        Args:
            app_id:     App whose KB to query.
            query:      User query text.
            role:       Caller's RBAC role string.
            n_results:  Maximum number of chunks to return.
            cloud_safe: If True, strip source_code chunks regardless of role.
                        Set by the WebSocket server when the active LLM backend
                        is a cloud provider.

        Returns:
            List of text chunks (strings).
        """
        from auth.rbac import RolePermissions

        collection = self.get_or_create_collection(app_id, role)

        # Determine whether source_code must be excluded:
        #   - always excluded if cloud_safe (LLM is cloud provider)
        #   - always excluded if the caller's role cannot see code
        exclude_code = cloud_safe or not RolePermissions.can_see_source_code(role)

        if exclude_code:
            if cloud_safe:
                logger.debug(
                    "KBRetriever: cloud_safe=True — stripping source_code "
                    "chunks from context (code must not leave the machine)"
                )
            where_filter = {"content_type": {"$nin": list(_CODE_CONTENT_TYPES)}}
        else:
            where_filter = None

        try:
            results = collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter,
                include=["documents"],
            )
            docs = results.get("documents", [[]])[0]
            return docs
        except Exception as exc:
            logger.error("KBRetriever.retrieve error: %s", exc, exc_info=True)
            return []

    def delete_collection(self, app_id: str):
        """Delete the entire ChromaDB collection for an app (destructive)."""
        name = self._collection_name(app_id)
        self._client.delete_collection(name)
        logger.info("KBRetriever: deleted collection for app=%s", app_id)
