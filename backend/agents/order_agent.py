import os
import re

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_groq import ChatGroq

from backend.state import ResolveState
from backend.tools.order_tools import ORDER_TOOLS

load_dotenv()

# =============================================================================
# CONFIGURATION
# =============================================================================

MODEL                = "llama-3.3-70b-versatile"
CONFIDENCE_THRESHOLD = 0.75

_llm            = ChatGroq(model=MODEL, temperature=0, api_key=os.getenv("GROQ_API_KEY"))
_llm_with_tools = _llm.bind_tools(ORDER_TOOLS)

# Map tool name → callable, so we can execute tool calls by name
_TOOL_MAP = {tool.name: tool for tool in ORDER_TOOLS}

# =============================================================================
# SYSTEM PROMPT
# =============================================================================

_SYSTEM_PROMPT = """You are a helpful customer support agent for CartFlow, \
India's leading eCommerce platform.

You have access to tools to look up real order information from the CartFlow database.

When a customer asks about an order:
- Use get_order_status if they provide an order ID (e.g. ORD-10001)
- Use get_orders_by_email if they provide an email address but no order ID
- If they provide neither, politely ask for their order ID or registered email address

Provide a clear, friendly, and complete response based on the tool result.

Write in plain text only. Do not use markdown, asterisks, bold (**), or bullet symbols (*). Use a dash (-) for any lists.

At the end of your response, on a new line, write exactly:
CONFIDENCE: [score]
where [score] is a number between 0.0 and 1.0 representing how confident you are
that you have fully addressed the customer's question.

0.9–1.0 = you found the order and answered completely
0.7–0.9 = you found partial information or the customer needs to clarify
0.0–0.7 = you could not find what the customer needed"""


# =============================================================================
# HELPERS
# =============================================================================

def _parse_confidence(text: str) -> tuple[str, float]:
    """Extract CONFIDENCE score. Returns (clean_text, score). Defaults to 0.5."""
    pattern = r"\bCONFIDENCE:\s*(0(?:\.\d+)?|1(?:\.0+)?)\b"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        score      = float(match.group(1))
        clean_text = re.sub(pattern, "", text, flags=re.IGNORECASE).strip()
        clean_text = re.sub(r"\n{3,}", "\n\n", clean_text).strip()
        return clean_text, score
    return text.strip(), 0.5


def _run_tool(tool_name: str, tool_args: dict) -> str:
    """Execute a tool by name and return its string result."""
    tool = _TOOL_MAP.get(tool_name)
    if not tool:
        return f"Error: unknown tool '{tool_name}'"
    return tool.invoke(tool_args)


# =============================================================================
# AGENT FUNCTION
# =============================================================================

_NO_ORDER_ID_RESPONSE = (
    "I'd be happy to help with your order! To look up the details, "
    "I'll need your order ID.\n\n"
    "It looks like ORD-10001 and can be found in:\n"
    "- Your order confirmation email\n"
    "- CartFlow app > My Orders\n\n"
    "Could you please share it?"
)


def run_order_agent(state: ResolveState) -> dict:
    """
    Tool-calling loop:
      1. If no order ID in message → ask for it immediately
      2. Otherwise: send to LLM with tools → execute tool → parse confidence
    """
    user_message = state["messages"][-1].content

    # Search conversation history for order ID (user may have given it earlier)
    order_id = None
    for msg in reversed(state["messages"][-6:]):
        m = re.search(r'\b(ORD-\d+)\b', getattr(msg, 'content', ''), re.IGNORECASE)
        if m:
            order_id = m.group(1)
            break

    if not order_id:
        return {
            "agent_response":    _NO_ORDER_ID_RESPONSE,
            "confidence_score":  0.9,
            "escalated":         False,
            "escalation_reason": None,
        }

    # Include found order ID in message so LLM uses the right one
    enriched = user_message if order_id in user_message.upper() else f"{user_message} (Order ID: {order_id})"

    # Build the message list for this agent's internal conversation.
    # This is separate from state["messages"] — it's just for this agent's
    # tool-calling loop. We don't add these to the LangGraph state directly.
    agent_messages = [
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=enriched),
    ]

    # ------------------------------------------------------------------
    # Tool calling loop
    # Runs until the LLM stops calling tools and gives a final response.
    # Typically 1–2 iterations (call tool once, read result, reply).
    # ------------------------------------------------------------------
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
        final_response = "I'm having trouble looking up that order right now. Please try again."

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
