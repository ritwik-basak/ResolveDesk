import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from psycopg_pool import AsyncConnectionPool
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

load_dotenv()

DB_URL = os.getenv("SUPABASE_DB_URL")


# =============================================================================
# get_checkpointer — async context manager
#
# WHY AN ASYNC CONTEXT MANAGER?
#   The connection pool must be opened before use and closed when the app
#   shuts down. An async context manager (async with) handles this cleanly —
#   the pool opens on entry and closes on exit, even if an error occurs.
#
# WHY AsyncConnectionPool AND NOT A SINGLE CONNECTION?
#   A connection pool keeps several database connections open and ready.
#   When multiple users send messages at the same time, each request gets
#   its own connection from the pool instead of waiting. This is what makes
#   the app handle concurrent users correctly.
#
# autocommit=True:
#   Required by LangGraph's checkpointer. Without this, writes would be
#   held in a transaction until explicitly committed, which breaks LangGraph's
#   internal checkpoint mechanism.
#
# prepare_threshold=0:
#   Disables prepared statements. Required for compatibility with Supabase's
#   connection pooler (PgBouncer), which doesn't support prepared statements
#   in transaction pooling mode.
# =============================================================================

@asynccontextmanager
async def get_checkpointer():
    """
    Async context manager that yields a ready-to-use AsyncPostgresSaver.

    Usage:
        async with get_checkpointer() as checkpointer:
            graph = build_graph(checkpointer)
    """
    async with AsyncConnectionPool(
        conninfo=DB_URL,
        max_size=10,
        kwargs={
            "autocommit":        True,
            "prepare_threshold": None,
        },
    ) as pool:
        checkpointer = AsyncPostgresSaver(pool)

        # setup() creates LangGraph's internal tables in Supabase if they
        # don't exist yet. Safe to call every time — uses IF NOT EXISTS.
        await checkpointer.setup()

        yield checkpointer
