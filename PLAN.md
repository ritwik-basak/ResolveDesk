# ResolveDesk — Full Build Plan

ResolveDesk is an Agentic AI-powered Customer Support System for CartFlow (Indian eCommerce).
Rule: one step at a time. Wait for "next" before proceeding.

---

## STATUS

| Step | What | Status |
|------|------|--------|
| 1 | Project scaffold, folder structure, requirements.txt, .env | DONE |
| 2 | Supabase database setup — db.py, seed_db.py, mock_db.py redirect | DONE |
| 3 | Knowledge base — 8 markdown documents in backend/rag/knowledge_base/ | DONE |
| 4 | RAG Ingest Pipeline — backend/rag/ingest.py | DONE |
| 5 | Hybrid RAG Retriever — backend/rag/retriever.py | DONE |
| 6 | Tools — backend/tools/order_tools.py and returns_tools.py | DONE |
| 7 | Analytics Tracker — backend/analytics/tracker.py | DONE |
| 8 | Individual Agents — all 6 agents in backend/agents/ | DONE |
| 9 | Checkpointer — backend/db/checkpointer.py | DONE |
| 10 | LangGraph Graph — backend/graph.py | DONE |
| 11 | Redis Cache and Rate Limiter — backend/cache/ | DONE |
| 12 | FastAPI Backend — backend/main.py | DONE |
| 12.5 | Document Management — upload/delete pipeline + LlamaIndex RAG rewrite | DONE |
| 12.6 | Query Rewriting — FAQ agent retries with rewritten query before escalating | DONE |
| 13 | LangSmith Tracing | DONE |
| 14 | Frontend — chat page + analytics page + admin document panel | pending |
| 15 | Deployment on GCP (Cloud Run + Cloud Storage) | pending |
| 16 | README with architecture diagram | pending |

---

## Step 5 — Hybrid RAG Retriever

**File:** `backend/rag/retriever.py`

Build a 3-step hybrid retriever:
1. **Dense search** — embed the query with BGE-M3, search Pinecone for semantically similar vectors. Pinecone metadata available per vector: `source`, `text`, `chunk_index`, `category` (policy / faq / support). The retriever should accept an optional `category` filter so agents can narrow the Pinecone search to a specific category if needed.
2. **Sparse search** — BM25 keyword search over chunks.json (already saved by ingest.py). chunks.json also contains `chunk_index` and `category` per chunk.
3. **Reranking** — merge + deduplicate results from steps 1 & 2, feed all candidates to CrossEncoder (ms-marco-MiniLM-L-12-v2), return top 3 chunks + best similarity score. Each returned chunk should include `text`, `source`, `category`, and `chunk_index`.

**After building, explain:** what dense search is, what sparse search is, why we combine them, what reranking does, and why CrossEncoder is better than vector similarity alone.

---

## Step 6 — Tools

**Files:** `backend/tools/order_tools.py` and `backend/tools/returns_tools.py`

Build LangChain tools that agents can call. These tools query **`db.py`** (Supabase) — NOT mock_db.py.
mock_db.py is just a redirect wrapper to db.py; always import from db.py.

- `order_tools.py` — `get_order_status(order_id)`: looks up order from `db.get_order_by_id()`, returns status, estimated delivery, tracking number, carrier, items, shipping address
- `returns_tools.py` — `get_return_eligibility(order_id)`: looks up eligibility from `db.get_return_eligibility()`, returns eligible flag, reason, return window, refund method, timeline

Add proper tool descriptions in plain English so the LLM knows when to call each tool.

**After building, explain:** what tool calling is, how the LLM decides to call a tool, what the tool description does, and what this would look like in production with a real API.

---

## Step 7 — Analytics Tracker

**File:** `backend/analytics/tracker.py`

Create two Supabase tables if they do not exist: `sessions` and `messages`.

Provide functions to:
- Log session start
- Log each message with all metadata
- Update session on end
- Update feedback on a message

Track all fields in the Analytics Requirements. Must be importable by main.py and agents.

**After building, explain:** why we track analytics separately from checkpointing, the difference between the sessions table and messages table, and how this feeds both live metrics and the full analytics dashboard.

---

## Step 8 — Individual Agents

**Files:** all 6 agents in `backend/agents/`

Build one by one:

| Agent | Model | What it does |
|-------|-------|--------------|
| `supervisor.py` | Gemini 2.5 Flash | Classifies every message into one of 5 routes: chitchat, faq, order, returns, escalation |
| `chitchat_agent.py` | Groq Llama 3.3 70B | Handles greetings and small talk. No RAG, no tools, no confidence score |
| `faq_agent.py` | Groq Llama 3.3 70B | Calls retriever, gets chunks + best score, generates answer, outputs confidence score, checks both thresholds |
| `order_agent.py` | Groq Llama 3.3 70B | Calls order tool, outputs confidence score, checks confidence threshold |
| `returns_agent.py` | Groq Llama 3.3 70B | Calls returns tool, outputs confidence score, checks confidence threshold |
| `escalation_agent.py` | Groq Llama 3.3 70B | Generates human handoff message, logs escalation reason |

