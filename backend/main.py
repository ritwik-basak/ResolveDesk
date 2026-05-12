import asyncio
import json

import time
import uuid
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from backend.analytics.tracker import (
    create_tables,
    get_live_metrics,
    log_message,
    log_session_start,
    supabase as _db,
    update_feedback,
    update_session_end,
)
from backend.cache.rate_limiter import is_allowed
from backend.cache.semantic_cache import get_cached_answer, store_answer
from backend.db.checkpointer import get_checkpointer
from backend.graph import build_graph
from backend.ingest.router import router as ingest_router
from backend.rag.ingest import create_document_tables

load_dotenv()


# =============================================================================
# STARTUP / SHUTDOWN
# The lifespan context manager runs before the first request (setup) and after
# the last request (teardown). Using `async with get_checkpointer()` keeps the
# Postgres connection pool open for the entire life of the app.
# =============================================================================

graph = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global graph
    create_tables()                                   # analytics tables — safe every time
    create_document_tables()                          # documents + chunks tables
    async with get_checkpointer() as checkpointer:
        graph = build_graph(checkpointer)             # compiled once, reused for all requests
        yield                                         # app serves requests here
    # pool closes automatically when async with exits


app = FastAPI(title="ResolveDesk API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingest_router)


# =============================================================================
# REQUEST MODELS
# Pydantic models validate and parse the JSON body of incoming requests.
# FastAPI returns a clear 422 error automatically if required fields are missing.
# =============================================================================

class ChatRequest(BaseModel):
    session_id:     str
    customer_email: str
    message:        str


class FeedbackRequest(BaseModel):
    message_id: str
    feedback:   int    # 1 = thumbs up, -1 = thumbs down


class SessionEndRequest(BaseModel):
    session_id: str


# =============================================================================
# HELPERS
# =============================================================================

def _ensure_session(session_id: str, customer_email: str) -> None:
    """
    Insert a session row if it doesn't exist yet.
    Silent on duplicate key — subsequent messages in the same session will
    hit the unique constraint, which we intentionally ignore.
    """
    try:
        log_session_start(session_id, customer_email)
    except Exception:
        pass


def _sse(data: dict) -> str:
    """Format a dict as a single SSE data line."""
    return f"data: {json.dumps(data)}\n\n"


# =============================================================================
# POST /chat
# The core endpoint. Runs the full pipeline for every user message.
#
# FLOW:
#   1. Rate limit check     — block if user exceeded 10 msg/min
#   2. Semantic cache check — return cached answer instantly if similarity ≥ 0.85
#   3. LangGraph invoke     — run all agents (supervisor → specialist → optional escalation)
#   4. Log to analytics     — write message row to Supabase
#   5. Store in cache       — save answer for future similar queries (skip if escalated)
#   6. Stream via SSE       — send response word-by-word to the frontend
# =============================================================================

@app.post("/chat")
async def chat(req: ChatRequest):

    # ── 1. Rate limit ──────────────────────────────────────────────────────
    allowed, _ = is_allowed(req.customer_email)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many messages. Please wait a moment before sending again.",
        )

    # ── 2. Semantic cache check ────────────────────────────────────────────
    # Skip cache entirely if the query mentions a specific order ID — those
    # responses are customer+order specific and must never be served to others.
    import re as _re
    _has_order_id = bool(_re.search(r'\bORD-\d+\b', req.message, _re.IGNORECASE))
    cached = None if _has_order_id else get_cached_answer(req.message)
    if cached:
        message_id = str(uuid.uuid4())
        answer     = cached["answer"]

        _ensure_session(req.session_id, req.customer_email)
        try:
            log_message(
                message_id=message_id,     session_id=req.session_id,
                user_message=req.message,  agent_response=answer,
                agent_type="cache",        intent="cache",
                confidence_score=None,     rag_best_score=None,
                rag_chunks_retrieved=0,    cache_hit=True,
                response_time_ms=0,        escalated=False,
                escalation_reason=None,
            )
        except Exception:
            pass

        async def _stream_cached():
            for word in answer.split():
                yield _sse({"type": "token", "content": word + " "})
                await asyncio.sleep(0.02)
            yield _sse({
                "type": "done", "message_id": message_id,
                "agent_type": "cache", "escalated": False, "cache_hit": True,
            })

        return StreamingResponse(_stream_cached(), media_type="text/event-stream")

    # ── 3. Run LangGraph ───────────────────────────────────────────────────
    start_ms = time.time()

    try:
        result = await graph.ainvoke(
            {
                "messages":             [HumanMessage(content=req.message)],
                "customer_email":       req.customer_email,
                "session_id":           req.session_id,
                "intent":               None,
                "agent_response":       None,
                "confidence_score":     None,
                "rag_best_score":       None,
                "rag_chunks_retrieved": 0,
                "escalated":            False,
                "escalation_reason":    None,
                "retry_attempted":      False,
                "rewritten_query":      None,
                "total_tokens":         0,
                "chitchat_tokens":      0,
                "supervisor_tokens":    0,
                "cache_hit":            False,
                "response_time_ms":     None,
            },
            config={"configurable": {"thread_id": req.session_id}},
        )
    except Exception as _exc:
        _msg = str(_exc).lower()
        if "quota" in _msg or "resourceexhausted" in _msg or "429" in _msg:
            async def _quota_err():
                yield _sse({
                    "type": "error",
                    "code": "quota_exceeded",
                    "message": "Gemini 2.5 Flash API quota exceeded (free tier limit: 20 req/day). Please swap in a new API key or wait a few minutes.",
                })
            return StreamingResponse(_quota_err(), media_type="text/event-stream")
        raise

    response_time_ms = int((time.time() - start_ms) * 1000)

    agent_response       = result.get("agent_response") or "Sorry, I couldn't process your request."
    intent               = result.get("intent") or "unknown"
    escalated            = result.get("escalated", False)
    escalation_reason    = result.get("escalation_reason")
    confidence_score     = result.get("confidence_score")
    rag_best_score       = result.get("rag_best_score")
    rag_chunks_retrieved = result.get("rag_chunks_retrieved", 0)
    retry_attempted      = result.get("retry_attempted", False)
    rewritten_query      = result.get("rewritten_query")
    total_tokens         = result.get("total_tokens", 0) or 0       # Groq Llama 3.3 70B (faq/order/returns/escalation)
    chitchat_tokens      = result.get("chitchat_tokens", 0) or 0    # Groq Llama 3.1 8B (chitchat)
    supervisor_tokens    = result.get("supervisor_tokens", 0) or 0  # Gemini 2.5 Flash (supervisor)
    # Pricing: Llama 3.3 70B ~$0.70/1M | Llama 3.1 8B ~$0.06/1M | Gemini 2.5 Flash input $0.15/1M
    est_cost_usd         = round(
        total_tokens      * 0.0000007  +
        chitchat_tokens   * 0.00000006 +
        supervisor_tokens * 0.00000015,
        6
    )
    agent_type           = "escalation" if escalated else intent
    message_id           = str(uuid.uuid4())

    # ── 4. Log to analytics ────────────────────────────────────────────────
    _ensure_session(req.session_id, req.customer_email)
    try:
        log_message(
            message_id=message_id,             session_id=req.session_id,
            user_message=req.message,          agent_response=agent_response,
            agent_type=agent_type,             intent=intent,
            confidence_score=confidence_score, rag_best_score=rag_best_score,
            rag_chunks_retrieved=rag_chunks_retrieved,
            cache_hit=False,                   response_time_ms=response_time_ms,
            escalated=escalated,               escalation_reason=escalation_reason,
            retry_attempted=retry_attempted,   rewritten_query=rewritten_query,
            total_tokens=total_tokens,         est_cost_usd=est_cost_usd,
        )
    except Exception:
        pass

    # ── 5. Store in cache (FAQ + chitchat only) ───────────────────────────
    # order/returns responses are specific to the customer's order — caching
    # them would serve wrong answers to other users asking similar questions.
    _CACHEABLE = {'faq', 'chitchat'}
    if not escalated and intent in _CACHEABLE:
        try:
            store_answer(req.message, agent_response)
        except Exception:
            pass

    # ── 6. Stream response via SSE ─────────────────────────────────────────
    async def _stream_response():
        for word in agent_response.split():
            yield _sse({"type": "token", "content": word + " "})
            await asyncio.sleep(0.02)
        yield _sse({
            "type":       "done",
            "message_id": message_id,
            "agent_type": agent_type,
            "escalated":  escalated,
            "cache_hit":  False,
        })

    return StreamingResponse(_stream_response(), media_type="text/event-stream")


