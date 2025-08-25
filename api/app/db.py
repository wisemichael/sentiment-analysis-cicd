from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from .config import DATABASE_URL

# Engine & session factory
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def init_db():
    """Create the predictions table if it doesn't exist."""
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS predictions (
                id SERIAL PRIMARY KEY,
                input_text TEXT NOT NULL,
                predicted_label TEXT NOT NULL,
                probability DOUBLE PRECISION,
                latency_ms DOUBLE PRECISION,
                model_version TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                feedback BOOLEAN
            );
        """))
        conn.commit()
