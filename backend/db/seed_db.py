# =============================================================================
# backend/db/seed_db.py
# =============================================================================
# ONE-TIME SETUP SCRIPT — run this ONCE to:
#   1. Create the 'customers', 'orders', and 'return_eligibility' tables
#      in your Supabase PostgreSQL database
#   2. Insert realistic Indian eCommerce sample data into those tables
#
# HOW TO RUN:
#   Make sure your .env has SUPABASE_DB_URL filled in, then run:
#       python -m backend.db.seed_db
#
# WHY psycopg2 HERE (not supabase-py)?
#   Creating tables requires raw SQL commands like CREATE TABLE.
#   The supabase-py client only supports reading/writing rows — it cannot
#   create or modify tables. psycopg2 gives us a direct PostgreSQL
#   connection where we can run any SQL we want.
#
# SAFE TO RE-RUN:
#   All CREATE TABLE statements use "IF NOT EXISTS" — so running this
#   again won't crash or duplicate data. INSERT statements use
#   "ON CONFLICT DO NOTHING" for the same reason.
# =============================================================================

import os
import json
import psycopg2                 # Direct PostgreSQL driver — like a phone line to the database
from psycopg2.extras import RealDictCursor  # Returns rows as dicts instead of plain tuples
from dotenv import load_dotenv

# Load the .env file so os.getenv() can read our credentials
load_dotenv()


# =============================================================================
# DATABASE CONNECTION
# psycopg2.connect() opens a live connection to Supabase PostgreSQL.
# We use the full connection string from SUPABASE_DB_URL in .env.
# =============================================================================
def get_connection():
    """
    Create and return a psycopg2 connection to Supabase PostgreSQL.
    This is a direct, raw database connection — not through the REST API.
    """
    db_url = os.getenv("SUPABASE_DB_URL")
    if not db_url:
        raise ValueError(
            "SUPABASE_DB_URL is missing from your .env file. "
            "Find it in: Supabase Dashboard > Project Settings > Database > Connection string (URI format)"
        )
    return psycopg2.connect(db_url)


# =============================================================================
# TABLE DEFINITIONS (SQL)
# These SQL statements define the structure (schema) of each table.
# Think of a table like an Excel sheet:
#   - column name = column header
#   - data type = what kind of data is allowed (TEXT, INTEGER, BOOLEAN, etc.)
#   - PRIMARY KEY = the unique identifier for each row
#   - REFERENCES = a foreign key link (this column must match a row in another table)
# =============================================================================

CREATE_CUSTOMERS_TABLE = """
CREATE TABLE IF NOT EXISTS customers (
    customer_id     TEXT PRIMARY KEY,       -- e.g. "CUST-001"
    name            TEXT NOT NULL,
    email           TEXT UNIQUE NOT NULL,   -- UNIQUE = no two customers can share an email
    phone           TEXT,
    account_created DATE,
    loyalty_tier    TEXT,                   -- Bronze / Silver / Gold / Platinum
    total_orders    INTEGER DEFAULT 0
);
"""

CREATE_ORDERS_TABLE = """
CREATE TABLE IF NOT EXISTS orders (
    order_id            TEXT PRIMARY KEY,   -- e.g. "ORD-10001"
    customer_id         TEXT REFERENCES customers(customer_id),  -- links to customers table
    customer_name       TEXT,
    customer_email      TEXT,
    order_date          DATE,
    status              TEXT,               -- Processing / In Transit / Delivered / Cancelled / Out for Delivery
    items               JSONB,              -- JSONB = structured JSON stored in the database
    subtotal            NUMERIC(10, 2),     -- NUMERIC(10,2) = number with 2 decimal places (for money)
    shipping_cost       NUMERIC(10, 2),
    total               NUMERIC(10, 2),
    shipping_address    TEXT,
    tracking_number     TEXT,
    carrier             TEXT,
    tracking_url        TEXT,
    estimated_delivery  DATE,
    actual_delivery     DATE,
    payment_method      TEXT,
    cancellation_reason TEXT,
    refund_status       TEXT
);
"""

