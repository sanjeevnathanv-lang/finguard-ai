from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.db.models import Base

# Configure SQLite engine with check_same_thread=False for multithreading
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    echo=False,
)

# Enforce foreign key constraints on SQLite connections
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    except Exception:
        pass

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db() -> None:
    """Initialize database tables, execute safe column migrations, and bootstrap initial users."""
    from app.db.migrations import run_migrations
    from app.services.user_service import seed_default_users_if_empty
    Base.metadata.create_all(bind=engine)
    run_migrations(engine=engine)
    with SessionLocal() as db:
        seed_default_users_if_empty(db)

def get_db() -> Generator[Session, None, None]:
    """Dependency that yields a SQLAlchemy session and ensures cleanup."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