Two-trigger escalation logic for FAQ agent: escalate if (1) retriever best score is below retrieval threshold OR (2) agent confidence score is below confidence threshold.

**After building, explain:** how each agent is different, what system prompts do, how confidence scores are parsed from LLM output, and the two-trigger escalation logic.

---

## Step 9 — Checkpointer

**File:** `backend/db/checkpointer.py`

Connect to Supabase PostgreSQL using `AsyncPostgresSaver` from LangGraph.

Note: This is separate from db.py. db.py handles order/customer data. The checkpointer handles LangGraph conversation history (what was said in this thread).

**After building, explain:** what checkpointing is, what AsyncPostgresSaver does under the hood, why Supabase and not SQLite, and what thread_id means.

---

## Step 10 — LangGraph Graph

**File:** `backend/graph.py`

Wire all 6 agents into a LangGraph `StateGraph`:
- Define state schema including `escalation_reason` field
- Add all agent nodes
- Add supervisor routing edges for all 5 routes including chitchat
- Add conditional edges based on supervisor output and agent confidence results
- Connect checkpointer
- Compile the graph

**After building, explain:** what a StateGraph is, what nodes and edges mean, what conditional edges are, and how the graph handles the two different escalation paths.

---

## Step 11 — Redis Cache and Rate Limiter

**Files:** `backend/cache/semantic_cache.py` and `backend/cache/rate_limiter.py`

- `semantic_cache.py` — BGE embedding + cosine similarity against stored Redis embeddings. Return cached answer if similarity > 0.85. Store new answers with 24-hour TTL. **Do NOT cache escalation responses.**
- `rate_limiter.py` — Redis counter per user per minute with TTL

Only cache successful answers from chitchat, faq, order, and returns agents.

**After building, explain:** what cosine similarity is, what TTL means, why we do not cache escalation responses, and what rate limiting prevents.

---

## Step 12 — FastAPI Backend

**File:** `backend/main.py`

Endpoints:
- `POST /chat` — rate limit check → semantic cache check → run LangGraph graph → stream response via SSE → log to analytics → store in cache if not escalated
- `POST /feedback` — accept message_id and feedback value, update Supabase messages table
- `GET /metrics/live` — current live metrics for the panel
- `GET /analytics/summary` — full analytics summary
- `GET /analytics/sessions` — paginated sessions list with filters
- `GET /analytics/session/{session_id}` — full transcript and metadata for one session
- `GET /health` — health check

**After building, explain:** what SSE streaming is, the full request/response flow end to end, and how the feedback endpoint works.

---

## Step 12.5 — Document Management + LlamaIndex RAG Rewrite

**Files:**
- `backend/rag/ingest.py` — rewritten using LlamaIndex ingestion pipeline
- `backend/rag/retriever.py` — rewritten using LlamaIndex query engine
- `backend/ingest/router.py` — new FastAPI router for document management endpoints
- `backend/db/gcs.py` — Google Cloud Storage helper (upload, delete, list files)

**LlamaIndex replaces both ingest.py and retriever.py:**
- Same models kept: BGE-M3 (HuggingFaceEmbedding), CrossEncoder reranker (SentenceTransformerRerank), Pinecone vector store
- LlamaIndex orchestrates the pipeline instead of hand-written Python
- BM25 sparse search configured inside LlamaIndex alongside dense search

**Supported file types:** PDF, DOCX, TXT, MD, PPTX, CSV
- CSV chunking strategy: one row per chunk, column headers prepended for context
  e.g. `"product_name: Headphones | price: 2999 | return_eligible: yes"`

**File storage:** Google Cloud Storage (GCS)
- Raw uploaded files stored in GCS bucket
- File metadata (filename, upload date, chunk count, GCS path) stored in Supabase `documents` table

**Chunk storage:** Supabase `chunks` table
- Columns: chunk_id, text, source, category, chunk_index
- Used to rebuild BM25 index on startup
- Enables clean per-document delete (DELETE WHERE source = filename)

**New endpoints (added to main.py):**
- `POST /ingest/upload` — receive file → store in GCS → LlamaIndex pipeline → save chunks to Supabase
- `DELETE /ingest/delete/{filename}` — delete from Pinecone (by source filter) + Supabase chunks + GCS
- `GET /ingest/documents` — list all documents with metadata from Supabase documents table

**After building, explain:** what LlamaIndex replaced and why, how GCS and Supabase chunks table serve different purposes, and how the delete pipeline works across three systems.

---

## Step 13 — LangSmith Tracing

Add LangSmith tracing via environment variables. Verify agent calls appear in LangSmith dashboard.

**After building, explain:** what LangSmith shows, why it is different from our own analytics tracker, and what you would use each one for.

---

## Step 14 — Frontend

**Before writing any code:** stop and ask for sample frontend designs (screenshots). Do not proceed until user sends samples and approves the direction.

Once approved, build:

**Chat Page:**
- Email input screen first
- Chat interface after email entered
- Right panel: Live Metrics Panel polling `GET /metrics/live` every 5 seconds
- Live metrics: total sessions today, messages today, active sessions, avg confidence, cache hit rate, escalation rate, avg response time, intent breakdown bars, feedback summary with circular progress, current session stats
- Every agent reply bubble (except escalation) has thumbs up / thumbs down buttons
- Clicking feedback sends `POST /feedback` and updates button state

**Analytics Page (separate tab):**
- Summary cards
- All charts using Recharts
- Sessions table with filters and search
- Transcript modal: full conversation, per-message metadata, session summary

**Admin Panel (tab inside analytics page):**
- Document list table: filename, upload date, chunk count, delete button
- Upload button with drag-and-drop, shows supported formats (PDF, DOCX, TXT, MD, PPTX, CSV)
- Delete triggers `DELETE /ingest/delete/{filename}`
- Upload triggers `POST /ingest/upload`

**After building, explain:** how SSE works on the browser side, how polling works, how feedback buttons update without page refresh.

---

## Step 15 — Deployment on GCP

Deploy the full application to Google Cloud Platform:
- **Backend:** Cloud Run (containerised FastAPI app)
- **File storage:** Google Cloud Storage bucket for uploaded documents
- **Redis:** Upstash Redis (see notes below — do NOT use local Redis or GCP Memorystore)
- **Environment variables:** set in Cloud Run service configuration

Add deployment instructions to README.

### ⚠️ Redis on Cloud Run — use Upstash

Cloud Run containers are **stateless and ephemeral** — Redis cannot run inside the container.
Use **Upstash Redis** (https://upstash.com) — serverless Redis, free tier available, connects over HTTPS.

Steps:
1. Create a free Upstash Redis database at upstash.com
2. Copy the connection details and set these env vars in Cloud Run:
   ```
   REDIS_HOST=your-endpoint.upstash.io
   REDIS_PORT=6379
   REDIS_PASSWORD=your-upstash-token
   ```
3. The existing `semantic_cache.py` connects via these env vars — no code change needed

This way the 30-day semantic cache (FAQ + chitchat only) survives every redeployment.
Rebuilding the app container never touches Redis.

### ⚠️ Cold starts — set minimum instances to 1

Cloud Run scales to zero when idle. A cold start reloads the BGE embedding model
(~10-15 seconds). To avoid this, set `--min-instances=1` in Cloud Run config.
Small cost (~$5-10/month) but eliminates cold start delay for all users.

---

## Step 16 — README

Comprehensive README with:
- Mermaid architecture diagram
- Agent routing explanation
- RAG pipeline explanation (LlamaIndex)
- Tech stack table
- Setup instructions (local + GCP)
- Environment variables list
- Example conversations

---

## Key Technical Notes (for future reference)

- **Embedding model:** BGE-M3 (BAAI/bge-m3), 1024-dimensional vectors, cached at `C:\Users\britw\AppData\Local\llama_index\` (LlamaIndex cache, different from old SentenceTransformer cache)
- **Pinecone index:** `resolvedesk-knowledge`, dimension=1024, metric=cosine, region=us-east-1 (free tier). Switch to ap-south-1 (Mumbai) on paid plan for production.
- **Pinecone metadata per vector:** LlamaIndex node format (includes `_node_content`, `_node_type` + custom fields: source, category, chunk_index)
- **chunks.json:** deprecated — replaced by Supabase chunks table in Step 12.5. File still exists on disk but is no longer used.
- **Supabase tables (document management):** documents, chunks — created in Step 12.5. GRANT permissions run manually in SQL Editor.
- **GCS bucket:** stores raw uploaded files (PDF, DOCX, TXT, MD, PPTX, CSV). Set GCS_BUCKET_NAME in .env. Use GOOGLE_APPLICATION_CREDENTIALS locally.
- **LlamaIndex:** replaces hand-written ingest.py and retriever.py in Step 12.5. Models stay the same — BGE-M3, CrossEncoder, Pinecone. SentenceTransformerRerank from LlamaIndex was incompatible with sentence-transformers 3.3.1 — CrossEncoder used directly instead.
- **Query rewriting (Step 12.6):** faq_agent.py retries retrieval once with a rewritten query before escalating on weak_rag_match. Tracks retry_attempted (bool) and rewritten_query (text) in messages table. Only applies to FAQ agent — other escalation paths (supervisor unclear, LLM confidence low, order/returns tool failure) don't benefit from rewriting.
- **Supabase messages table:** added retry_attempted (BOOLEAN) and rewritten_query (TEXT) columns in Step 12.6. ALTER TABLE IF NOT EXISTS runs at startup — safe to run on existing tables.
- **db.py vs mock_db.py:** Always use db.py. mock_db.py is a redirect-only wrapper kept for accidental imports.
- **Supabase tables (order data):** customers, orders, return_eligibility — seeded with 5 customers, 5 orders
- **Supabase tables (analytics):** sessions, messages — created in Step 7
- **Supabase tables (checkpointing):** created by AsyncPostgresSaver in Step 9
