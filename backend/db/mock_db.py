# =============================================================================
# This file has been renamed to db.py
# =============================================================================
# Import everything from the new location so any accidental import of
# mock_db still works without crashing.
#
# Always use: from backend.db.db import get_order_by_id
# Not:        from backend.db.mock_db import get_order_by_id
# =============================================================================

from backend.db.db import (
    get_order_by_id,
    get_orders_by_customer_email,
    get_return_eligibility,
    get_customer_by_email,
    get_all_orders,
)