CREATE_RETURN_ELIGIBILITY_TABLE = """
CREATE TABLE IF NOT EXISTS return_eligibility (
    order_id                TEXT PRIMARY KEY REFERENCES orders(order_id),
    customer_name           TEXT,
    delivery_date           DATE,
    days_since_delivery     INTEGER,
    eligible                BOOLEAN,
    reason                  TEXT,
    return_window_days      INTEGER,
    condition_requirement   TEXT,
    refund_method           TEXT,
    refund_timeline         TEXT,
    return_label_available  BOOLEAN
);
"""


# =============================================================================
# SAMPLE DATA — Indian eCommerce customers and orders
# CartFlow is an Indian eCommerce platform.
#
# Products are Indian-market relevant (OnePlus, boAt, saree, cricket gear, etc.)
# Carriers are Indian logistics companies (Delhivery, BlueDart, Ekart, DTDC)
# Payment methods include UPI, Rupay, and popular Indian wallets
# Currency is INR (₹)
# =============================================================================

CUSTOMERS_DATA = [
    {
        "customer_id": "CUST-001",
        "name": "Arjun Sharma",
        "email": "arjun.sharma@gmail.com",
        "phone": "+91-98201-34567",
        "account_created": "2023-03-15",
        "loyalty_tier": "Gold",           # Frequent buyer
        "total_orders": 14,
    },
    {
        "customer_id": "CUST-002",
        "name": "Priya Nair",
        "email": "priya.nair@gmail.com",
        "phone": "+91-90112-78654",
        "account_created": "2024-01-08",
        "loyalty_tier": "Silver",
        "total_orders": 5,
    },
    {
        "customer_id": "CUST-003",
        "name": "Rahul Gupta",
        "email": "rahul.gupta@outlook.com",
        "phone": "+91-99304-22110",
        "account_created": "2022-11-20",
        "loyalty_tier": "Platinum",       # VIP — highest priority
        "total_orders": 31,
    },
    {
        "customer_id": "CUST-004",
        "name": "Sneha Patel",
        "email": "sneha.patel@yahoo.com",
        "phone": "+91-87405-66321",
        "account_created": "2025-07-01",
        "loyalty_tier": "Bronze",         # New customer
        "total_orders": 2,
    },
    {
        "customer_id": "CUST-005",
        "name": "Vikram Reddy",
        "email": "vikram.reddy@gmail.com",
        "phone": "+91-76506-99887",
        "account_created": "2023-09-12",
        "loyalty_tier": "Silver",
        "total_orders": 8,
    },
]

