import sys
import os
from pathlib import Path
import pytest_asyncio

# Ensure project root is always present on sys.path regardless of execution context
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from backend.db.database import init_db

@pytest_asyncio.fixture(autouse=True)
async def setup_test_db():
    await init_db()
