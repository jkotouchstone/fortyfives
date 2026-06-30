"""
Game persistence layer.

By default games are kept in an in-process dict (fine for local dev / a
single server). If a DATABASE_URL environment variable is present (Railway
sets this automatically when you add a Postgres database to a project),
games are instead persisted to Postgres so they survive deploys/restarts
and multiple workers can share state correctly.

Games are arbitrary Python objects (game_logic.Game), so they're serialized
with pickle and stored as bytes. This keeps the store fully decoupled from
the shape of Game/Card, so it doesn't need to change every time the game
logic does.
"""

import os
import pickle
import threading

DATABASE_URL = os.environ.get("DATABASE_URL")

_lock = threading.Lock()
_memory_store = {}

_engine = None
_metadata = None
_games_table = None

if DATABASE_URL:
    # Lazy/optional import so the app still runs with zero extra
    # dependencies when no database is configured.
    from sqlalchemy import create_engine, MetaData, Table, Column, String, LargeBinary, DateTime, func

    # Railway (and most providers) hand out a postgres:// URL; SQLAlchemy
    # with psycopg2 wants postgresql://.
    db_url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    _engine = create_engine(db_url, pool_pre_ping=True)
    _metadata = MetaData()
    _games_table = Table(
        "games",
        _metadata,
        Column("session_id", String, primary_key=True),
        Column("data", LargeBinary, nullable=False),
        Column("updated_at", DateTime(timezone=True), server_default=func.now(), onupdate=func.now()),
    )
    _metadata.create_all(_engine)


def save_game(session_id, game):
    blob = pickle.dumps(game)
    if _engine is not None:
        from sqlalchemy import insert
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        stmt = pg_insert(_games_table).values(session_id=session_id, data=blob)
        stmt = stmt.on_conflict_do_update(
            index_elements=["session_id"], set_={"data": blob}
        )
        with _engine.begin() as conn:
            conn.execute(stmt)
    else:
        with _lock:
            _memory_store[session_id] = blob


def load_game(session_id):
    if _engine is not None:
        from sqlalchemy import select

        with _engine.begin() as conn:
            row = conn.execute(
                select(_games_table.c.data).where(_games_table.c.session_id == session_id)
            ).fetchone()
        if row is None:
            return None
        return pickle.loads(row[0])
    else:
        with _lock:
            blob = _memory_store.get(session_id)
        return pickle.loads(blob) if blob else None


def delete_game(session_id):
    if _engine is not None:
        with _engine.begin() as conn:
            conn.execute(_games_table.delete().where(_games_table.c.session_id == session_id))
    else:
        with _lock:
            _memory_store.pop(session_id, None)
