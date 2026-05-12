import os
import re

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from backend.rag.retriever import retriever
from backend.state import ResolveState

load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

MODEL = "llama-3.3-70b-versatile"

RAG_SCORE_THRESHOLD  = float(os.getenv("RAG_SCORE_THRESHOLD", 0.60))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.75))

_llm = ChatGroq(
    model=MODEL,
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY"),
)

# =============================================================================
# PROMPTS
# =============================================================================

_SYSTEM_PROMPT = """You are a knowledgeable customer support agent for CartFlow, \
India's leading eCommerce platform.

Answer the customer's question using ONLY the information provided in the Context below.
Do not make up any information that is not in the context.
If the context does not contain enough information to fully answer, say so clearly.

Be concise and friendly. Use bullet points where helpful.

Write in plain text only. Do not use markdown, asterisks, bold (**), or bullet symbols (*). Use a dash (-) for any lists.

At the end of your response, on a new line, write exactly:
CONFIDENCE: [score]
where [score] is a number between 0.0 and 1.0 representing how confident you are
that your answer fully and correctly addresses the customer's question based on the context.

0.9–1.0 = context directly and completely answers the question
0.7–0.9 = context mostly answers the question
0.5–0.7 = context partially answers the question
0.0–0.5 = context barely addresses the question"""

# Query rewriting prompt — asks the LLM to rephrase for better semantic search.
# Temperature is set slightly higher (0.3) to allow creative rephrasing.
_REWRITE_PROMPT = (
    "Rewrite the following customer support query to be clearer and more specific "
    "for searching a knowledge base about eCommerce policies, shipping, returns, "
    "payments, and account management.\n"
    "Return ONLY the rewritten query — no explanation, no quotes.\n\n"
    "Original query: {query}\n"
    "Rewritten query:"
)


# =============================================================================
# HELPERS
# =============================================================================

def _build_context(chunks: list[dict]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, 1):
        parts.append(f"[{i}] Source: {chunk['source']}\n{chunk['text']}")
    return "\n\n".join(parts)


def _strip_markdown(text: str) -> str:
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    text = re.sub(r'^\* ', '- ', text, flags=re.MULTILINE)
    return text


def _parse_confidence(text: str) -> tuple[str, float]:
    """
    Extract the CONFIDENCE score from the LLM's response.
    Returns (clean_response_without_confidence_line, score).
    Falls back to 0.5 if the LLM didn't include the marker.
    """
    pattern = r"\bCONFIDENCE:\s*(0(?:\.\d+)?|1(?:\.0+)?)\b"
    match   = re.search(pattern, text, re.IGNORECASE)
    if match:
        score      = float(match.group(1))
        clean_text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
        clean_text = re.sub(r"\n{3,}", "\n\n", clean_text).strip()
        return clean_text, score
    return text.strip(), 0.5


def _get_tokens(response) -> int:
    try:
        usage = response.response_metadata.get('token_usage', {})
        return int(usage.get('total_tokens', 0) or 0)
    except Exception:
        return 0


def _rewrite_query(query: str) -> tuple[str, int]:
    """Rewrite a low-scoring query for better retrieval. Returns (rewritten_text, tokens_used)."""
    response = _llm.invoke([HumanMessage(content=_REWRITE_PROMPT.format(query=query))])
    return response.content.strip(), _get_tokens(response)


# =============================================================================
# AGENT FUNCTION
# =============================================================================

def run_faq_agent(state: ResolveState) -> dict:
    """
    FLOW:
      1. Retrieve chunks for the original query.
      2. If score < threshold → rewrite query → retry retrieval (one attempt).
         a. Retry passes → continue to answer.
         b. Retry also fails → escalate with weak_rag_match.
      3. Ask LLM to answer using the chunks as context.
      4. Parse confidence score from LLM response.
      5. If confidence < threshold → escalate with low_confidence.
      6. Return the answer.
    """
    user_message     = state["messages"][-1].content
    retry_attempted  = False
    rewritten_query  = None

    # ------------------------------------------------------------------
    # Step 1 — Retrieve chunks for the original query
    # ------------------------------------------------------------------
    result     = retriever.retrieve(user_message)
    chunks     = result["chunks"]
    best_score = result["best_score"]

    # ------------------------------------------------------------------
    # Step 2 — Trigger 1: weak retrieval
    # Before escalating, try ONE query rewrite and retry retrieval.
    # ------------------------------------------------------------------
    tokens = 0

    if best_score < RAG_SCORE_THRESHOLD or not chunks:
        rewritten_query, rewrite_tokens = _rewrite_query(user_message)
        tokens         += rewrite_tokens
        retry_attempted = True

        retry_result  = retriever.retrieve(rewritten_query)
        retry_chunks  = retry_result["chunks"]
        retry_score   = retry_result["best_score"]

        if retry_score >= RAG_SCORE_THRESHOLD and retry_chunks:
            # Retry succeeded — use the rewritten query's results
            chunks     = retry_chunks
            best_score = retry_score
        else:
            return {
                "escalated":            True,
                "escalation_reason":    "weak_rag_match",
                "rag_best_score":       max(best_score, retry_score),
                "rag_chunks_retrieved": len(retry_chunks),
                "confidence_score":     None,
                "agent_response":       None,
                "retry_attempted":      True,
                "rewritten_query":      rewritten_query,
                "total_tokens":         tokens,
            }

    # ------------------------------------------------------------------
    # Step 3 — Build context and ask the LLM
    # ------------------------------------------------------------------
    context = _build_context(chunks)
    prompt  = (
        f"Context:\n{context}\n\n"
        f"Customer question: {user_message}"
    )

    response = _llm.invoke([
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])
    tokens += _get_tokens(response)

    clean_response, confidence = _parse_confidence(_strip_markdown(response.content))

    # ------------------------------------------------------------------
    # Step 5 — Trigger 2: low LLM confidence
    # ------------------------------------------------------------------
    if confidence < CONFIDENCE_THRESHOLD:
        return {
            "escalated":            True,
            "escalation_reason":    "low_confidence",
            "agent_response":       None,
            "confidence_score":     confidence,
            "rag_best_score":       best_score,
            "rag_chunks_retrieved": len(chunks),
            "retry_attempted":      retry_attempted,
            "rewritten_query":      rewritten_query,
            "total_tokens":         tokens,
        }

    return {
        "agent_response":       clean_response,
        "confidence_score":     confidence,
        "rag_best_score":       best_score,
        "rag_chunks_retrieved": len(chunks),
        "escalated":            False,
        "escalation_reason":    None,
        "retry_attempted":      retry_attempted,
        "rewritten_query":      rewritten_query,
        "total_tokens":         tokens,
    }
