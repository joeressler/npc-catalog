import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure /workspace/backend is on sys.path so `app` is importable when running
# pytest from that directory (or any subdirectory).
_BACKEND_ROOT = str(Path(__file__).parent.parent)
if _BACKEND_ROOT not in sys.path:
    sys.path.insert(0, _BACKEND_ROOT)


@pytest.fixture()
def client(tmp_path):
    """
    Provide a TestClient backed by a fresh, isolated SQLite database.

    The FastAPI dependency `get_db` is overridden so every test operates on its
    own temp DB, with all tables created via SQLAlchemy metadata and dropped on
    teardown.  The media root (set at app-import time) is left as the real
    default; no media is uploaded in these tests so that's fine.
    """
    db_path = tmp_path / "test.sqlite3"

    # app.main imports all routers → all models are registered with Base
    from app.main import app
    from app.deps import get_db
    from app.database import Base

    test_engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    TestingSessionLocal = sessionmaker(bind=test_engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()
    Base.metadata.drop_all(test_engine)
    test_engine.dispose()
