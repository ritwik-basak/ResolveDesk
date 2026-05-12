import os
import re

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq

from backend.state import ResolveState
from backend.tools.returns_tools import RETURNS_TOOLS

load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

MODEL                = "llama-3.3-70b-versatile"
CONFIDENCE_THRESHOLD = 0.75

_llm            = ChatGroq(model=MODEL, temperature=0, api_key=os.getenv("GROQ_API_KEY"))
_llm_with_tools = _llm.bind_tools(RETURNS_TOOLS)

_TOOL_MAP = {tool.name: tool for tool in RETURNS_TOOLS}

# =============================================================================
# SYSTEM PROMPT
# =============================================================================

_SYSTEM_PROMPT = """You are a helpful customer support agent for CartFlow, \
India's leading eCommerce platform.

You have access to a tool to check real-time return eligibility from the CartFlow database.

When a customer asks about returning or exchanging an item:
- Use check_return_eligibility if they provide an order ID (e.g. ORD-10001)
- If they don't provide an order ID, politely ask for it
- Clearly explain whether their order is eligible and exactly why
- If eligible, walk them through the return steps
- If ineligible, explain the reason empathetically

Be empathetic — returns can be frustrating. Acknowledge the customer's situation.

Write in plain text only. Do not use markdown, asterisks, bold (**), or bullet symbols (*). Use a dash (-) for any lists.

At the end of your response, on a new line, write exactly:
CONFIDENCE: [score]
where [score] is a number between 0.0 and 1.0 representing how confident you are
that you have fully addressed the customer's question.

0.9–1.0 = you checked eligibility and gave a complete answer
0.7–0.9 = partial answer or customer needs to provide more information
0.0–0.7 = could not resolve the customer's issue"""


# =============================================================================
# HELPERS — identical to order_agent.py
# =============================================================================

def _parse_confidence(text: str) -> tuple[str, float]:
    pattern = r"\bCONFIDENCE:\s*(0(?:\.\d+)?|1(?:\.0+)?)\b"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        score      = float(match.group(1))
        clean_text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
        clean_text = re.sub(r"\n{3,}", "\n\n", clean_text).strip()
        return clean_text, score
    return text.strip(), 0.5


def _run_tool(tool_name: str, tool_args: dict) -> str:
    tool = _TOOL_MAP.get(tool_name)
    if not tool:
        return f"Error: unknown tool '{tool_name}'"
    return tool.invoke(tool_args)


# =============================================================================
# AGENT FUNCTION
# =============================================================================

_NO_ORDER_ID_RESPONSE = (
    "I'd be happy to help with your return! To check your eligibility, "
    "I'll need your order ID.\n\n"
    "It looks like ORD-10001 and can be found in:\n"
    "- Your order confirmation email\n"
    "- CartFlow app > My Orders\n\n"
    "Could you please share it?"
)


def _find_order_id(messages) -> str | None:
    """Search the last 6 messages for a CartFlow order ID."""
    for msg in reversed(messages[-6:]):
        m = re.search(r'\b(ORD-\d+)\b', getattr(msg, 'content', ''), re.IGNORECASE)
        if m:
            return m.group(1)
    return None


def run_returns_agent(state: ResolveState) -> dict:
    """
    Tool-calling loop to check return eligibility and generate a response.
    Searches recent conversation history for an order ID so the user
    doesn't have to repeat it if they already gave it earlier.
    """
    user_message = state["messages"][-1].content
    order_id     = _find_order_id(state["messages"])

    # If no order ID found anywhere in recent conversation, ask for it
    if not order_id:
        return {
            "agent_response":    _NO_ORDER_ID_RESPONSE,
            "confidence_score":  0.9,
            "escalated":         False,
            "escalation_reason": None,
        }

    # Include the found order ID in the message so the LLM uses it
    enriched = user_message if order_id in user_message.upper() else f"{user_message} (Order ID: {order_id})"

    agent_messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=enriched),
    ]

    final_response = None
    tokens = 0
    for _ in range(5):
        response = _llm_with_tools.invoke(agent_messages)
        agent_messages.append(response)
        try:
            tokens += int(response.response_metadata.get('token_usage', {}).get('total_tokens', 0) or 0)
        except Exception:
            pass

        if not response.tool_calls:
            final_response = response.content
            break

        for tc in response.tool_calls:
            result = _run_tool(tc["name"], tc["args"])
            agent_messages.append(ToolMessage(content=result, tool_call_id=tc["id"]))

    if not final_response:
        final_response = "I'm having trouble checking return eligibility right now. Please try again."

    clean_response, confidence = _parse_confidence(final_response)

    if confidence < CONFIDENCE_THRESHOLD:
        return {
            "escalated":         True,
            "escalation_reason": "low_confidence",
            "agent_response":    None,
            "confidence_score":  confidence,
            "total_tokens":      tokens,
        }

    return {
        "agent_response":    clean_response,
        "confidence_score":  confidence,
        "escalated":         False,
        "escalation_reason": None,
        "total_tokens":      tokens,
    }
