from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from fir_system.app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


def get_db():
    """FastAPI dependency — yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables if they don't exist."""
    from fir_system.app import models  # noqa: F401  — registers models with Base
    Base.metadata.create_all(bind=engine)
