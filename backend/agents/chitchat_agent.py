import os

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_groq import ChatGroq

from backend.state import ResolveState

load_dotenv()

MODEL = "llama-3.1-8b-instant"

_llm = ChatGroq(
    model=MODEL,
    temperature=0.7,    # Slightly warm — greetings should feel natural, not robotic
    api_key=os.getenv("GROQ_API_KEY"),
)

_SYSTEM_PROMPT = """You are a warm, friendly customer support agent for CartFlow, \
India's leading eCommerce platform.

Your name is ResolveDesk Assistant. Do not introduce yourself with any other name.

The customer is making small talk or sending a greeting. Respond naturally and warmly.
Keep your response to 2–3 sentences maximum.
After your greeting, gently mention what you can help with:
orders, returns, refunds, shipping, payments, or account questions.

Do NOT make up CartFlow policies or order information.
Do NOT ask for personal details unprompted."""


def run_chitchat_agent(state: ResolveState) -> dict:
    """
    Generate a warm reply to a greeting or small talk message.
    No confidence score — chitchat never escalates.
    """
    user_message = state["messages"][-1].content

    response = _llm.invoke([
        SystemMessage(content=_SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ])

    try:
        usage = response.response_metadata.get("token_usage", {}) or {}
        chitchat_tokens = int(usage.get("total_tokens", 0) or 0)
    except Exception:
        chitchat_tokens = 0

    return {
        "agent_response":   response.content.strip(),
        "confidence_score": None,
        "escalated":        False,
        "chitchat_tokens":  chitchat_tokens,
    }
