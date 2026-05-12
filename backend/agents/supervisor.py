import os
import re

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from backend.state import ResolveState

load_dotenv()

# =============================================================================
# MODEL
# =============================================================================

MODEL = "gemini-2.5-flash"

_llm = ChatGoogleGenerativeAI(
    model=MODEL,
    temperature=0,                  # Zero temperature = deterministic, consistent routing
    google_api_key=os.getenv("GOOGLE_API_KEY"),
)

# =============================================================================
# SYSTEM PROMPT
# The system prompt is the supervisor's "job description".
# It must be precise — any ambiguity leads to misclassification.
# =============================================================================

_SYSTEM_PROMPT = """You are a message router for CartFlow customer support.

Your ONLY job is to classify the customer's message into exactly one of these five categories:

chitchat   — greetings, small talk, thank you messages, general pleasantries,
             AND vague complaints or unclear requests where the customer hasn't
             specified what they need yet — the chitchat agent will ask for more details
             Examples: "Hi", "Hello", "Thanks!", "I am having an issue",
                       "I need help", "Something is wrong", "I have a problem"

faq        — questions about CartFlow policies, products, shipping timelines,
             return/refund rules, payment methods, or account management
             Examples: "What is your return policy?", "How long does shipping take?",
                       "What payment methods do you accept?", "How do I reset my password?"

order      — questions about the status of a specific order, delivery date,
             tracking information, or items in an order
             Examples: "Where is my order?", "When will ORD-10002 arrive?",
                       "What did I order last week?", "Show me my recent orders"

returns    — requests to return, exchange, or get a refund on an already-delivered item
             Examples: "I want to return my headphones", "Can I exchange this?",
                       "How do I return ORD-10001?", "I received the wrong item"

escalation — ONLY messages that are abusive, threatening, or offensive.
             Do NOT use escalation for vague requests — use chitchat instead.

Reply with ONLY the category label — one word, lowercase, no punctuation, nothing else."""

# =============================================================================
# VALID ROUTES — fallback if LLM produces unexpected output
# =============================================================================

_VALID_ROUTES = {"chitchat", "faq", "order", "returns", "escalation"}


# =============================================================================
# AGENT FUNCTION
# Called by LangGraph as a node. Receives full state, returns partial update.
# =============================================================================

def run_supervisor(state: ResolveState) -> dict:
    """
    Classify the latest user message into one of 5 routes.
    Returns: {"intent": "<route>"}
    """
    user_message = state["messages"][-1].content

    response = _llm.invoke([
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ])

    # Track Gemini token usage (langchain-google-genai exposes usage_metadata)
    try:
        usage = getattr(response, "usage_metadata", {}) or {}
        supervisor_tokens = (usage.get("input_tokens", 0) or 0) + (usage.get("output_tokens", 0) or 0)
    except Exception:
        supervisor_tokens = 0

    # Extract just the route label — strip whitespace, lowercase
    route = response.content.strip().lower()

    # Remove any stray punctuation the LLM might have added
    route = re.sub(r"[^a-z]", "", route)

    # Fallback: if the LLM returned something unexpected, escalate
    if route not in _VALID_ROUTES:
        route = "escalation"

    return {
        "intent":             route,
        "escalated":          False,   # reset escalation at the start of each turn
        "escalation_reason":  None,
        "agent_response":     None,
        "confidence_score":   None,
        "rag_best_score":     None,
        "rag_chunks_retrieved": 0,
        "supervisor_tokens":  supervisor_tokens,
    }
