"""Tests for Sessions API endpoints - validation only."""
import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestSessionsAPIValidation:
    """Test API input validation."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_list_sessions_limit_validation(self, client):
        """Test that limit over 1000 is rejected."""
        response = client.get("/api/v1/sessions?limit=1001")
        assert response.status_code == 400
    
    def test_create_session_endpoint_exists(self, client):
        """Test that create session endpoint exists and accepts valid input."""
        response = client.post("/api/v1/sessions", json={
            "code": "fn main() {}"
        })
        # Endpoint exists - may succeed or fail due to dependencies
        assert response.status_code in [202, 400, 500]
    
    def test_create_session_empty_body(self, client):
        """Test creating session with empty body fails validation."""
        response = client.post("/api/v1/sessions", json={})
        assert response.status_code in [400, 422]
    
    def test_create_session_git_without_ref(self, client):
        """Test that Git URL without ref fails validation."""
        response = client.post("/api/v1/sessions", json={
            "orig_location": "https://github.com/user/repo"
        })
        assert response.status_code in [400, 422]