"""
Test script to verify Phase 1 setup
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

print("=" * 60)
print("Phase 1: Foundation & Setup - Verification")
print("=" * 60)
print()

# Test 1: Configuration Loading
print("✓ Test 1: Configuration Loading")
try:
    from config.settings import settings
    print(f"  ✅ Settings loaded successfully")
    print(f"  • App Name: {settings.APP_NAME}")
    print(f"  • API Port: {settings.API_PORT}")
    print(f"  • Frontend Port: {settings.FRONTEND_PORT}")
    print(f"  • Database: {settings.DATABASE_URL}")
    print(f"  • Default Symbols: {settings.DEFAULT_SYMBOLS}")
except Exception as e:
    print(f"  ❌ Failed to load settings: {e}")
    sys.exit(1)

print()

# Test 2: Database Models
print("✓ Test 2: Database Models")
try:
    from backend.storage.models import (
        TickData, OHLC, AnalyticsCache, 
        Alert, AlertHistory, UploadedData
    )
    print(f"  ✅ All models imported successfully")
    print(f"  • TickData: {TickData.__tablename__}")
    print(f"  • OHLC: {OHLC.__tablename__}")
    print(f"  • AnalyticsCache: {AnalyticsCache.__tablename__}")
    print(f"  • Alert: {Alert.__tablename__}")
    print(f"  • AlertHistory: {AlertHistory.__tablename__}")
    print(f"  • UploadedData: {UploadedData.__tablename__}")
except Exception as e:
    print(f"  ❌ Failed to import models: {e}")
    sys.exit(1)

print()

# Test 3: Database Initialization
print("✓ Test 3: Database Initialization")
try:
    from backend.storage.database import init_db, engine
    init_db()
    print(f"  ✅ Database initialized successfully")
    
    # Check if tables were created
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"  • Tables created: {len(tables)}")
    for table in tables:
        print(f"    - {table}")
except Exception as e:
    print(f"  ❌ Failed to initialize database: {e}")
    sys.exit(1)

print()

# Test 4: Directory Structure
print("✓ Test 4: Directory Structure")
required_dirs = [
    "backend",
    "backend/ingestion",
    "backend/storage",
    "backend/analytics",
    "backend/api",
    "backend/alerts",
    "frontend",
    "frontend/components",
    "frontend/utils",
    "config",
    "docs",
    "tests",
    "logs",
    "exports"
]

missing_dirs = []
for dir_path in required_dirs:
    full_path = project_root / dir_path
    if full_path.exists():
        print(f"  ✅ {dir_path}")
    else:
        print(f"  ❌ {dir_path} - MISSING")
        missing_dirs.append(dir_path)

if missing_dirs:
    print(f"\n  ⚠️  {len(missing_dirs)} directories missing")
else:
    print(f"\n  ✅ All directories present")

print()

# Test 5: Required Files
print("✓ Test 5: Required Files")
required_files = [
    "requirements.txt",
    "README.md",
    "run.py",
    ".env",
    ".gitignore",
    "config/settings.py",
    "backend/storage/models.py",
    "backend/storage/database.py",
    "docs/chatgpt_usage.md",
    "docs/architecture.txt"
]

missing_files = []
for file_path in required_files:
    full_path = project_root / file_path
    if full_path.exists():
        print(f"  ✅ {file_path}")
    else:
        print(f"  ❌ {file_path} - MISSING")
        missing_files.append(file_path)

if missing_files:
    print(f"\n  ⚠️  {len(missing_files)} files missing")
else:
    print(f"\n  ✅ All files present")

print()
print("=" * 60)
print("Phase 1 Verification Complete!")
print("=" * 60)
print()

if missing_dirs or missing_files:
    print("⚠️  Some components are missing. Please review above.")
    sys.exit(1)
else:
    print("✅ Phase 1 setup is complete and verified!")
    print()
    print("Next Steps:")
    print("1. Install dependencies: pip install -r requirements.txt")
    print("2. Proceed to Phase 2: Data Ingestion Pipeline")
    print()
