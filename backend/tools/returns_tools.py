# =============================================================================
# backend/tools/returns_tools.py
# =============================================================================
# ResolveDesk — Returns Tool (LangChain Tool for the Returns Agent)
#
# WHAT THIS FILE DOES:
#   Defines one LangChain tool the Returns Agent can call:
#
#   check_return_eligibility(order_id)
#     → Checks whether an order is eligible for a return
#     → If eligible: return window, condition requirements, refund method,
#       refund timeline, whether a return label is available
#     → If ineligible: explains exactly why (not delivered yet, cancelled,
#       outside return window, etc.)
#
# WHY A SEPARATE FILE FROM order_tools.py?
#   Separation of concerns — the Returns Agent only needs return data,
#   and the Order Agent only needs order status data. Keeping them separate
#   means each agent gets exactly the tools it needs, nothing more.
#   An LLM with fewer tools makes more accurate tool-calling decisions.
#
# IN PRODUCTION:
#   Replace db.get_return_eligibility() with a call to your Returns
#   Management System (RMS) or OMS returns API.
# =============================================================================

from langchain_core.tools import tool
from backend.db.db import get_return_eligibility, get_order_by_id


# =============================================================================
# HELPER — Format a return eligibility dict into a readable string for the LLM
# =============================================================================

def _format_eligibility(record: dict, order_id: str) -> str:
    """Convert a raw return_eligibility dict from db.py into a readable summary."""

    if record["eligible"]:
        lines = [
            f"Return Eligibility for {order_id}: ELIGIBLE ✓",
            f"Reason:               {record['reason']}",
            f"Return Window:        {record['return_window_days']} days",
            f"Delivery Date:        {record.get('delivery_date') or 'N/A'}",
            f"Days Since Delivery:  {record.get('days_since_delivery') if record.get('days_since_delivery') is not None else 'N/A'}",
            f"Condition Required:   {record['condition_requirement']}",
            f"Refund Method:        {record['refund_method']}",
            f"Refund Timeline:      {record['refund_timeline']}",
            f"Return Label:         {'Available — free pickup will be arranged' if record['return_label_available'] else 'Not available'}",
            "",
            "How to raise the return request:",
            "  1. Go to My Orders in the CartFlow app or website",
            "  2. Select this order and tap Return / Exchange",
            "  3. Choose the return reason and upload a photo if required",
            "  4. Submit — CartFlow will confirm within 24 hours and schedule free pickup",
        ]
    else:
        lines = [
            f"Return Eligibility for {order_id}: NOT ELIGIBLE ✗",
            f"Reason: {record['reason']}",
        ]
        # Add refund info if relevant (e.g. order was cancelled and already refunded)
        if record.get("refund_timeline") and record["refund_timeline"] != "N/A":
            lines.append(f"Refund Info: {record['refund_method']} — {record['refund_timeline']}")

    return "\n".join(lines)


# =============================================================================
# TOOL — Check Return Eligibility
# =============================================================================

@tool
def check_return_eligibility(order_id: str) -> str:
    """
    Check whether a CartFlow order is eligible for a return or exchange.

    Use this tool when the customer:
    - Asks if they can return an item or initiate a return
    - Asks about the return window or return policy for their specific order
    - Wants to know how to return something they received
    - Asks whether they are eligible for a refund on a delivered order
    - Asks about exchange options for a delivered order
    - Provides an order ID and mentions words like return, exchange, refund,
      wrong item, damaged, or not satisfied

    Input: the order ID exactly as the customer provided it (e.g. "ORD-10001").
    Do not guess or make up an order ID — only call this if the customer has given one.

    Returns: whether the order is eligible for return, the reason, the return window,
    condition requirements, refund method, refund timeline, and step-by-step
    instructions for raising the return request if eligible.
    If ineligible, returns a clear explanation of why.
    """
    order_id_clean = order_id.strip().upper()

    # First confirm the order actually exists
    order = get_order_by_id(order_id_clean)
    if not order:
        return (
            f"No order found with ID '{order_id}'. "
            "Please check the order ID — it should look like ORD-10001. "
            "The customer can find it in their confirmation email or the CartFlow app under My Orders."
        )

    # Now check the return eligibility record
    record = get_return_eligibility(order_id_clean)
    if not record:
        return (
            f"Return eligibility information is not available for order '{order_id_clean}'. "
            f"The order status is currently '{order['status']}'. "
            "Please advise the customer to contact CartFlow support directly via live chat "
            "or call 1800-XXX-XXXX for assistance with this return."
        )

    return _format_eligibility(record, order_id_clean)


# =============================================================================
# TOOL LIST — exported so the Returns Agent can bind tools in one line:
#   from backend.tools.returns_tools import RETURNS_TOOLS
#   llm_with_tools = llm.bind_tools(RETURNS_TOOLS)
# =============================================================================

RETURNS_TOOLS = [check_return_eligibility]
