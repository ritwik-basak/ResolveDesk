import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from backend.state import ResolveState

load_dotenv()

MODEL = "llama-3.3-70b-versatile"

_llm = ChatGroq(
    model=MODEL,
    temperature=0.3,    # Slightly above zero — empathetic tone needs a little warmth
    api_key=os.getenv("GROQ_API_KEY"),
)

# =============================================================================
# SYSTEM PROMPT
# =============================================================================

_SYSTEM_PROMPT = """You are a senior customer support agent for CartFlow, \
India's leading eCommerce platform.

This customer's query needs to be handled by a human support specialist.
Your job is to write a professional, empathetic handoff message.

Your message must:
1. Acknowledge the customer's issue briefly and empathetically (1 sentence)
2. Let them know you're connecting them with a specialist who can help
3. Give them these direct contact options clearly:
   - Live Chat: Available 24/7 in the CartFlow app (average wait: under 2 minutes)
   - Phone: 1800-XXX-XXXX (Mon–Sat 9 AM–9 PM, Sun 10 AM–6 PM IST)
   - Email: support@cartflow.in (response within 24 hours)
4. Set expectations: most issues resolved within 24–48 hours

Keep the tone warm, professional, and reassuring.
Do NOT mention any technical reason for the escalation.
Do NOT say words like "error", "failed", "threshold", or "confidence".
Keep the message concise — 4 to 6 sentences."""

# =============================================================================
# HUMAN-READABLE REASON MAP
# Converts internal escalation reason codes into context for the LLM prompt.
# The LLM uses this context to tailor the empathy in its message — but never
# reveals the technical reason to the customer.
# =============================================================================

_REASON_CONTEXT = {
    "supervisor_unclassified": "The customer's request is unusual or outside standard support topics.",
    "weak_rag_match":          "The customer is asking about something our knowledge base doesn't cover well.",
    "low_confidence":          "The customer's issue is complex and needs specialist attention.",
}


# =============================================================================
# AGENT FUNCTION
# =============================================================================

def run_escalation_agent(state: ResolveState) -> dict:
    """
    Generate a warm human handoff message.
    The escalation_reason from state is used to give the LLM context
    for tone — but never exposed to the customer.
    """
    user_message     = state["messages"][-1].content
    escalation_reason = state.get("escalation_reason") or "low_confidence"

    # Internal context for the LLM — helps it write the right tone of empathy
    reason_context = _REASON_CONTEXT.get(escalation_reason, _REASON_CONTEXT["low_confidence"])

    prompt = (
        f"Internal context (do not mention to the customer): {reason_context}\n\n"
        f"Customer's message: {user_message}"
    )

    response = _llm.invoke([
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=prompt),
    ])

    return {
        "agent_response":   response.content.strip(),
        "escalated":        True,     # confirm final state
        "confidence_score": None,     # no confidence for escalation
    }
