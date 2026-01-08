from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL - using SQLite for simplicity
# On Vercel, we must use /tmp directory for SQLite if not using a real DB
if os.getenv("VERCEL"):
    default_db_url = "sqlite:///tmp/documents.db"
else:
    default_db_url = "sqlite:///./documents.db"

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", default_db_url)

# Connect args needed for SQLite
connect_args = {"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args=connect_args
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

