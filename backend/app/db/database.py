from sqlalchemy import text
from app.db.base import Base
from app.db.session import SessionLocal, engine


def test_connection():
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
        return "Database connection successful!"
