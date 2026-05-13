<div align="center">

# ResolveDesk

### Agentic AI Customer Support System for eCommerce

A full-stack, production-deployed AI support assistant that routes user queries through a LangGraph multi-agent system, retrieves grounded answers via a hybrid RAG pipeline, streams responses live to the UI, tracks operational analytics, and supports document uploads into the live knowledge base.

[![Python](https://img.shields.io/badge/Python-3.11+-blue?style=flat&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAF8?style=flat&logo=react)](https://react.dev)
[![LangGraph](https://img.shields.io/badge/LangGraph-Agent%20Orchestration-purple?style=flat)](https://langchain-ai.github.io/langgraph)
[![Pinecone](https://img.shields.io/badge/Pinecone-Vector%20Search-green?style=flat)](https://pinecone.io)
[![Groq](https://img.shields.io/badge/Groq-LLM-orange?style=flat)](https://groq.com)
[![Gemini](https://img.shields.io/badge/Gemini-Intent%20Routing-blue?style=flat)](https://deepmind.google/gemini)
[![GCP](https://img.shields.io/badge/GCP-Cloud%20Run-blue?style=flat&logo=googlecloud)](https://cloud.google.com/run)
[![Vercel](https://img.shields.io/badge/Vercel-Frontend-black?style=flat&logo=vercel)](https://vercel.com)
[![Redis](https://img.shields.io/badge/Redis-Semantic%20Cache-red?style=flat&logo=redis)](https://redis.io)

</div>

---

## Key Highlights

- Multi-agent LangGraph system with Gemini 2.5 Flash supervisor dynamically routing across 5 specialist agents
- Hybrid RAG pipeline: Pinecone dense search + BM25 sparse search + CrossEncoder reranking for maximum retrieval accuracy
- Redis-backed semantic cache (cosine similarity threshold 0.85) reduces redundant LLM calls by ~27%
- PostgreSQL-backed agent memory via LangGraph checkpointing for persistent multi-turn conversations
- Real-time analytics dashboard with session tracking, intent breakdown, confidence scoring, and feedback metrics
- Live document ingestion — upload PDFs/DOCX/PPTX through the UI and they become searchable immediately
- Full CI/CD: GitHub Actions → Docker multi-stage build → GCP Cloud Run + Vercel

---

## Architecture

### Full Request Flow

```
User Message (Frontend → Vercel proxy → GCP Cloud Run)
        │
        ▼
┌─────────────────────────────────────────────┐
│   Rate Limiter                              │
│   Redis INCR + EXPIRE (60s window)          │
│   Limit: 10 messages/minute per email       │
│   Exceeded → HTTP 429, no LLM call         │
└────────┬────────────────────────────────────┘
         │ allowed
         ▼
┌─────────────────────────────────────────────┐
│   Semantic Cache                            │
│   Embed query → BGE-base-en-v1.5           │
│   Cosine similarity vs. Redis cache         │
│                                             │
│   score ≥ 0.85 ──▶ return cached answer    │
│   score < 0.85 ──▶ continue to agents      │
│                                             │
│   Note: queries with ORD-XXXXX pattern      │
│   bypass cache entirely (order-specific)    │
└────────┬────────────────────────────────────┘
         │ cache miss
         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        LangGraph State (ResolveState)                   │
│                                                                         │
│  Persisted per session via AsyncPostgresSaver → Supabase PostgreSQL     │
│  thread_id = session_id (same UUID used for LangGraph + analytics)      │
│                                                                         │
│  Fields written/read by all agents:                                     │
│  ┌──────────────────┬──────────────────────────────────────────────┐   │
│  │ messages         │ full conversation history (HumanMessage,      │   │
│  │                  │ AIMessage) — appended, never overwritten      │   │
│  │ customer_email   │ email from login screen                       │   │
│  │ session_id       │ UUID for this chat session                    │   │
│  │ intent           │ set by Supervisor, read by graph router       │   │
│  │ agent_response   │ final text set by whichever agent ran         │   │
│  │ confidence_score │ LLM's self-reported confidence (0.0–1.0)      │   │
│  │ rag_best_score   │ top CrossEncoder score from retrieval         │   │
│  │ escalated        │ bool — triggers escalation_agent if True      │   │
│  │ escalation_reason│ weak_rag_match / low_confidence /             │   │
│  │                  │ supervisor_unclear                            │   │
│  │ retry_attempted  │ bool — was query rewritten and retried?       │   │
│  │ rewritten_query  │ the rewritten version (logged for analysis)   │   │
│  │ total_tokens     │ Groq token count this turn                    │   │
│  │ supervisor_tokens│ Gemini token count this turn                  │   │
│  └──────────────────┴──────────────────────────────────────────────┘   │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
               ┌────────────────────────────────┐
               │       Supervisor Agent         │
               │       Gemini 2.5 Flash         │
               │                                │
               │  Reads: messages               │
               │  Writes: intent                │
               │                                │
               │  Classifies into one of:       │
               │  faq / order / returns /       │
               │  chitchat / escalate           │
               └──┬──────┬───────┬──────┬───┬───┘
                  │      │       │      │   │
              faq │  order│returns│chit- │esc│
                  │      │       │ chat  │   │
                  ▼      ▼       ▼      ▼   ▼
```

### FAQ Agent Flow (most complex — includes RAG + retry + escalation)

```
FAQ Agent — Llama 3.3 70B (Groq)
        │
        ▼
  Retrieve chunks for user query
  via Hybrid RAG Pipeline (see below)
        │
        ├── best_score ≥ 0.60 ──────────────────────────────────┐
        │                                                        │
        └── best_score < 0.60 (weak retrieval)                  │
                │                                               │
                ▼                                               │
        Query Rewrite (Llama 3.3 70B)                          │
        Rephrase for better semantic search                      │
                │                                               │
                ▼                                               │
        Retry retrieval with rewritten query                     │
                │                                               │
                ├── retry_score ≥ 0.60 ──────────────────────▶ │
                │   use retry results                           │
                │                                               │
                └── retry_score < 0.60                         │
                    ESCALATE                                    │
                    reason: weak_rag_match                      │
                                                               │
                    ◄──────────────────────────────────────────┘
                                    │
                                    ▼
                        Build context from chunks
                        Ask Llama 3.3 70B to answer
                        LLM appends: "CONFIDENCE: 0.XX"
                                    │
                        Parse confidence score
                                    │
                        ├── score ≥ 0.75 ──▶ return answer ✓
                        │
                        └── score < 0.75
                            ESCALATE
                            reason: low_confidence
```

### Other Agents

```
Order Agent (Llama 3.3 70B)          Returns Agent (Llama 3.3 70B)
  Reads: customer_email, messages       Reads: messages (order ID extracted)
  Queries: Supabase orders table        Queries: Supabase return_eligibility table
  Writes: agent_response                Writes: agent_response

Chitchat Agent (Llama 3.1 8B)         Escalation Agent (Llama 3.3 70B)
  Reads: messages                        Reads: escalation_reason, messages
  No retrieval — LLM only               Returns: fixed human handoff response
  Writes: agent_response                 Writes: agent_response, escalated=True
```

### Escalation Triggers Summary

| Trigger | Condition | Reason logged |
|---|---|---|
| Supervisor routing | Intent is clearly out of scope | `supervisor_unclear` |
| FAQ: weak retrieval | RAG best score < **0.60** after retry | `weak_rag_match` |
| FAQ: low confidence | LLM confidence score < **0.75** | `low_confidence` |

### Hybrid RAG Pipeline

```
User Query (or rewritten query)
        │
        ├──────────────────────────────────────▶ Dense Search
        │                                         Embed with BGE-base-en-v1.5
        │                                         (384-dim, HuggingFace)
        │                                         Query Pinecone index
        │                                         Returns top-k with scores
        │
        └──────────────────────────────────────▶ Sparse Search
                                                  BM25 via LlamaIndex (bm25s)
                                                  Corpus loaded from Supabase
                                                  chunks table at startup
                                                  Returns top-k with BM25 scores
                                    │
                                    ▼
                          Merge + Deduplicate
                          (union of both result sets)
                                    │
                                    ▼
                          CrossEncoder Reranking
                          ms-marco-MiniLM-L-12-v2
                          Scores each (query, chunk) pair
                          with full cross-attention
                                    │
                                    ▼
                          Sort by CrossEncoder score
                          best_score → state.rag_best_score
                          Top chunks → LLM context window
```

---

## LLM Usage by Agent

| Agent | Model | Provider | Role |
|---|---|---|---|
| **Supervisor** | Gemini 2.5 Flash | Google | Intent classification, dynamic routing |
| **FAQ Agent** | Llama 3.3 70B | Groq | RAG-grounded product/policy Q&A |
| **Order Agent** | Llama 3.3 70B | Groq | Order lookup and status queries |
| **Returns Agent** | Llama 3.3 70B | Groq | Return eligibility checking |
| **Escalation Agent** | Llama 3.3 70B | Groq | Human handoff with context summary |
| **Chitchat Agent** | Llama 3.1 8B | Groq | Lightweight casual conversation |

> Groq is used for all specialist agents due to its ultra-low inference latency (~200ms). Gemini 2.5 Flash is used for the supervisor because of its superior instruction-following for structured JSON routing decisions.

---

## RAG Pipeline — Models & Components

| Stage | Component | Model / Tool |
|---|---|---|
| **Embedding** | Dense vector generation | `BAAI/bge-base-en-v1.5` (384-dim, HuggingFace) |
| **Vector Store** | Dense retrieval | Pinecone (serverless, cosine similarity) |
| **Sparse Retrieval** | Keyword-based search | BM25 via LlamaIndex (`bm25s`) |
| **BM25 Corpus** | Chunk storage for BM25 | Supabase PostgreSQL (`chunks` table) |
| **Reranker** | Cross-attention reranking | `cross-encoder/ms-marco-MiniLM-L-12-v2` |
| **Document Storage** | Raw file storage | Google Cloud Storage |

### Why Hybrid RAG?
- **Dense search** (Pinecone) excels at semantic similarity — finds conceptually related chunks even with different wording
- **Sparse search** (BM25) excels at exact keyword matches — critical for order IDs, product names, error codes
- **CrossEncoder reranking** re-scores the merged candidate list with full query-document attention for final precision

---

## Semantic Cache

```
Incoming query
      │
      ▼
Generate embedding (BGE-base-en-v1.5)
      │
      ▼
Compare against Redis cache (cosine similarity)
      │
   ≥ 0.85 ──────────────────▶ Return cached answer (0ms LLM cost)
      │
   < 0.85
      │
      ▼
Run full agent pipeline → store result in Redis
```

Queries containing order IDs (`ORD-XXXXX`) bypass the cache entirely since those responses are customer-specific.

---

## Agent Responsibilities

| Agent | Trigger | Data Source |
|---|---|---|
| **Supervisor** | Every message | — (routing only) |
| **FAQ Agent** | `intent = faq` | Hybrid RAG (Pinecone + BM25) |
| **Order Agent** | `intent = order` | Supabase `orders` table |
| **Returns Agent** | `intent = returns` | Supabase `return_eligibility` table |
| **Chitchat Agent** | `intent = chitchat` | LLM only (no retrieval) |
| **Escalation Agent** | `intent = escalate` or low confidence | Fixed handoff response |

---

## Tech Stack

**Frontend**
- React 19 + Vite — component-based chat UI, analytics dashboard, document upload
- Framer Motion — animated panel transitions and message entrance effects
- Tailwind CSS — utility-first styling
- Hosted on **Vercel**

**Backend**
- FastAPI + Uvicorn — REST + SSE streaming endpoints
- LangGraph — multi-agent orchestration graph with supervisor routing
- LangChain — LLM abstractions, prompt templates, text splitters
- LlamaIndex — BM25 retrieval and hybrid search utilities
- `sse-starlette` — Server-Sent Events for token-by-token streaming
- Hosted on **GCP Cloud Run** (scale-to-zero, 2 CPU / 2GiB RAM)

**AI / ML**
- Groq (Llama 3.3 70B + Llama 3.1 8B) — specialist agent inference
- Google Gemini 2.5 Flash — supervisor intent routing
- `sentence-transformers` + PyTorch (CPU) — embedding and reranking models
- LangSmith — tracing and observability

**Storage & Databases**
- Supabase (PostgreSQL) — sessions, messages, chunks, documents, LangGraph checkpoints
- Pinecone — vector embeddings for dense retrieval
- Google Cloud Storage — raw uploaded documents
- Redis (Upstash) — semantic cache + rate limiting

**DevOps**
- Docker (multi-stage build, ~851MB image)
- GitHub Actions — automated CI/CD on push to `main`
- GCP Artifact Registry — Docker image registry

---

## Project Structure

```
ResolveDesk/
│
├── backend/
│   ├── main.py                  FastAPI app, lifespan, all endpoints
│   ├── graph.py                 LangGraph graph definition
│   ├── state.py                 Shared agent state schema
│   ├── models.py                Pydantic request/response models
│   │
│   ├── agents/
│   │   ├── supervisor.py        Gemini 2.5 Flash — intent classification
│   │   ├── faq_agent.py         Llama 3.3 70B — RAG-based FAQ
│   │   ├── order_agent.py       Llama 3.3 70B — order lookup
│   │   ├── returns_agent.py     Llama 3.3 70B — return eligibility
│   │   ├── chitchat_agent.py    Llama 3.1 8B — casual conversation
│   │   └── escalation_agent.py  Llama 3.3 70B — human handoff
│   │
│   ├── rag/
│   │   ├── retriever.py         Hybrid RAG: Pinecone + BM25 + CrossEncoder
│   │   └── ingest.py            Document ingestion pipeline
│   │
│   ├── cache/
│   │   ├── semantic_cache.py    Redis semantic cache (BGE embeddings)
│   │   └── rate_limiter.py      Redis rate limiter (10 msg/min)
│   │
│   ├── db/
│   │   ├── checkpointer.py      LangGraph PostgreSQL checkpointer
│   │   ├── db.py                Supabase REST client for orders/customers
│   │   └── gcs.py               Google Cloud Storage client
│   │
│   ├── analytics/
│   │   └── tracker.py           Session + message logging to Supabase
│   │
│   ├── ingest/
│   │   └── router.py            FastAPI router for document upload endpoints
│   │
│   └── tools/
│       ├── order_tools.py        LangGraph tools for order queries
│       └── returns_tools.py      LangGraph tools for return queries
│
├── frontend/
│   └── src/
│       ├── pages/               ChatPage, AnalyticsPage
│       ├── components/          ChatWindow, LiveMetrics, AnalyticsDashboard
│       └── hooks/               useMetrics
│
├── Dockerfile                   Multi-stage build (builder + runtime)
├── requirements.txt
├── vercel.json                  Vercel proxy rewrites → Cloud Run
└── .github/workflows/deploy.yml GitHub Actions CI/CD
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SUPABASE_URL` | Yes | Supabase project URL |
| `SUPABASE_KEY` | Yes | Supabase service role key |
| `SUPABASE_DB_URL` | Yes | PostgreSQL Transaction pooler URL (port 6543) |
| `PINECONE_API_KEY` | Yes | Pinecone API key |
| `PINECONE_INDEX_NAME` | Yes | Pinecone index name |
| `GROQ_API_KEY` | Yes | Groq API key (Llama models) |
| `GOOGLE_API_KEY` | Yes | Gemini API key (supervisor) |
| `REDIS_HOST` | Yes | Upstash Redis hostname only (no `rediss://` prefix) |
| `REDIS_PASSWORD` | Yes | Upstash Redis password |
| `REDIS_PORT` | Yes | `6379` |
| `REDIS_SSL` | Yes | `true` for production, `false` for local |
| `GCS_BUCKET_NAME` | Yes | GCS bucket for document storage |
| `LANGCHAIN_API_KEY` | Optional | LangSmith tracing key |
| `LANGCHAIN_PROJECT` | Optional | LangSmith project name |
| `LANGCHAIN_TRACING_V2` | Optional | `true` to enable tracing |

---

## Local Setup

### 1. Clone and create virtual environment

```bash
git clone https://github.com/ritwik-basak/ResolveDesk.git
cd ResolveDesk
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create `.env` in project root

```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_service_role_key
SUPABASE_DB_URL=postgresql://postgres.PROJECT_REF:PASSWORD@HOST:6543/postgres

PINECONE_API_KEY=your_pinecone_key
PINECONE_INDEX_NAME=resolvedesk-knowledge

GROQ_API_KEY=your_groq_key
GOOGLE_API_KEY=your_gemini_key

REDIS_HOST=your_upstash_hostname
REDIS_PASSWORD=your_upstash_password
REDIS_PORT=6379
REDIS_SSL=false

GCS_BUCKET_NAME=your_bucket_name

LANGCHAIN_API_KEY=your_langsmith_key
LANGCHAIN_PROJECT=resolvedesk
LANGCHAIN_TRACING_V2=true
```

### 4. Run backend

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Run frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check — returns `{"status": "ok"}` |
| `POST` | `/chat` | Run agent pipeline, stream SSE response |
| `POST` | `/feedback` | Record thumbs up / thumbs down on a message |
| `POST` | `/session/end` | Finalize session analytics |
| `GET` | `/metrics/live` | Live metrics polled every 5s by the UI |
| `GET` | `/analytics/summary` | Aggregate stats for analytics dashboard |
| `GET` | `/analytics/sessions` | Paginated session list with filters |
| `GET` | `/analytics/session/{id}` | Full transcript for one session |
| `GET` | `/analytics/trend` | Daily message/token/cost trend data |
| `GET` | `/ingest/documents` | List all uploaded documents |
| `POST` | `/ingest/upload` | Upload document → GCS → Pinecone + Supabase |
| `DELETE` | `/ingest/delete/{filename}` | Remove document from GCS + vector store |

---

## Deployment

**Backend → GCP Cloud Run**
- Every push to `main` that touches `backend/**`, `requirements.txt`, or `Dockerfile` triggers a GitHub Actions build
- Docker image is pushed to GCP Artifact Registry
- Cloud Run deploys the new revision (scale-to-zero, max 3 instances)
- Cloud Scheduler pings `/health` every 10 minutes to keep the instance warm

**Frontend → Vercel**
- Auto-deploys on every push to `main`
- `vercel.json` proxies all API paths (`/chat`, `/metrics`, `/analytics`, etc.) to Cloud Run

---

## Notes

- Never commit `.env` files or GCP service account JSON to GitHub
- `SUPABASE_DB_URL` must use the **Transaction pooler** (port 6543), not the direct connection (IPv6 only, incompatible with Cloud Run)
- `REDIS_HOST` must be the hostname only — not the full `rediss://` connection URL
- The BM25 index is rebuilt from Supabase on every cold start — no local state needed
