from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from .config import settings
from .db.base import Base
from .db.session import engine, SessionLocal, get_db
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
__all__ = ["Base", "engine", "SessionLocal", "get_db"]