# =============================================================================
# POST /feedback
# Records a thumbs up (1) or thumbs down (-1) on a specific message.
# Updates both the message row and the session's feedback counters.
# =============================================================================

@app.post("/feedback")
async def feedback(req: FeedbackRequest):
    if req.feedback not in (1, -1):
        raise HTTPException(status_code=400, detail="feedback must be 1 or -1")
    try:
        update_feedback(req.message_id, req.feedback)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "ok"}


# =============================================================================
# POST /session/end
# Called by the frontend when the user closes the chat window.
# Computes aggregate stats for the session and writes the final summary row.
# =============================================================================

@app.post("/session/end")
async def session_end(req: SessionEndRequest):
    try:
        update_session_end(req.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "ok"}


# =============================================================================
# GET /metrics/live
# Polled every 5 seconds by the frontend's Live Metrics Panel.
# Returns all stats computed from today's sessions and messages only.
# =============================================================================

@app.get("/metrics/live")
async def metrics_live():
    try:
        return get_live_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# GET /analytics/summary
# All-time aggregate stats for the Analytics Dashboard summary cards.
# =============================================================================

@app.get("/analytics/summary")
async def analytics_summary(days: int = Query(0, ge=0)):
    from datetime import datetime, timedelta, timezone as _tz
    q_sessions = _db.table("sessions").select("*")
    q_msgs     = _db.table("messages").select("*")
    if days > 0:
        cutoff = (datetime.now(_tz.utc) - timedelta(days=days)).isoformat()
        q_sessions = q_sessions.gte("started_at", cutoff)
        q_msgs     = q_msgs.gte("timestamp", cutoff)
    sessions = q_sessions.execute().data or []
    msgs     = q_msgs.execute().data or []

    total_sessions  = len(sessions)
    total_messages  = len(msgs)

    escalated_count = sum(1 for m in msgs if m.get("escalated"))
    escalation_rate = round(escalated_count / total_messages, 4) if total_messages else 0.0

    conf_values    = [m["confidence_score"] for m in msgs if m.get("confidence_score") is not None]
    avg_confidence = round(sum(conf_values) / len(conf_values), 4) if conf_values else 0.0

    cache_hits     = sum(1 for m in msgs if m.get("cache_hit"))
    cache_hit_rate = round(cache_hits / total_messages, 4) if total_messages else 0.0

    rt_values            = [m["response_time_ms"] for m in msgs if m.get("response_time_ms") is not None]
    avg_response_time_ms = round(sum(rt_values) / len(rt_values)) if rt_values else 0

    intent_counts: dict[str, int] = {}
    for m in msgs:
        k = m.get("intent") or "unknown"
        intent_counts[k] = intent_counts.get(k, 0) + 1

    retry_count   = sum(1 for m in msgs if m.get("retry_attempted"))
    retry_rate    = round(retry_count / total_messages, 4) if total_messages else 0.0

    rag_scores    = [m["rag_best_score"] for m in msgs if m.get("rag_best_score") is not None]
    avg_rag_score = round(sum(rag_scores) / len(rag_scores), 4) if rag_scores else 0.0

    return {
        "total_sessions":       total_sessions,
        "total_messages":       total_messages,
        "escalation_rate":      escalation_rate,
        "avg_confidence":       avg_confidence,
        "cache_hit_rate":       cache_hit_rate,
        "avg_response_time_ms": avg_response_time_ms,
        "intent_breakdown":     intent_counts,
        "feedback_positive":    sum(1 for m in msgs if m.get("feedback") == 1),
        "feedback_negative":    sum(1 for m in msgs if m.get("feedback") == -1),
        "total_tokens":         sum(m.get("total_tokens") or 0 for m in msgs),
        "est_cost_usd":         round(sum(m.get("est_cost_usd") or 0 for m in msgs), 4),
        "retry_rate":           retry_rate,
        "avg_rag_score":        avg_rag_score,
    }


