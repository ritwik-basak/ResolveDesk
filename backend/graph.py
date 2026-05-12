from langgraph.graph import END, START, StateGraph

from backend.agents.chitchat_agent import run_chitchat_agent
from backend.agents.escalation_agent import run_escalation_agent
from backend.agents.faq_agent import run_faq_agent
from backend.agents.order_agent import run_order_agent
from backend.agents.returns_agent import run_returns_agent
from backend.agents.supervisor import run_supervisor
from backend.state import ResolveState


# =============================================================================
# ROUTING FUNCTIONS
# These are the "decision makers" on conditional edges.
# LangGraph calls them after a node finishes and uses the return value
# to decide which node to visit next.
# =============================================================================

def route_from_supervisor(state: ResolveState) -> str:
    """
    Read state["intent"] set by the supervisor and return the next node name.
    The 5 possible values match the 5 node names exactly — no mapping needed.
    """
    return state["intent"]   # "chitchat" | "faq" | "order" | "returns" | "escalation"


def route_after_specialist(state: ResolveState) -> str:
    """
    After faq / order / returns agent runs, check if it set escalated=True.
    If yes → go to escalation agent.
    If no  → end the graph (response is ready).
    """
    if state.get("escalated"):
        return "escalation"
    return END


# =============================================================================
# GRAPH DEFINITION
# Build the node/edge structure once at module level.
# This is fast — we're just describing the shape of the graph, not running it.
# The actual execution happens when graph.invoke() / graph.ainvoke() is called.
# =============================================================================

def _build_graph_structure() -> StateGraph:
    """
    Define all nodes and edges. Returns an uncompiled StateGraph.
    Separated from build_graph() so the structure is created once,
    and only the compile step (which needs the checkpointer) runs later.
    """
    g = StateGraph(ResolveState)

    # ------------------------------------------------------------------
    # NODES — each node is an agent function that reads state and
    # returns a partial state update (a dict of changed fields only). #ResolveState is a TypedDict that every node reads from and writes partial updates back to — fields like intent, escalated, agent_response, rag_best_score, etc. Nodes never talk to each other directly; they only read/write this shared state.
    # add_node registers the function under a name. LangGraph will call run_faq_agent(state) when execution reaches the "faq" node. The function returns a partial dict — only the fields it changed — and LangGraph merges that back into the shared state.
    # ------------------------------------------------------------------
    g.add_node("supervisor",  run_supervisor)
    g.add_node("chitchat",    run_chitchat_agent)
    g.add_node("faq",         run_faq_agent) 
    g.add_node("order",       run_order_agent)
    g.add_node("returns",     run_returns_agent)
    g.add_node("escalation",  run_escalation_agent)

    # ------------------------------------------------------------------
    # ENTRY POINT — every message starts at the supervisor
    # ------------------------------------------------------------------
    g.add_edge(START, "supervisor")

    # ------------------------------------------------------------------
    # SUPERVISOR → specialist (conditional)
    # route_from_supervisor reads state["intent"] and returns the node name.
    # The dict maps every possible return value to a node — LangGraph
    # uses this to validate that all routes are reachable.
    # ------------------------------------------------------------------
    g.add_conditional_edges(
        "supervisor",
        route_from_supervisor,
        {
            "chitchat":   "chitchat",
            "faq":        "faq",
            "order":      "order",
            "returns":    "returns",
            "escalation": "escalation",
        },
    )

    # ------------------------------------------------------------------
    # CHITCHAT → END (direct — never escalates)
    # ------------------------------------------------------------------
    g.add_edge("chitchat", END)

    # ------------------------------------------------------------------
    # FAQ / ORDER / RETURNS → escalation or END (conditional)
    # route_after_specialist checks state["escalated"].
    # All three use the same routing function — same logic applies.
    # ------------------------------------------------------------------
    g.add_conditional_edges(
        "faq",
        route_after_specialist,
        {"escalation": "escalation", END: END},
    )
    g.add_conditional_edges(
        "order",
        route_after_specialist,
        {"escalation": "escalation", END: END},
    )
    g.add_conditional_edges(
        "returns",
        route_after_specialist,
        {"escalation": "escalation", END: END},
    )

    # ------------------------------------------------------------------
    # ESCALATION → END (terminal — no further routing possible)
    # ------------------------------------------------------------------
    g.add_edge("escalation", END)

    return g


# Build the structure once when this module is imported
_graph_structure = _build_graph_structure()


# =============================================================================
# build_graph — called by main.py at startup
#
# WHY SEPARATE FROM _build_graph_structure?
#   The structure (nodes + edges) never changes — build it once.
#   The checkpointer is created fresh at startup by main.py, so we compile
#   with the live checkpointer only when it's available.
# =============================================================================

def build_graph(checkpointer):
    """
    Compile the graph with a checkpointer and return the runnable graph.

    Args:
        checkpointer: An AsyncPostgresSaver instance from checkpointer.py.

    Returns:
        A compiled LangGraph runnable. Call with:
            await graph.ainvoke(state, config={"configurable": {"thread_id": session_id}})
    """
    return _graph_structure.compile(checkpointer=checkpointer)
