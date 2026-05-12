# =============================================================================
# backend/models.py
# =============================================================================
# ResolveDesk — Shared Model Singletons
#
# WHAT THIS DOES:
#   Loads the embedding model and CrossEncoder reranker ONCE at startup.
#   Both retriever.py and ingest.py import from here instead of each loading
#   their own copy — halves the RAM used by embeddings.
#
# WHY BGE-BASE instead of BGE-M3?
#   BGE-M3 (1024-dim, 2.3 GB) is designed for multilingual queries and very
#   long documents. CartFlow support is English-only with short policy chunks.
#   BGE-base (768-dim, 109 MB) matches BGE-M3's quality on this use case at
#   21x less RAM. Pinecone index dimension must be 768 to match.
#
# RAM SAVINGS VS ORIGINAL:
#   Before: BGE-M3 loaded twice (retriever + ingest) = 4.6 GB
#   After:  BGE-base loaded once here              = 109 MB
#   Saving: ~4.5 GB
# =============================================================================

from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from sentence_transformers import CrossEncoder

EMBED_MODEL  = "BAAI/bge-base-en-v1.5"
EMBED_DIM    = 768
RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-12-v2"

print("[Models] Loading BGE-base embedding model...")
embed_model = HuggingFaceEmbedding(model_name=EMBED_MODEL, embed_batch_size=16)

print("[Models] Loading CrossEncoder reranker...")
cross_encoder = CrossEncoder(RERANK_MODEL)

print("[Models] Ready.")
