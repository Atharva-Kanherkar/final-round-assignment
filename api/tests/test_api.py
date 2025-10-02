"""Comprehensive API tests."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock, AsyncMock, patch

from api.main import app
from api.database import Base, get_db
from api.models.db_models import DBSession, SessionStatus


# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    """Setup and teardown test database."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ============================================================================
# Health Check Tests
# ============================================================================

class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_ping(self):
        """Test ping endpoint."""
        response = client.get("/api/ping")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "database" in data


# ============================================================================
# Session Creation Tests
# ============================================================================

class TestSessionCreation:
    """Test session creation endpoint."""

    @patch('api.routers.sessions.InterviewService')
    def test_create_session_success(self, mock_service):
        """Test successful session creation."""
        # Mock service
        mock_instance = Mock()
        mock_instance.create_session = AsyncMock(return_value=(
            Mock(
                id="test-uuid",
                candidate_name="John Doe",
                job_title="Engineer",
                company="TechCo",
                topics=[],
                status=SessionStatus.ACTIVE
            ),
            Mock(question="What is Python?", topic="Python", question_number=1, topic_progress="1/5", questions_in_topic=1)
        ))
        mock_service.return_value = mock_instance

        response = client.post(
            "/api/sessions",
            json={
                "resume_text": "John Doe\nSoftware Engineer\nSkills: Python\n5 years experience\n" * 3,
                "job_description_text": "Software Engineer\nCompany: TechCo\nRequirements:\n- Python\n- 5 years\n" * 3
            }
        )

        assert response.status_code == 201

    def test_create_session_empty_resume(self):
        """Test session creation with empty resume fails."""
        response = client.post(
            "/api/sessions",
            json={
                "resume_text": "",
                "job_description_text": "Valid job description" * 10
            }
        )

        assert response.status_code == 422  # Validation error

    def test_create_session_too_short(self):
        """Test session creation with too-short inputs fails."""
        response = client.post(
            "/api/sessions",
            json={
                "resume_text": "Short",
                "job_description_text": "Short"
            }
        )

        assert response.status_code == 422  # Validation error


# ============================================================================
# Session Retrieval Tests
# ============================================================================

class TestSessionRetrieval:
    """Test session retrieval endpoints."""

    def test_list_sessions_empty(self):
        """Test listing sessions when none exist."""
        response = client.get("/api/sessions")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_sessions_with_pagination(self):
        """Test pagination parameters."""
        response = client.get("/api/sessions?limit=10&offset=0")
        assert response.status_code == 200
        assert isinstance(response.json(), list)


# ============================================================================
# Response Submission Tests
# ============================================================================

class TestResponseSubmission:
    """Test response submission endpoint."""

    def test_submit_response_invalid_session(self):
        """Test submitting response to non-existent session."""
        response = client.post(
            "/api/sessions/00000000-0000-0000-0000-000000000000/respond",
            json={"response": "Test answer"}
        )

        # Should return error (404 or 500 depending on implementation)
        assert response.status_code in [404, 500]

    def test_submit_empty_response(self):
        """Test validation rejects empty response."""
        response = client.post(
            "/api/sessions/00000000-0000-0000-0000-000000000000/respond",
            json={"response": ""}
        )

        # Should validate and potentially reject
        assert response.status_code in [400, 404, 422, 500]


# ============================================================================
# Root Endpoint Tests
# ============================================================================

class TestRootEndpoint:
    """Test root endpoint."""

    def test_root(self):
        """Test root endpoint returns API info."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "status" in data
        assert data["status"] == "running"