# =============================================================================
# GET /analytics/trend
# Daily aggregates for the trend chart: message volume, avg confidence, tokens, cost.
# =============================================================================

@app.get("/analytics/trend")
async def analytics_trend(days: int = Query(30, ge=1, le=90)):
    from datetime import datetime, timedelta, timezone
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    msgs = (
        _db.table("messages")
        .select("timestamp,confidence_score,response_time_ms,total_tokens,est_cost_usd,escalated")
        .gte("timestamp", cutoff)
        .execute()
    ).data or []

    by_date: dict = {}
    for m in msgs:
        if not m.get("timestamp"):
            continue
        date = m["timestamp"][:10]
        d = by_date.setdefault(date, {
            "messages": 0, "conf_sum": 0.0, "conf_count": 0,
            "rt_sum": 0, "rt_count": 0, "tokens": 0, "cost": 0.0, "escalated": 0,
        })
        d["messages"] += 1
        if m.get("confidence_score") is not None:
            d["conf_sum"]   += m["confidence_score"]
            d["conf_count"] += 1
        if m.get("response_time_ms") is not None:
            d["rt_sum"]   += m["response_time_ms"]
            d["rt_count"] += 1
        d["tokens"]    += m.get("total_tokens") or 0
        d["cost"]      += m.get("est_cost_usd") or 0.0
        d["escalated"] += 1 if m.get("escalated") else 0

    return [
        {
            "date":            date,
            "messages":        d["messages"],
            "avg_confidence":  round(d["conf_sum"] / d["conf_count"], 3) if d["conf_count"] else None,
            "avg_response_ms": round(d["rt_sum"] / d["rt_count"]) if d["rt_count"] else None,
            "tokens":          d["tokens"],
            "cost":            round(d["cost"], 4),
            "escalated":       d["escalated"],
        }
        for date, d in sorted(by_date.items())
    ]


