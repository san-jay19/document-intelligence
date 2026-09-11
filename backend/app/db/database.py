import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# =========================================================
# Environment
# =========================================================

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not configured in the environment."
    )


# =========================================================
# SQLAlchemy Engine
# =========================================================

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)


# =========================================================
# Session
# =========================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# =========================================================
# Base Model
# =========================================================

Base = declarative_base()


# =========================================================
# Database Session
# =========================================================

def get_db():
    """
    Provide a database session.
    """

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


# =========================================================
# Initialize Database
# =========================================================

def init_db():
    """
    Create all database tables.
    """

    # Import models before create_all so SQLAlchemy
    # knows about the tables.
    from backend.app.db.models import Document

    Base.metadata.create_all(
        bind=engine
    )