ORDERS_DATA = [
    {
        "order_id": "ORD-10001",
        "customer_id": "CUST-001",
        "customer_name": "Arjun Sharma",
        "customer_email": "arjun.sharma@gmail.com",
        "order_date": "2026-04-28",
        "status": "Delivered",
        # items stored as JSON list — JSONB in PostgreSQL can store this natively
        "items": json.dumps([
            {"product": "boAt Rockerz 550 Bluetooth Headphones", "qty": 1, "price": 1999.00},
            {"product": "OnePlus Type-C Warp Charge Cable",      "qty": 2, "price": 599.00},
        ]),
        "subtotal": 3197.00,
        "shipping_cost": 0.00,            # Free shipping — Gold tier
        "total": 3197.00,
        "shipping_address": "14B, Andheri West, Mumbai, Maharashtra 400053",
        "tracking_number": "DLVR2026042811234",
        "carrier": "Delhivery",
        "tracking_url": "https://www.delhivery.com/track/package/DLVR2026042811234",
        "estimated_delivery": "2026-05-03",
        "actual_delivery": "2026-05-02",   # Arrived one day early
        "payment_method": "UPI - GPay (arjun@oksbi)",
        "cancellation_reason": None,
        "refund_status": None,
    },
    {
        "order_id": "ORD-10002",
        "customer_id": "CUST-002",
        "customer_name": "Priya Nair",
        "customer_email": "priya.nair@gmail.com",
        "order_date": "2026-05-05",
        "status": "In Transit",
        "items": json.dumps([
            {"product": "Nike Air Max 270 Running Shoes (Size 6)", "qty": 1, "price": 8495.00},
            {"product": "Adidas Sports Socks (Pack of 3)",         "qty": 1, "price": 699.00},
        ]),
        "subtotal": 9194.00,
        "shipping_cost": 99.00,
        "total": 9293.00,
        "shipping_address": "Flat 3C, Koramangala 4th Block, Bengaluru, Karnataka 560034",
        "tracking_number": "BDAR2026050509876",
        "carrier": "BlueDart",
        "tracking_url": "https://www.bluedart.com/web/guest/trackyourshipment?trackFor=0&trackNo=BDAR2026050509876",
        "estimated_delivery": "2026-05-11",
        "actual_delivery": None,           # Still in transit
        "payment_method": "Rupay Credit Card - HDFC ending in 7823",
        "cancellation_reason": None,
        "refund_status": None,
    },
    {
        "order_id": "ORD-10003",
        "customer_id": "CUST-003",
        "customer_name": "Rahul Gupta",
        "customer_email": "rahul.gupta@outlook.com",
        "order_date": "2026-05-07",
        "status": "Processing",
        "items": json.dumps([
            {"product": "Samsung 55-inch 4K QLED Smart TV (UA55Q70C)", "qty": 1, "price": 54990.00},
            {"product": "AmazonBasics HDMI Cable 1.8m (Pack of 2)",    "qty": 1, "price": 499.00},
        ]),
        "subtotal": 55489.00,
        "shipping_cost": 0.00,             # Free shipping — Platinum tier
        "total": 55489.00,
        "shipping_address": "House No. 21, Sector 15, Dwarka, New Delhi 110078",
        "tracking_number": None,           # Not shipped yet
        "carrier": None,
        "tracking_url": None,
        "estimated_delivery": "2026-05-14",
        "actual_delivery": None,
        "payment_method": "Mastercard - ICICI Bank ending in 4401",
        "cancellation_reason": None,
        "refund_status": None,
    },
    {
        "order_id": "ORD-10004",
        "customer_id": "CUST-004",
        "customer_name": "Sneha Patel",
        "customer_email": "sneha.patel@yahoo.com",
        "order_date": "2026-04-20",
        "status": "Cancelled",
        "items": json.dumps([
            {"product": "Banarasi Silk Saree - Royal Blue", "qty": 1, "price": 4200.00},
        ]),
        "subtotal": 4200.00,
        "shipping_cost": 99.00,
        "total": 4299.00,
        "shipping_address": "12, Satellite Road, Ahmedabad, Gujarat 380015",
        "tracking_number": None,
        "carrier": None,
        "tracking_url": None,
        "estimated_delivery": None,        # Cancelled — no delivery
        "actual_delivery": None,
        "payment_method": "Paytm Wallet",
        "cancellation_reason": "Customer requested cancellation before dispatch",
        "refund_status": "Refund Issued",  # ₹4299 already returned to Paytm Wallet
    },
    {
        "order_id": "ORD-10005",
        "customer_id": "CUST-005",
        "customer_name": "Vikram Reddy",
        "customer_email": "vikram.reddy@gmail.com",
        "order_date": "2026-05-01",
        "status": "Out for Delivery",
        "items": json.dumps([
            {"product": "Boldfit Yoga Mat Anti-Slip 6mm",       "qty": 1, "price": 799.00},
            {"product": "Boldfit Resistance Bands Set (5 pcs)", "qty": 1, "price": 549.00},
            {"product": "Nalgene Wide-Mouth Water Bottle 1L",   "qty": 1, "price": 1299.00},
        ]),
        "subtotal": 2647.00,
        "shipping_cost": 0.00,             # Free — order above ₹500 threshold
        "total": 2647.00,
        "shipping_address": "Flat 7, Green Park Colony, Jubilee Hills, Hyderabad, Telangana 500033",
        "tracking_number": "EKRT2026050144321",
        "carrier": "Ekart Logistics",
        "tracking_url": "https://ekartlogistics.com/track/EKRT2026050144321",
        "estimated_delivery": "2026-05-09",
        "actual_delivery": None,           # Out for delivery today
        "payment_method": "UPI - PhonePe (vikram@ybl)",
        "cancellation_reason": None,
        "refund_status": None,
    },
]

