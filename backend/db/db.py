# =============================================================================
# backend/db/db.py
# =============================================================================
# CartFlow's database access layer.
#
# WHAT THIS FILE DOES:
#   Provides Python functions to look up customers, orders, and return
#   eligibility from the real Supabase PostgreSQL database.
#
# HOW IT WORKS:
#   - We use the supabase-py client (already in requirements.txt)
#   - supabase-py talks to Supabase over its REST API (built on PostgREST)
#   - All functions return plain Python dicts or lists — callers don't need
#     to know anything about Supabase or SQL
#
# SWAP-OUT PRINCIPLE:
#   If you ever move from Supabase to a different database, you only
#   change this file. Everything that calls these functions stays the same.
# =============================================================================

import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# =============================================================================
# SUPABASE CLIENT
# create_client() sets up a connection using your project URL + API key.
# Created once at module level and reused for every query.
# =============================================================================
_supabase_url = os.getenv("SUPABASE_URL")
_supabase_key = os.getenv("SUPABASE_KEY")

if not _supabase_url or not _supabase_key:
    raise EnvironmentError(
        "SUPABASE_URL and SUPABASE_KEY must be set in your .env file. "
        "Find them in Supabase Dashboard > Project Settings > API."
    )

supabase: Client = create_client(_supabase_url, _supabase_key)


# =============================================================================
# LOOKUP FUNCTIONS
# =============================================================================

def get_order_by_id(order_id: str):
    """
    Look up a single order by its order_id (e.g. 'ORD-10001').
    Returns the order as a dict if found, or None if not found.
    """
    result = (
        supabase
        .table("orders")
        .select("*")
        .eq("order_id", order_id.upper())
        .execute()
    )

    if not result.data:
        return None

    order = result.data[0]

    # items is stored as JSONB — parse it back into a Python list
    if order.get("items") and isinstance(order["items"], str):
        order["items"] = json.loads(order["items"])

    return order


def get_orders_by_customer_email(email: str):
    """
    Find all orders placed by a customer with the given email address.
    Returns a list of order dicts (empty list if none found).
    """
    result = (
        supabase
        .table("orders")
        .select("*")
        .ilike("customer_email", email)
        .execute()
    )

    orders = result.data if result.data else []

    for order in orders:
        if order.get("items") and isinstance(order["items"], str):
            order["items"] = json.loads(order["items"])

    return orders


def get_return_eligibility(order_id: str):
    """
    Check whether a specific order is eligible for a return.
    Returns the eligibility dict if found, or None if not found.
    """
    result = (
        supabase
        .table("return_eligibility")
        .select("*")
        .eq("order_id", order_id.upper())
        .execute()
    )

    if not result.data:
        return None

    return result.data[0]


def get_customer_by_email(email: str):
    """
    Look up a customer profile by email address.
    Returns the customer dict if found, or None if not found.
    """
    result = (
        supabase
        .table("customers")
        .select("*")
        .ilike("email", email)
        .execute()
    )

    if not result.data:
        return None

    return result.data[0]


def get_all_orders():
    """
    Return all orders in the database as a list of dicts.
    """
    result = (
        supabase
        .table("orders")
        .select("*")
        .execute()
    )

    orders = result.data if result.data else []

    for order in orders:
        if order.get("items") and isinstance(order["items"], str):
            order["items"] = json.loads(order["items"])

    return orders
