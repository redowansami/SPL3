"""SQLAlchemy engine/session setup for the auth module (Postgres via DATABASE_URL)."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from backend.app.core.config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True) if DATABASE_URL else None
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    if engine is None:
        print("[auth] DATABASE_URL is not set; skipping table creation.")
        return
    from backend.app.db import models  # noqa: F401 - registers models on Base before create_all

    try:
        Base.metadata.create_all(bind=engine)
    except Exception as exc:  # pragma: no cover - startup diagnostics only
        print(f"[auth] Could not connect to the database ({exc}). "
              "Auth endpoints will fail until DATABASE_URL in backend/.env is correct.")


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