RETURN_ELIGIBILITY_DATA = [
    {
        "order_id": "ORD-10001",
        "customer_name": "Arjun Sharma",
        "delivery_date": "2026-05-02",
        "days_since_delivery": 7,
        "eligible": True,
        "reason": "Within 30-day return window. Item is in original, sealed packaging.",
        "return_window_days": 30,
        "condition_requirement": "Original sealed packaging, all accessories included",
        "refund_method": "UPI - GPay (arjun@oksbi) — refund in 5-7 business days",
        "refund_timeline": "5-7 business days after return pickup",
        "return_label_available": True,
    },
    {
        "order_id": "ORD-10002",
        "customer_name": "Priya Nair",
        "delivery_date": None,
        "days_since_delivery": None,
        "eligible": False,
        "reason": "Order has not been delivered yet. You can request a return only after the item is delivered to you.",
        "return_window_days": 30,
        "condition_requirement": "Original packaging, unworn, tags intact",
        "refund_method": "Rupay Credit Card - HDFC ending in 7823",
        "refund_timeline": "5-7 business days after return pickup",
        "return_label_available": False,
    },
    {
        "order_id": "ORD-10003",
        "customer_name": "Rahul Gupta",
        "delivery_date": None,
        "days_since_delivery": None,
        "eligible": False,
        "reason": "Order is currently being processed and has not shipped yet. Returns can only be initiated after delivery.",
        "return_window_days": 30,
        "condition_requirement": "Original packaging, undamaged, all accessories included",
        "refund_method": "Mastercard - ICICI Bank ending in 4401",
        "refund_timeline": "5-7 business days after return pickup",
        "return_label_available": False,
    },
    {
        "order_id": "ORD-10004",
        "customer_name": "Sneha Patel",
        "delivery_date": None,
        "days_since_delivery": None,
        "eligible": False,
        "reason": "This order was cancelled before dispatch. A full refund of Rs. 4299 has already been credited back to your Paytm Wallet.",
        "return_window_days": None,
        "condition_requirement": None,
        "refund_method": "Paytm Wallet",
        "refund_timeline": "Already processed",
        "return_label_available": False,
    },
    {
        "order_id": "ORD-10005",
        "customer_name": "Vikram Reddy",
        "delivery_date": "2026-05-09",
        "days_since_delivery": 0,
        "eligible": True,
        "reason": "Delivered today. You are within the 30-day return window.",
        "return_window_days": 30,
        "condition_requirement": "Original packaging, unused, all tags attached",
        "refund_method": "UPI - PhonePe (vikram@ybl)",
        "refund_timeline": "5-7 business days after return pickup",
        "return_label_available": True,
    },
]


