from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL - using SQLite for simplicity
# On Vercel (or any read-only env), we must use /tmp
if os.getenv("VERCEL") or not os.access(".", os.W_OK):
    print("Environment is read-only or VERCEL detected. Using /tmp for SQLite.")
    default_db_url = "sqlite:////tmp/documents.db"
else:
    default_db_url = "sqlite:///./documents.db"

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", default_db_url)
if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Connect args needed for SQLite
connect_args = {"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}

try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args=connect_args
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    print(f"Database initialized with URL: {SQLALCHEMY_DATABASE_URL}")
except Exception as e:
    print(f"Failed to initialize database engine: {e}. Falling back to in-memory.")
    engine = create_engine(
        "sqlite:///:memory:", connect_args=connect_args
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

