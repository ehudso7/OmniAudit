"""
Database initialization script.

Creates tables and sets up TimescaleDB hypertables.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.omniaudit.db.base import engine, Base
from src.omniaudit.db.models import Project, Audit, Metric, Alert
from sqlalchemy import text


def init_database():
    """Initialize database with tables and TimescaleDB."""
    print("Creating database tables...")

    # Create all tables
    Base.metadata.create_all(bind=engine)

    print("✓ Tables created")

    # Setup TimescaleDB hypertable for metrics
    try:
        with engine.connect() as conn:
            # Check if TimescaleDB extension exists
            result = conn.execute(text(
                "SELECT * FROM pg_extension WHERE extname = 'timescaledb'"
            ))

            if result.fetchone() is None:
                print("Installing TimescaleDB extension...")
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
                conn.commit()

            # Convert metrics table to hypertable
            print("Converting metrics table to hypertable...")
            conn.execute(text(
                "SELECT create_hypertable('metrics', 'timestamp', "
                "if_not_exists => TRUE)"
            ))
            conn.commit()

            print("✓ TimescaleDB hypertable created")

    except Exception as e:
        print(f"Warning: TimescaleDB setup failed: {e}")
        print("Continuing with regular PostgreSQL table...")

    print("\n✓ Database initialization complete!")


if __name__ == "__main__":
    init_database()