# =============================================================================
# MAIN SEEDING FUNCTION
# This creates tables and inserts all the sample data above.
# =============================================================================
def seed():
    """
    Connect to Supabase PostgreSQL, create tables, and insert sample data.
    Safe to run multiple times — uses IF NOT EXISTS and ON CONFLICT DO NOTHING.
    """
    print("Connecting to Supabase PostgreSQL...")
    conn = get_connection()

    # cursor = the "pen" you use to write SQL queries to the database
    # Using RealDictCursor so any SELECT results come back as dicts
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # ----------------------------------------------------------
    # STEP 1 — Create tables
    # ----------------------------------------------------------
    print("Creating tables...")
    cursor.execute(CREATE_CUSTOMERS_TABLE)
    cursor.execute(CREATE_ORDERS_TABLE)
    cursor.execute(CREATE_RETURN_ELIGIBILITY_TABLE)
    conn.commit()  # commit() = save the changes permanently
    print("  Tables created (or already existed).")

    # ----------------------------------------------------------
    # STEP 2 — Insert customers
    # ON CONFLICT (customer_id) DO NOTHING means:
    #   "If a row with this customer_id already exists, skip it."
    # This makes the script safe to re-run.
    # ----------------------------------------------------------
    print("Inserting customers...")
    for c in CUSTOMERS_DATA:
        cursor.execute("""
            INSERT INTO customers (customer_id, name, email, phone, account_created, loyalty_tier, total_orders)
            VALUES (%(customer_id)s, %(name)s, %(email)s, %(phone)s, %(account_created)s, %(loyalty_tier)s, %(total_orders)s)
            ON CONFLICT (customer_id) DO NOTHING
        """, c)
    conn.commit()
    print(f"  {len(CUSTOMERS_DATA)} customers inserted.")

    # ----------------------------------------------------------
    # STEP 3 — Insert orders
    # %(key)s is a safe parameterized placeholder — psycopg2
    # replaces it with the actual value from the dict.
    # This prevents SQL injection attacks.
    # ----------------------------------------------------------
    print("Inserting orders...")
    for o in ORDERS_DATA:
        cursor.execute("""
            INSERT INTO orders (
                order_id, customer_id, customer_name, customer_email,
                order_date, status, items, subtotal, shipping_cost, total,
                shipping_address, tracking_number, carrier, tracking_url,
                estimated_delivery, actual_delivery, payment_method,
                cancellation_reason, refund_status
            ) VALUES (
                %(order_id)s, %(customer_id)s, %(customer_name)s, %(customer_email)s,
                %(order_date)s, %(status)s, %(items)s, %(subtotal)s, %(shipping_cost)s, %(total)s,
                %(shipping_address)s, %(tracking_number)s, %(carrier)s, %(tracking_url)s,
                %(estimated_delivery)s, %(actual_delivery)s, %(payment_method)s,
                %(cancellation_reason)s, %(refund_status)s
            )
            ON CONFLICT (order_id) DO NOTHING
        """, o)
    conn.commit()
    print(f"  {len(ORDERS_DATA)} orders inserted.")

    # ----------------------------------------------------------
    # STEP 4 — Insert return eligibility records
    # ----------------------------------------------------------
    print("Inserting return eligibility records...")
    for r in RETURN_ELIGIBILITY_DATA:
        cursor.execute("""
            INSERT INTO return_eligibility (
                order_id, customer_name, delivery_date, days_since_delivery,
                eligible, reason, return_window_days, condition_requirement,
                refund_method, refund_timeline, return_label_available
            ) VALUES (
                %(order_id)s, %(customer_name)s, %(delivery_date)s, %(days_since_delivery)s,
                %(eligible)s, %(reason)s, %(return_window_days)s, %(condition_requirement)s,
                %(refund_method)s, %(refund_timeline)s, %(return_label_available)s
            )
            ON CONFLICT (order_id) DO NOTHING
        """, r)
    conn.commit()
    print(f"  {len(RETURN_ELIGIBILITY_DATA)} return records inserted.")

    # ----------------------------------------------------------
    # STEP 5 — Close the connection (good housekeeping)
    # ----------------------------------------------------------
    cursor.close()
    conn.close()
    print("\nDatabase seeding complete! Your Supabase tables are ready.")


# =============================================================================
# ENTRY POINT
# "if __name__ == '__main__'" means:
#   "Only run this block if this file is run directly (not imported)."
# So you can safely import this file without triggering the seed.
# =============================================================================
if __name__ == "__main__":
    seed()
