import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.db.models import Base, User
from app.db.session import get_db
from app.core.deps import get_current_user
from app.main import app

# Use in-memory SQLite with StaticPool so all sessions share the in-memory database
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    """Create a fresh isolated session and clean tables between tests."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture
def test_analyst_user():
    return User(
        id=101,
        username="test_analyst",
        email="analyst@test.local",
        password_hash="test_hash",
        role="ANALYST",
        is_active=True,
    )

@pytest.fixture
def test_admin_user():
    return User(
        id=102,
        username="test_admin",
        email="admin@test.local",
        password_hash="test_hash",
        role="ADMIN",
        is_active=True,
    )

@pytest.fixture
def test_viewer_user():
    return User(
        id=103,
        username="test_viewer",
        email="viewer@test.local",
        password_hash="test_hash",
        role="VIEWER",
        is_active=True,
    )

@pytest.fixture
def client(db_session, test_analyst_user):
    """Override get_db and default get_current_user (Analyst) for backward-compatible regression tests."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_user():
        return test_analyst_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def unauthenticated_client(db_session):
    """Client without user authentication (tests 401 Unauthorized)."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    # Do NOT override get_current_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def viewer_client(db_session, test_viewer_user):
    """Client authenticated with VIEWER permissions (tests 403 Forbidden on writes)."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_user():
        return test_viewer_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def admin_client(db_session, test_admin_user):
    """Client authenticated with ADMIN permissions."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    def override_get_current_user():
        return test_admin_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
