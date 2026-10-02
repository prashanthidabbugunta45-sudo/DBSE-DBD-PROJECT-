import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv
import pymysql
from sqlalchemy import create_engine

load_dotenv(Path(__file__).with_name(".env"))

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "healthcare_appointment_db")

# URL-encode the password so special chars like @ don't break the URL
encoded_password = quote_plus(DB_PASSWORD)

# SQLAlchemy engine manages the connection pool; PyMySQL is the DBAPI driver.
engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{encoded_password}@{DB_HOST}/{DB_NAME}",
    pool_pre_ping=True,
    pool_recycle=280,
)


class _CompatConnection:
    """Wraps a SQLAlchemy-pooled DBAPI connection with the mysql-connector
    cursor interface (`cursor(dictionary=True)`) so existing repository code
    in models.py does not need to change."""

    def __init__(self, raw_connection):
        self._raw = raw_connection

    def cursor(self, dictionary=False):
        cursor_class = pymysql.cursors.DictCursor if dictionary else None
        return self._raw.cursor(cursor_class) if cursor_class else self._raw.cursor()

    def commit(self):
        self._raw.commit()

    def rollback(self):
        self._raw.rollback()

    def close(self):
        self._raw.close()


def get_connection():
    """Check out a pooled MySQL connection (via SQLAlchemy) for one repository operation."""
    return _CompatConnection(engine.raw_connection())


def get_db():
    db = get_connection()
    try:
        yield db
    finally:
        db.close()