# =============================================================================
# GET /analytics/sessions
# Paginated session list with optional filters for the Analytics Dashboard.
#
# Query params:
#   page, page_size   — pagination
#   email             — partial match on customer_email
#   escalated         — true / false filter
#   date_from, date_to — ISO datetime strings e.g. "2025-01-01T00:00:00+00:00"
# =============================================================================

@app.get("/analytics/sessions")
async def analytics_sessions(
    page:      int        = Query(1,    ge=1),
    page_size: int        = Query(20,   ge=1, le=100),
    email:     str | None = Query(None),
    escalated: bool | None = Query(None),
    date_from: str | None = Query(None),
    date_to:   str | None = Query(None),
):
    query = _db.table("sessions").select("*").order("started_at", desc=True)

    if email:
        query = query.ilike("customer_email", f"%{email}%")
    if escalated is not None:
        query = query.eq("escalated", escalated)
    if date_from:
        query = query.gte("started_at", date_from)
    if date_to:
        query = query.lte("started_at", date_to)

    offset = (page - 1) * page_size
    result = query.range(offset, offset + page_size - 1).execute()

    sessions = result.data or []

    # Enrich each session with live message stats (bypasses stale session-level fields)
    if sessions:
        sids     = [s["session_id"] for s in sessions]
        all_msgs = (_db.table("messages").select(
            "session_id,confidence_score,escalated,total_tokens,est_cost_usd"
        ).in_("session_id", sids).execute()).data or []

        by_sid: dict = {}
        for m in all_msgs:
            by_sid.setdefault(m["session_id"], []).append(m)

        for s in sessions:
            msgs = by_sid.get(s["session_id"], [])
            conf_vals = [m["confidence_score"] for m in msgs if m.get("confidence_score") is not None]
            s["live_message_count"]   = len(msgs)
            s["live_avg_confidence"]  = round(sum(conf_vals) / len(conf_vals), 3) if conf_vals else None
            s["live_escalated"]       = any(m.get("escalated") for m in msgs)
            s["live_total_tokens"]    = sum(m.get("total_tokens") or 0 for m in msgs)
            s["live_est_cost_usd"]    = round(sum(m.get("est_cost_usd") or 0 for m in msgs), 5)

    return {"page": page, "page_size": page_size, "sessions": sessions}


# =============================================================================
# GET /analytics/session/{session_id}
# Full transcript + metadata for one session.
# Used by the Transcript Modal in the Analytics Dashboard.
# =============================================================================

@app.get("/analytics/session/{session_id}")
async def analytics_session_detail(session_id: str):
    s = _db.table("sessions").select("*").eq("session_id", session_id).execute()
    if not s.data:
        raise HTTPException(status_code=404, detail="Session not found")

    m = (
        _db.table("messages")
        .select("*")
        .eq("session_id", session_id)
        .order("timestamp")
        .execute()
    )

    return {"session": s.data[0], "messages": m.data or []}


# =============================================================================
# GET /health
# Used by deployment platforms (Railway, Render, etc.) to check if the server
# is alive. Returns 200 OK when the app is running.
# =============================================================================

@app.get("/health")
async def health():
    return {"status": "ok"}
