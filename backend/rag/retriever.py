import math
import os

from dotenv import load_dotenv
from llama_index.core import StorageContext, VectorStoreIndex
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.schema import TextNode, NodeWithScore
from llama_index.core.vector_stores.types import MetadataFilter, MetadataFilters
from llama_index.retrievers.bm25 import BM25Retriever
from llama_index.vector_stores.pinecone import PineconeVectorStore
from pinecone import Pinecone
from supabase import create_client

from backend.models import embed_model as _embed_model
from backend.models import cross_encoder as _cross_encoder_model

load_dotenv()


# =============================================================================
# CONFIGURATION
# =============================================================================

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_INDEX   = os.getenv("PINECONE_INDEX_NAME", "resolvedesk-knowledge")

DENSE_TOP_K  = 10
SPARSE_TOP_K = 10
FINAL_TOP_K  = 3

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")


def _sigmoid(x: float) -> float:
    """Normalise a raw CrossEncoder logit score to the 0–1 range."""
    return 1.0 / (1.0 + math.exp(-x))


# =============================================================================
# HybridRetriever — LlamaIndex edition
# Loaded once at module import as a singleton. All 6 agents share this instance.
# =============================================================================

class HybridRetriever:

    def __init__(self):
        self._embed_model  = _embed_model
        self._reranker     = _cross_encoder_model

        print("[Retriever] Connecting to Pinecone...")
        pc             = Pinecone(api_key=PINECONE_API_KEY)
        pinecone_index = pc.Index(PINECONE_INDEX)
        vector_store   = PineconeVectorStore(pinecone_index=pinecone_index)

        # VectorStoreIndex.from_vector_store reads existing Pinecone data —
        # does NOT re-embed. Just a thin pointer to the live Pinecone index.
        self._vector_index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            embed_model=self._embed_model,
        )

        self._supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

        print("[Retriever] Loading chunks from Supabase for BM25...")
        self._bm25_retriever = self._build_bm25()

        print("[Retriever] Ready.")

    # ── BM25 build / rebuild ──────────────────────────────────────────────────

    def _build_bm25(self) -> BM25Retriever | None:
        """
        Build a BM25 index from every chunk in the Supabase chunks table.
        Returns None if there are no chunks yet (empty knowledge base).
        """
        result = self._supabase.table("chunks").select("*").execute()
        chunks = result.data or []
        if not chunks:
            print("[Retriever] chunks table is empty — BM25 disabled until first ingest.")
            return None
        nodes = [
            TextNode(
                text=c["text"],
                metadata={
                    "source":      c["source"],
                    "category":    c["category"],
                    "chunk_index": c["chunk_index"],
                },
                id_=c["chunk_id"],
            )
            for c in chunks
        ]
        return BM25Retriever.from_defaults(nodes=nodes, similarity_top_k=SPARSE_TOP_K)

    def rebuild_bm25(self) -> None:
        """
        Rebuild BM25 index from Supabase.
        Called by the ingest router after every upload or delete so the
        keyword search always reflects the current document set.
        """
        print("[Retriever] Rebuilding BM25 index from Supabase...")
        self._bm25_retriever = self._build_bm25()
        print("[Retriever] BM25 index rebuilt.")

    # ── Dense search (Pinecone) ───────────────────────────────────────────────

    def _dense_search(
        self, query: str, category: str | None
    ) -> list[NodeWithScore]:
        filters = None
        if category:
            filters = MetadataFilters(
                filters=[MetadataFilter(key="category", value=category)]
            )
        dense_retriever = VectorIndexRetriever(
            index=self._vector_index,
            similarity_top_k=DENSE_TOP_K,
            filters=filters,
        )
        return dense_retriever.retrieve(query)

    # ── Sparse search (BM25) ─────────────────────────────────────────────────

    def _sparse_search(
        self, query: str, category: str | None
    ) -> list[NodeWithScore]:
        if not self._bm25_retriever:
            return []
        results = self._bm25_retriever.retrieve(query)
        if category:
            results = [
                n for n in results
                if n.node.metadata.get("category") == category
            ]
        return results[:SPARSE_TOP_K]

    # ── Public API ────────────────────────────────────────────────────────────

    def retrieve(
        self, query: str, top_k: int = FINAL_TOP_K, category: str | None = None
    ) -> dict:
        """
        Run the full hybrid retrieval pipeline.

        Args:
            query:    User's question in plain text.
            top_k:    Number of chunks to return (default 3).
            category: Optional metadata filter — "policy", "faq", or "support".
                      Passed to both Pinecone and BM25 search.

        Returns:
            {
              "chunks": [
                  {
                    "text":        str,
                    "source":      str,   # e.g. "shipping_policy"
                    "category":    str,   # "policy" | "faq" | "support"
                    "chunk_index": int,
                  },
                  ...
              ],
              "best_score": float   # 0–1 sigmoid score of the top chunk.
                                    # FAQ agent uses this against RAG_SCORE_THRESHOLD.
            }
        """
        # ── Step 1: Dense search ─────────────────────────────────────────
        dense_results = self._dense_search(query, category)

        # ── Step 2: Sparse search ────────────────────────────────────────
        sparse_results = self._sparse_search(query, category)

        # ── Step 3: Merge + deduplicate (dense first = higher priority) ──
        seen_ids: set = set()
        merged: list[NodeWithScore] = []
        for nws in dense_results + sparse_results:
            nid = nws.node.node_id
            if nid not in seen_ids:
                seen_ids.add(nid)
                merged.append(nws)

        if not merged:
            return {"chunks": [], "best_score": 0.0}

        # ── Step 4: Rerank with CrossEncoder ─────────────────────────────
        # predict() returns raw logit scores (roughly -10 to +10)
        pairs      = [[query, nws.node.text] for nws in merged]
        raw_scores = self._reranker.predict(pairs)
        for nws, raw in zip(merged, raw_scores):
            nws.score = float(raw)
        merged.sort(key=lambda x: x.score, reverse=True)

        top = merged[:top_k]

        # CrossEncoder outputs raw logits (~-10 to +10). Sigmoid converts this to a probability-like score. The FAQ agent uses best_score against a threshold to decide whether the RAG result is confident enough to use.
        # Sigmoid normalises raw logits to 0–1 range
        raw_best   = top[0].score if top else 0.0
        best_score = _sigmoid(float(raw_best))

        return {
            "chunks": [
                {
                    "text":        nws.node.text,
                    "source":      nws.node.metadata.get("source", ""),
                    "category":    nws.node.metadata.get("category", ""),
                    "chunk_index": nws.node.metadata.get("chunk_index", 0),
                }
                for nws in top
            ],
            "best_score": round(best_score, 4),
        }


# =============================================================================
# SINGLETON
# Created once when this module is first imported.
# All 6 agents import `retriever` from here — they share this single instance.
# =============================================================================

retriever = HybridRetriever()
