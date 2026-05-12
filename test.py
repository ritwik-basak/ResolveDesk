import sys
from langchain_core.messages import HumanMessage
from backend.rag.retriever import retriever
from backend.agents.faq_agent import run_faq_agent

print("\n=== ResolveDesk FAQ Test ===")
print("Type a question and press Enter. Type 'quit' to exit.\n")

while True:
    query = input("Enter query: ").strip()
    if query.lower() in ("quit", "exit", "q"):
        break

    print("\n[1] Running retriever...")
    result = retriever.retrieve(query)
    print(f"    best_score:  {result['best_score']}")
    print(f"    chunks found: {len(result['chunks'])}")
    for i, c in enumerate(result["chunks"], 1):
        print(f"    chunk {i}: {c['source']} (index {c['chunk_index']})")

    print("\n[2] Running FAQ agent...")
    state = {
        "messages": [HumanMessage(content=query)],
        "customer_email": "test@test.com",
        "session_id": "test-001",
        "intent": "faq",
        "agent_response": None,
        "confidence_score": None,
        "rag_best_score": None,
        "rag_chunks_retrieved": 0,
        "escalated": False,
        "escalation_reason": None,
        "retry_attempted": False,
        "rewritten_query": None,
        "cache_hit": False,
        "response_time_ms": None,
    }

    agent_result = run_faq_agent(state)

    print(f"    escalated:        {agent_result['escalated']}")
    print(f"    reason:           {agent_result.get('escalation_reason')}")
    print(f"    confidence:       {agent_result.get('confidence_score')}")
    print(f"    rag_score:        {agent_result.get('rag_best_score')}")
    print(f"    retry_attempted:  {agent_result.get('retry_attempted', False)}")
    if agent_result.get('rewritten_query'):
        print(f"    rewritten_query: \"{agent_result['rewritten_query']}\"")

    if agent_result.get("agent_response"):
        print(f"\n[3] Response:\n{agent_result['agent_response']}")
    else:
        print("\n[3] Escalated — no response generated")

    print("\n" + "-" * 50 + "\n")
