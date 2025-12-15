"""
Fix database schema by recreating alert tables
"""
import os
from sqlalchemy import text
from backend.storage.database import engine, SessionLocal
from backend.alerts.alert_storage import Base, AlertRule, AlertHistory

print("=" * 70)
print("Fixing Alert Database Schema")
print("=" * 70)
print()

# Create a session
session = SessionLocal()

try:
    # Drop existing alert tables
    print("Dropping old alert tables...")
    session.execute(text("DROP TABLE IF EXISTS alert_history"))
    session.execute(text("DROP TABLE IF EXISTS alert_rules"))
    session.commit()
    print("  ✓ Old tables dropped")
    print()

    # Recreate tables with correct schema
    print("Creating new alert tables...")
    Base.metadata.create_all(engine, tables=[AlertRule.__table__, AlertHistory.__table__])
    print("  ✓ New tables created")
    print()

    print("=" * 70)
    print("✅ Database schema fixed!")
    print("=" * 70)
    print()
    print("Restart the API server to apply changes:")
    print("  python -m uvicorn backend.api.app:app --reload")
    print()

except Exception as e:
    print(f"❌ Error: {e}")
    session.rollback()
finally:
    session.close()
