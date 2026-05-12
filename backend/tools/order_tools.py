# =============================================================================
# backend/tools/order_tools.py
# =============================================================================
# ResolveDesk — Order Tools (LangChain Tools for the Order Agent)
#
# WHAT THIS FILE DOES:
#   Defines two LangChain tools the Order Agent can call:
#
#   1. get_order_status(order_id)
#      → Look up one order by its ID (e.g. "ORD-10001")
#      → Returns status, delivery dates, tracking, items, address
#
#   2. get_orders_by_email(customer_email)
#      → Find ALL orders for a customer by their email address
#      → Useful when the customer doesn't have their order ID handy
#
# HOW TOOL CALLING WORKS:
#   The Order Agent is given these tools as a list. When the LLM receives
#   a user message, it reads each tool's docstring (description) and decides:
#   "Does the user need something this tool can provide?"
#
#   If yes, the LLM outputs a structured "tool call" — not a text reply —
#   specifying which tool to call and with what arguments. LangChain runs
#   the function, sends the result back to the LLM, and the LLM uses that
#   result to generate the final human-readable response.
#
#   The docstring IS the tool description. Write it as if explaining
#   to the LLM exactly when and why to use the tool.
#
# IN PRODUCTION:
#   Replace db.get_order_by_id() calls with requests to your real
#   Order Management System (OMS) API — Shopify, WooCommerce, SAP, etc.
#   The agent code does not need to change at all, only this file.
# =============================================================================

from langchain_core.tools import tool
from backend.db.db import get_order_by_id, get_orders_by_customer_email


# =============================================================================
# HELPER — Format a single order dict into a readable string for the LLM
#
# WHY RETURN A STRING AND NOT A DICT?
#   LangChain tools pass their return value back to the LLM as text.
#   A clean, labelled string is easier for the LLM to read and summarise
#   than raw JSON. Think of it as writing a status report the LLM can quote.
# =============================================================================

def _format_order(order: dict) -> str:
    """Convert a raw order dict from db.py into a readable summary string."""

    # Format the items list into a numbered list of product names + quantities
    items = order.get("items") or []
    if items:
        items_str = "\n".join(
            f"  {i+1}. {item['product']} x{item['qty']} — ₹{item['price']:.2f}"
            for i, item in enumerate(items)
        )
    else:
        items_str = "  (items not available)"

    # Build the full summary — every field the agent might need
    lines = [
        f"Order ID:           {order['order_id']}",
        f"Customer:           {order['customer_name']} ({order['customer_email']})",
        f"Order Date:         {order['order_date']}",
        f"Status:             {order['status']}",
        f"Items Ordered:\n{items_str}",
        f"Subtotal:           ₹{order['subtotal']:.2f}",
        f"Shipping Cost:      ₹{order['shipping_cost']:.2f}",
        f"Total:              ₹{order['total']:.2f}",
        f"Payment Method:     {order['payment_method']}",
        f"Shipping Address:   {order['shipping_address']}",
        f"Carrier:            {order.get('carrier') or 'Not assigned yet'}",
        f"Tracking Number:    {order.get('tracking_number') or 'Not assigned yet'}",
        f"Tracking URL:       {order.get('tracking_url') or 'Not available yet'}",
        f"Estimated Delivery: {order.get('estimated_delivery') or 'Not available'}",
        f"Actual Delivery:    {order.get('actual_delivery') or 'Not yet delivered'}",
    ]

    # Only show cancellation/refund fields if they have values
    if order.get("cancellation_reason"):
        lines.append(f"Cancellation Reason: {order['cancellation_reason']}")
    if order.get("refund_status"):
        lines.append(f"Refund Status:      {order['refund_status']}")

    return "\n".join(lines)


# =============================================================================
# TOOL 1 — Get Order Status by Order ID
# =============================================================================

@tool
def get_order_status(order_id: str) -> str:
    """
    Look up the full details of a CartFlow order using its order ID.

    Use this tool when the customer:
    - Asks where their order is or what the delivery status is
    - Wants to know the estimated or actual delivery date
    - Asks for tracking information or a tracking link
    - Wants to know what items are in their order
    - Asks about their payment method or order total
    - Provides an order ID (e.g. ORD-10001, ORD-10003) in their message

    Input: the order ID exactly as the customer provided it (e.g. "ORD-10001").
    Do not guess or make up an order ID — only call this if the customer has given one.

    Returns: a detailed summary including status, delivery dates, tracking number,
    carrier, items ordered, total amount, and shipping address.
    """
    order = get_order_by_id(order_id.strip().upper())

    if not order:
        return (
            f"No order found with ID '{order_id}'. "
            "Please check the order ID — it should look like ORD-10001. "
            "The customer can find their order ID in their confirmation email or SMS, "
            "or by checking My Orders in the CartFlow app."
        )

    return _format_order(order)


# =============================================================================
# TOOL 2 — Get All Orders by Customer Email
# =============================================================================

@tool
def get_orders_by_email(customer_email: str) -> str:
    """
    Find all CartFlow orders placed by a customer using their email address.

    Use this tool when:
    - The customer does not have their order ID but provides their email address
    - The customer asks "what orders do I have?" or "show me my recent orders"
    - You need to identify which order the customer is referring to before looking up details
    - The customer asks about multiple orders at once

    Input: the customer's email address exactly as they provided it.

    Returns: a list of all their orders with order IDs, dates, statuses, and totals.
    If multiple orders are found, you can ask the customer which one they mean,
    or call get_order_status with the relevant order ID for full details.
    """
    orders = get_orders_by_customer_email(customer_email.strip())

    if not orders:
        return (
            f"No orders found for email address '{customer_email}'. "
            "Please check the email — it must be the same address used when placing the order. "
            "The customer may have used a different email or placed the order as a guest."
        )

    # Return a brief summary of each order (not full details — use get_order_status for that)
    lines = [f"Found {len(orders)} order(s) for {customer_email}:\n"]
    for order in orders:
        items = order.get("items") or []
        item_names = ", ".join(item["product"] for item in items[:2])
        if len(items) > 2:
            item_names += f" + {len(items) - 2} more"

        lines.append(
            f"• {order['order_id']} | {order['order_date']} | "
            f"Status: {order['status']} | ₹{order['total']:.2f} | {item_names}"
        )

    lines.append(
        "\nTo get full details (tracking, delivery date, etc.) for a specific order, "
        "use the get_order_status tool with the relevant order ID."
    )

    return "\n".join(lines)


# =============================================================================
# TOOL LIST — exported so the Order Agent can bind both tools in one line:
#   from backend.tools.order_tools import ORDER_TOOLS
#   llm_with_tools = llm.bind_tools(ORDER_TOOLS)
# =============================================================================

ORDER_TOOLS = [get_order_status, get_orders_by_email]
