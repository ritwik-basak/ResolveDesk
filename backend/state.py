from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages


class ResolveState(TypedDict):
    # ------------------------------------------------------------------
    # Conversation history — managed by LangGraph.
    # add_messages means new messages are appended, not replaced.
    # Contains HumanMessage, AIMessage, ToolMessage objects.
    # ------------------------------------------------------------------
    messages: Annotated[list, add_messages]

    # ------------------------------------------------------------------
    # Session context — set by main.py before the graph runs.
    # ------------------------------------------------------------------
    customer_email: str    # email entered on the chat start screen
    session_id:     str    # UUID, also used as LangGraph thread_id

    # ------------------------------------------------------------------
    # Routing — set by the supervisor, read by all other agents.
    # One of: "chitchat" | "faq" | "order" | "returns" | "escalation"
    # ------------------------------------------------------------------
    intent: str | None

    # ------------------------------------------------------------------
    # Agent output — set by whichever specialist agent ran last.
    # This is the final text response sent back to the user.
    # ------------------------------------------------------------------
    agent_response: str | None

    # ------------------------------------------------------------------
    # Confidence & RAG metrics — set by the specialist agent.
    # Used by the graph to decide whether to escalate.
    # ------------------------------------------------------------------
    confidence_score:     float | None   # agent's self-reported confidence (0–1)
    rag_best_score:       float | None   # retriever's top CrossEncoder score (FAQ only)
    rag_chunks_retrieved: int            # how many chunks the retriever returned

    # ------------------------------------------------------------------
    # Escalation — set by any agent that can't handle the query.
    # The graph routes to escalation_agent when escalated = True.
    # ------------------------------------------------------------------
    escalated:         bool
    escalation_reason: str | None   # "retrieval_score_low" | "confidence_low" | "supervisor_unclear"

    # ------------------------------------------------------------------
    # Query rewriting — set by faq_agent when first retrieval score is low.
    # retry_attempted = True means the rewrite happened (pass or fail).
    # rewritten_query = the rewritten version of the original query.
    # ------------------------------------------------------------------
    retry_attempted:  bool
    rewritten_query:  str | None

    # ------------------------------------------------------------------
    # Performance — set by main.py after the graph finishes.
    # Passed to the analytics tracker.
    # ------------------------------------------------------------------
    total_tokens:      int        # Groq Llama 3.3 70B tokens (faq/order/returns/escalation)
    chitchat_tokens:   int        # Groq Llama 3.1 8B tokens (chitchat only)
    supervisor_tokens: int        # Gemini 2.5 Flash (supervisor) tokens this turn
    cache_hit:         bool
    response_time_ms:  int | None
