# syntax=docker/dockerfile:1

# =============================================================================
# Stage 1 — Builder
# Install all Python packages (including build tools for C extensions).
# Build tools are NOT carried into the final image, keeping it lean.
# =============================================================================
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc g++ \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install PyTorch CPU-only first — prevents pip from pulling the 2GB+ CUDA build.
# The +cpu local version tag requires the PyTorch index.
RUN pip install --no-cache-dir \
    torch==2.11.0+cpu \
    --extra-index-url https://download.pytorch.org/whl/cpu

# Install everything else. Torch is already satisfied above so pip skips it.
RUN pip install --no-cache-dir -r requirements.txt \
    --extra-index-url https://download.pytorch.org/whl/cpu

# pinecone>=7.0 crashes if pinecone-plugin-inference is installed (transitively
# pulled in by older deps). Remove it explicitly after all installs.
RUN pip uninstall -y pinecone-plugin-inference 2>/dev/null || true


# =============================================================================
# Stage 2 — Runtime
# Copy only compiled packages (no build tools).
# Pre-download HuggingFace models so cold starts don't re-download ~190MB.
# =============================================================================
FROM python:3.11-slim AS runtime

WORKDIR /app

# libgomp1 is required at runtime by PyTorch and scikit-learn (OpenMP).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder (no build tools included).
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Tell HuggingFace libraries where to cache models inside the image.
# This ENV persists into the running container so models are found at runtime.
ENV HF_HOME=/app/.cache/huggingface

# Pre-download both models during the image build.
# Cold starts load from this cache — no internet call needed at runtime.
RUN python3 -c "\
from llama_index.embeddings.huggingface import HuggingFaceEmbedding; \
from sentence_transformers import CrossEncoder; \
print('Downloading BAAI/bge-base-en-v1.5...'); \
HuggingFaceEmbedding(model_name='BAAI/bge-base-en-v1.5', embed_batch_size=16); \
print('Downloading cross-encoder/ms-marco-MiniLM-L-12-v2...'); \
CrossEncoder('cross-encoder/ms-marco-MiniLM-L-12-v2'); \
print('Models cached.')"

# Copy application source last — changes here don't invalidate model cache layer.
COPY backend/ ./backend/

EXPOSE 8080

# Cloud Run injects PORT at runtime (default 8080).
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
