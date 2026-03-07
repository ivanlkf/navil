# Copyright (c) 2026 Pantheon Lab Limited
# Licensed under the Business Source License 1.1 (see LICENSE.cloud)
"""Database engine and session management for Navil Cloud.

Connection
----------
Set ``DATABASE_URL`` to a SQLAlchemy-compatible connection string:

- **Development**: ``sqlite:///navil.db`` (default when unset)
- **Production**: ``postgresql://user:pass@host/navil``

Usage::

    from navil.cloud.database import get_session, init_db

    init_db()                # create tables on startup
    with get_session() as s: # scoped session
        s.add(Event(...))
"""

from __future__ import annotations

import logging
import os
from collections.abc import Generator
from contextlib import contextmanager

logger = logging.getLogger(__name__)

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///navil.db")

_engine = None
_SessionFactory = None


def _get_engine():  # type: ignore[no-untyped-def]
    """Lazy-create the SQLAlchemy engine."""
    global _engine
    if _engine is None:
        from sqlalchemy import create_engine

        connect_args = {}
        if DATABASE_URL.startswith("sqlite"):
            connect_args["check_same_thread"] = False
        _engine = create_engine(
            DATABASE_URL,
            echo=False,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
    return _engine


def _get_session_factory():  # type: ignore[no-untyped-def]
    """Lazy-create the session factory."""
    global _SessionFactory
    if _SessionFactory is None:
        from sqlalchemy.orm import sessionmaker

        _SessionFactory = sessionmaker(bind=_get_engine(), expire_on_commit=False)
    return _SessionFactory


def init_db() -> None:
    """Create all tables if they don't exist.

    Safe to call multiple times — ``create_all`` is idempotent.
    For production schema migrations, use Alembic (see ``migrations/``).
    """
    from navil.cloud.models import Base

    engine = _get_engine()
    Base.metadata.create_all(engine)
    logger.info("Database tables ensured (url=%s)", DATABASE_URL.split("@")[-1])


@contextmanager
def get_session() -> Generator:
    """Yield a scoped SQLAlchemy session that auto-commits on success.

    Usage::

        with get_session() as session:
            session.add(Event(...))
            # auto-committed here
    """
    factory = _get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def reset_engine() -> None:
    """Dispose of the engine and session factory.  Used in tests."""
    global _engine, _SessionFactory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _SessionFactory = None
