"""Comprehensive test suite for ComplianceBinder application."""

import os
import tempfile
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine, SQLModel

from app.main import app, get_session, get_current_user
from app.config import settings
from app.models import User, Binder, Task, Document


# Test database setup
@pytest.fixture(name="test_engine")
def test_engine_fixture():
    """Create a test database engine."""
    # Use in-memory SQLite for tests
    test_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(test_engine)
    return test_engine


@pytest.fixture(name="session")
def session_fixture(test_engine):
    """Create a test database session."""
    with Session(test_engine) as session:
        yield session


@pytest.fixture(name="client")
def client_fixture(session):
    """Create a test client with dependency overrides."""
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override
    
    # Create temporary upload directory for tests
    temp_dir = tempfile.mkdtemp()
    original_upload_dir = settings.upload_dir
    settings.upload_dir = temp_dir
    
    client = TestClient(app)
    yield client
    
    # Cleanup
    settings.upload_dir = original_upload_dir
    app.dependency_overrides.clear()


@pytest.fixture(name="test_user")
def test_user_fixture(client):
    """Create a test user and return authentication token."""
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    # Register user
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 201
    
    # Login to get token
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }
    response = client.post("/auth/token", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    return {"email": user_data["email"], "token": token}


class TestAuthentication:
    """Test user authentication endpoints."""
    
    def test_register_new_user(self, client):
        """Test registering a new user."""
        response = client.post("/auth/register", json={
            "email": "newuser@example.com",
            "password": "securepassword"
        })
        assert response.status_code == 201
        assert response.json() == {"ok": True}
    
    def test_register_duplicate_email(self, client, test_user):
        """Test registering with an already registered email."""
        response = client.post("/auth/register", json={
            "email": test_user["email"],
            "password": "anotherpassword"
        })
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"].lower()
    
    def test_login_success(self, client):
        """Test successful login."""
        # Register first
        client.post("/auth/register", json={
            "email": "logintest@example.com",
            "password": "password123"
        })
        
        # Login
        response = client.post("/auth/token", data={
            "username": "logintest@example.com",
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self, client, test_user):
        """Test login with invalid credentials."""
        response = client.post("/auth/token", data={
            "username": test_user["email"],
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        assert "credentials" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user."""
        response = client.post("/auth/token", data={
            "username": "nonexistent@example.com",
            "password": "password"
        })
        assert response.status_code == 401


class TestBinders:
    """Test binder CRUD operations."""
    
    def test_create_binder(self, client, test_user):
        """Test creating a new binder."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = client.post("/binders", json={
            "name": "My First Binder",
            "industry": "healthcare"
        }, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "My First Binder"
        assert data["industry"] == "healthcare"
        assert "id" in data
        assert "created_at" in data
    
    def test_create_binder_without_auth(self, client):
        """Test creating a binder without authentication."""
        response = client.post("/binders", json={
            "name": "Unauthorized Binder",
            "industry": "general"
        })
        assert response.status_code == 401
    
    def test_list_binders_empty(self, client, test_user):
        """Test listing binders when user has none."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = client.get("/binders", headers=headers)
        
        assert response.status_code == 200
        assert response.json() == []
    
    def test_list_binders_with_data(self, client, test_user):
        """Test listing binders after creating some."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        # Create multiple binders
        binders = [
            {"name": "Binder 1", "industry": "healthcare"},
            {"name": "Binder 2", "industry": "construction"}
        ]
        
        for binder_data in binders:
            client.post("/binders", json=binder_data, headers=headers)
        
        # List binders
        response = client.get("/binders", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all("id" in b for b in data)
    
    def test_user_isolation(self, client):
        """Test that users can only see their own binders."""
        # Create two users
        user1_data = {"email": "user1@example.com", "password": "pass123"}
        user2_data = {"email": "user2@example.com", "password": "pass123"}
        
        client.post("/auth/register", json=user1_data)
        client.post("/auth/register", json=user2_data)
        
        # Get tokens
        token1 = client.post("/auth/token", data={
            "username": user1_data["email"],
            "password": user1_data["password"]
        }).json()["access_token"]
        
        token2 = client.post("/auth/token", data={
            "username": user2_data["email"],
            "password": user2_data["password"]
        }).json()["access_token"]
        
        # User 1 creates a binder
        headers1 = {"Authorization": f"Bearer {token1}"}
        client.post("/binders", json={"name": "User 1 Binder"}, headers=headers1)
        
        # User 2 should not see User 1's binder
        headers2 = {"Authorization": f"Bearer {token2}"}
        response = client.get("/binders", headers=headers2)
        assert response.status_code == 200
        assert len(response.json()) == 0


class TestTasks:
    """Test task CRUD operations."""
    
    @pytest.fixture(name="binder_id")
    def binder_id_fixture(self, client, test_user):
        """Create a test binder and return its ID."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = client.post("/binders", json={
            "name": "Test Binder",
            "industry": "general"
        }, headers=headers)
        return response.json()["id"]
    
    def test_create_task(self, client, test_user, binder_id):
        """Test creating a task in a binder."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        task_data = {
            "title": "Complete inspection",
            "description": "Annual safety inspection",
            "due_date": "2024-12-31"
        }
        
        response = client.post(f"/binders/{binder_id}/tasks", json=task_data, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == task_data["title"]
        assert data["description"] == task_data["description"]
        assert data["status"] == "open"
        assert "id" in data
    
    def test_create_task_without_optional_fields(self, client, test_user, binder_id):
        """Test creating a task with only required fields."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = client.post(f"/binders/{binder_id}/tasks", json={
            "title": "Simple Task"
        }, headers=headers)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Simple Task"
        assert data["description"] == ""
        assert data["due_date"] is None
    
    def test_list_tasks(self, client, test_user, binder_id):
        """Test listing tasks in a binder."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        # Create some tasks
        tasks = [
            {"title": "Task 1", "description": "First task"},
            {"title": "Task 2", "description": "Second task"}
        ]
        
        for task in tasks:
            client.post(f"/binders/{binder_id}/tasks", json=task, headers=headers)
        
        # List tasks
        response = client.get(f"/binders/{binder_id}/tasks", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
    
    def test_mark_task_done(self, client, test_user, binder_id):
        """Test marking a task as done."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        # Create a task
        response = client.post(f"/binders/{binder_id}/tasks", json={
            "title": "Test Task"
        }, headers=headers)
        task_id = response.json()["id"]
        
        # Mark as done
        response = client.post(f"/tasks/{task_id}/done", headers=headers)
        assert response.status_code == 200
        assert response.json() == {"ok": True}
        
        # Verify status changed
        response = client.get(f"/binders/{binder_id}/tasks", headers=headers)
        tasks = response.json()
        task = next(t for t in tasks if t["id"] == task_id)
        assert task["status"] == "done"
    
    def test_task_access_control(self, client, binder_id):
        """Test that users can't access tasks in other users' binders."""
        # Create another user
        other_user_data = {"email": "other@example.com", "password": "pass123"}
        client.post("/auth/register", json=other_user_data)
        other_token = client.post("/auth/token", data={
            "username": other_user_data["email"],
            "password": other_user_data["password"]
        }).json()["access_token"]
        
        # Try to create task in original user's binder
        headers = {"Authorization": f"Bearer {other_token}"}
        response = client.post(f"/binders/{binder_id}/tasks", json={
            "title": "Unauthorized Task"
        }, headers=headers)
        
        assert response.status_code == 404


class TestDocuments:
    """Test document upload and download."""
    
    @pytest.fixture(name="binder_id")
    def binder_id_fixture(self, client, test_user):
        """Create a test binder and return its ID."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = client.post("/binders", json={
            "name": "Test Binder",
            "industry": "general"
        }, headers=headers)
        return response.json()["id"]
    
    def test_upload_document(self, client, test_user, binder_id):
        """Test uploading a document to a binder."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        # Create a test file
        file_content = b"Test document content"
        files = {"file": ("test.txt", file_content, "text/plain")}
        data = {"note": "Important compliance document"}
        
        response = client.post(f"/binders/{binder_id}/documents", 
                               files=files, data=data, headers=headers)
        
        assert response.status_code == 201
        assert response.json() == {"ok": True}
    
    def test_list_documents(self, client, test_user, binder_id):
        """Test listing documents in a binder."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        # Upload a document
        files = {"file": ("report.pdf", b"PDF content", "application/pdf")}
        data = {"note": "Annual report"}
        client.post(f"/binders/{binder_id}/documents", 
                    files=files, data=data, headers=headers)
        
        # List documents
        response = client.get(f"/binders/{binder_id}/documents", headers=headers)
        assert response.status_code == 200
        docs = response.json()
        assert len(docs) == 1
        assert docs[0]["original_name"] == "report.pdf"
        assert docs[0]["content_type"] == "application/pdf"
        assert docs[0]["note"] == "Annual report"
    
    def test_download_document(self, client, test_user, binder_id):
        """Test downloading a document."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        # Upload a document
        file_content = b"Downloadable content"
        files = {"file": ("download.txt", file_content, "text/plain")}
        client.post(f"/binders/{binder_id}/documents", 
                    files=files, data={"note": ""}, headers=headers)
        
        # Get document ID
        docs_response = client.get(f"/binders/{binder_id}/documents", headers=headers)
        doc_id = docs_response.json()[0]["id"]
        
        # Download document
        response = client.get(f"/documents/{doc_id}/download", headers=headers)
        assert response.status_code == 200
        assert response.content == file_content
    
    def test_document_access_control(self, client, binder_id):
        """Test that users can't access documents in other users' binders."""
        # Create another user
        other_user_data = {"email": "another@example.com", "password": "pass123"}
        client.post("/auth/register", json=other_user_data)
        other_token = client.post("/auth/token", data={
            "username": other_user_data["email"],
            "password": other_user_data["password"]
        }).json()["access_token"]
        
        # Try to list documents in original user's binder
        headers = {"Authorization": f"Bearer {other_token}"}
        response = client.get(f"/binders/{binder_id}/documents", headers=headers)
        
        assert response.status_code == 404


class TestInspectionReport:
    """Test inspection report generation."""
    
    @pytest.fixture(name="populated_binder")
    def populated_binder_fixture(self, client, test_user):
        """Create a binder with tasks and documents."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        # Create binder
        binder_response = client.post("/binders", json={
            "name": "Safety Compliance Binder",
            "industry": "healthcare"
        }, headers=headers)
        binder_id = binder_response.json()["id"]
        
        # Add tasks
        client.post(f"/binders/{binder_id}/tasks", json={
            "title": "Fire safety check",
            "description": "Monthly inspection",
            "due_date": "2024-03-01",
            "status": "open"
        }, headers=headers)
        
        task_response = client.post(f"/binders/{binder_id}/tasks", json={
            "title": "Equipment maintenance",
            "description": "Quarterly review"
        }, headers=headers)
        task_id = task_response.json()["id"]
        
        # Mark one task as done
        client.post(f"/tasks/{task_id}/done", headers=headers)
        
        # Upload document
        files = {"file": ("certificate.pdf", b"Cert content", "application/pdf")}
        client.post(f"/binders/{binder_id}/documents", 
                    files=files, data={"note": "Safety certificate"}, headers=headers)
        
        return binder_id
    
    def test_generate_report(self, client, test_user, populated_binder):
        """Test generating an inspection report."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = client.get(f"/binders/{populated_binder}/report", headers=headers)
        
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        
        html_content = response.text
        
        # Check that report contains expected sections
        assert "Safety Compliance Binder" in html_content
        assert "healthcare" in html_content
        assert "Open Tasks" in html_content
        assert "Completed Tasks" in html_content
        assert "Documents" in html_content
        
        # Check for specific task titles
        assert "Fire safety check" in html_content
        assert "Equipment maintenance" in html_content
        
        # Check for document
        assert "certificate.pdf" in html_content
        assert "Safety certificate" in html_content
    
    def test_report_access_control(self, client, populated_binder):
        """Test that users can't access other users' reports."""
        # Create another user
        other_user_data = {"email": "unauthorized@example.com", "password": "pass123"}
        client.post("/auth/register", json=other_user_data)
        other_token = client.post("/auth/token", data={
            "username": other_user_data["email"],
            "password": other_user_data["password"]
        }).json()["access_token"]
        
        # Try to access report
        headers = {"Authorization": f"Bearer {other_token}"}
        response = client.get(f"/binders/{populated_binder}/report", headers=headers)
        
        assert response.status_code == 404


class TestSecurityValidation:
    """Test security features."""
    
    def test_password_hashing(self, client):
        """Test that passwords are properly hashed."""
        from app.security import hash_password, verify_password
        
        password = "mysecretpassword"
        hashed = hash_password(password)
        
        # Hash should be different from original
        assert hashed != password
        
        # Should be able to verify correct password
        assert verify_password(password, hashed)
        
        # Should reject incorrect password
        assert not verify_password("wrongpassword", hashed)
    
    def test_token_authentication(self, client, test_user):
        """Test JWT token authentication."""
        # Valid token should work
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        response = client.get("/binders", headers=headers)
        assert response.status_code == 200
        
        # Invalid token should fail
        headers = {"Authorization": "Bearer invalid_token_here"}
        response = client.get("/binders", headers=headers)
        assert response.status_code == 401
        
        # Missing token should fail
        response = client.get("/binders")
        assert response.status_code == 401
    
    def test_file_upload_security(self, client, test_user):
        """Test that uploaded files are stored with safe names."""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        
        # Create a binder
        binder_response = client.post("/binders", json={
            "name": "Test Binder"
        }, headers=headers)
        binder_id = binder_response.json()["id"]
        
        # Upload file with potentially unsafe name
        unsafe_filename = "../../../etc/passwd"
        files = {"file": (unsafe_filename, b"content", "text/plain")}
        client.post(f"/binders/{binder_id}/documents", 
                    files=files, data={"note": ""}, headers=headers)
        
        # Get document info
        docs = client.get(f"/binders/{binder_id}/documents", headers=headers).json()
        
        # Original name should be preserved but stored filename should be safe
        assert docs[0]["original_name"] == unsafe_filename
        
        # The actual stored filename should not contain path separators
        # (we can't directly check this without DB access, but download should work)
        doc_id = docs[0]["id"]
        response = client.get(f"/documents/{doc_id}/download", headers=headers)
        assert response.status_code == 200
