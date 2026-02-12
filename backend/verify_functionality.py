#!/usr/bin/env python3
"""
Simple integration test script to verify ComplianceBinder functionality.
Tests all major features by making actual API calls.
"""

import requests
import json
import tempfile
import time
from datetime import date

BASE_URL = "http://localhost:8000"

def test_app():
    """Run comprehensive tests on the running application."""
    
    print("=" * 70)
    print("ComplianceBinder Functionality Verification")
    print("=" * 70)
    
    # Track test results
    tests_passed = 0
    tests_failed = 0
    
    def test_step(name, func):
        """Run a test step and track results."""
        nonlocal tests_passed, tests_failed
        print(f"\n[TEST] {name}...")
        try:
            func()
            print(f"[PASS] ✓ {name}")
            tests_passed += 1
            return True
        except AssertionError as e:
            print(f"[FAIL] ✗ {name}: {e}")
            tests_failed += 1
            return False
        except Exception as e:
            print(f"[ERROR] ✗ {name}: {e}")
            tests_failed += 1
            return False
    
    # Test 1: Homepage/Static files
    def test_homepage():
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert "ComplianceBinder" in response.text, "Homepage doesn't contain expected content"
    
    test_step("Homepage loads successfully", test_homepage)
    
    # Test 2: User Registration
    email = f"test_{int(time.time())}@example.com"
    password = "SecurePassword123"
    token = None
    
    def test_register():
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={"email": email, "password": password}
        )
        assert response.status_code == 201, f"Registration failed: {response.text}"
        assert response.json() == {"ok": True}, "Unexpected registration response"
    
    test_step("User registration", test_register)
    
    # Test 3: User Login
    def test_login():
        nonlocal token
        response = requests.post(
            f"{BASE_URL}/auth/token",
            data={"username": email, "password": password}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access token in response"
        assert data["token_type"] == "bearer", "Unexpected token type"
        token = data["access_token"]
    
    test_step("User login", test_login)
    
    # Test 4: Duplicate registration fails
    def test_duplicate_registration():
        response = requests.post(
            f"{BASE_URL}/auth/register",
            json={"email": email, "password": password}
        )
        assert response.status_code == 400, "Duplicate registration should fail"
        assert "already registered" in response.text.lower(), "Unexpected error message"
    
    test_step("Duplicate registration prevention", test_duplicate_registration)
    
    # Test 5: Invalid login fails
    def test_invalid_login():
        response = requests.post(
            f"{BASE_URL}/auth/token",
            data={"username": email, "password": "WrongPassword"}
        )
        assert response.status_code == 401, "Invalid login should fail with 401"
    
    test_step("Invalid login rejection", test_invalid_login)
    
    # Test 6: Unauthorized access
    def test_unauthorized():
        response = requests.get(f"{BASE_URL}/binders")
        assert response.status_code == 401, "Unauthorized request should fail"
    
    test_step("Unauthorized access prevention", test_unauthorized)
    
    headers = {"Authorization": f"Bearer {token}"}
    binder_id = None
    
    # Test 7: List binders (empty)
    def test_list_binders_empty():
        response = requests.get(f"{BASE_URL}/binders", headers=headers)
        assert response.status_code == 200, f"Failed to list binders: {response.text}"
        assert response.json() == [], "New user should have no binders"
    
    test_step("List empty binders", test_list_binders_empty)
    
    # Test 8: Create binder
    def test_create_binder():
        nonlocal binder_id
        response = requests.post(
            f"{BASE_URL}/binders",
            json={"name": "Safety Compliance Binder", "industry": "healthcare"},
            headers=headers
        )
        assert response.status_code == 201, f"Failed to create binder: {response.text}"
        data = response.json()
        assert data["name"] == "Safety Compliance Binder", "Binder name mismatch"
        assert data["industry"] == "healthcare", "Binder industry mismatch"
        assert "id" in data, "No binder ID returned"
        binder_id = data["id"]
    
    test_step("Create binder", test_create_binder)
    
    # Test 9: List binders (with data)
    def test_list_binders_with_data():
        response = requests.get(f"{BASE_URL}/binders", headers=headers)
        assert response.status_code == 200, f"Failed to list binders: {response.text}"
        binders = response.json()
        assert len(binders) == 1, f"Expected 1 binder, got {len(binders)}"
        assert binders[0]["id"] == binder_id, "Binder ID mismatch"
    
    test_step("List binders with data", test_list_binders_with_data)
    
    task_id = None
    
    # Test 10: Create task
    def test_create_task():
        nonlocal task_id
        response = requests.post(
            f"{BASE_URL}/binders/{binder_id}/tasks",
            json={
                "title": "Fire safety inspection",
                "description": "Monthly fire safety check",
                "due_date": "2024-12-31"
            },
            headers=headers
        )
        assert response.status_code == 201, f"Failed to create task: {response.text}"
        data = response.json()
        assert data["title"] == "Fire safety inspection", "Task title mismatch"
        assert data["status"] == "open", "Task should be open by default"
        assert "id" in data, "No task ID returned"
        task_id = data["id"]
    
    test_step("Create task", test_create_task)
    
    # Test 11: List tasks
    def test_list_tasks():
        response = requests.get(f"{BASE_URL}/binders/{binder_id}/tasks", headers=headers)
        assert response.status_code == 200, f"Failed to list tasks: {response.text}"
        tasks = response.json()
        assert len(tasks) == 1, f"Expected 1 task, got {len(tasks)}"
        assert tasks[0]["id"] == task_id, "Task ID mismatch"
    
    test_step("List tasks", test_list_tasks)
    
    # Test 12: Mark task as done
    def test_mark_task_done():
        response = requests.post(f"{BASE_URL}/tasks/{task_id}/done", headers=headers)
        assert response.status_code == 200, f"Failed to mark task done: {response.text}"
        assert response.json() == {"ok": True}, "Unexpected response"
        
        # Verify status changed
        response = requests.get(f"{BASE_URL}/binders/{binder_id}/tasks", headers=headers)
        tasks = response.json()
        assert tasks[0]["status"] == "done", "Task status didn't change to done"
    
    test_step("Mark task as done", test_mark_task_done)
    
    doc_id = None
    
    # Test 13: Upload document
    def test_upload_document():
        nonlocal doc_id
        files = {"file": ("test_certificate.pdf", b"PDF content here", "application/pdf")}
        data = {"note": "Annual safety certificate"}
        response = requests.post(
            f"{BASE_URL}/binders/{binder_id}/documents",
            files=files,
            data=data,
            headers=headers
        )
        assert response.status_code == 201, f"Failed to upload document: {response.text}"
        assert response.json() == {"ok": True}, "Unexpected response"
    
    test_step("Upload document", test_upload_document)
    
    # Test 14: List documents
    def test_list_documents():
        nonlocal doc_id
        response = requests.get(f"{BASE_URL}/binders/{binder_id}/documents", headers=headers)
        assert response.status_code == 200, f"Failed to list documents: {response.text}"
        docs = response.json()
        assert len(docs) == 1, f"Expected 1 document, got {len(docs)}"
        assert docs[0]["original_name"] == "test_certificate.pdf", "Document name mismatch"
        assert docs[0]["note"] == "Annual safety certificate", "Document note mismatch"
        doc_id = docs[0]["id"]
    
    test_step("List documents", test_list_documents)
    
    # Test 15: Download document
    def test_download_document():
        response = requests.get(f"{BASE_URL}/documents/{doc_id}/download", headers=headers)
        assert response.status_code == 200, f"Failed to download document: {response.text}"
        assert response.content == b"PDF content here", "Downloaded content mismatch"
    
    test_step("Download document", test_download_document)
    
    # Test 16: Generate inspection report
    def test_generate_report():
        response = requests.get(f"{BASE_URL}/binders/{binder_id}/report", headers=headers)
        assert response.status_code == 200, f"Failed to generate report: {response.text}"
        assert "text/html" in response.headers.get("content-type", ""), "Report should be HTML"
        
        html = response.text
        # Check report contains expected elements
        assert "Safety Compliance Binder" in html, "Report missing binder name"
        assert "healthcare" in html, "Report missing industry"
        assert "Fire safety inspection" in html, "Report missing task"
        assert "test_certificate.pdf" in html, "Report missing document"
        assert "Completed Tasks" in html, "Report missing completed section"
        assert "Open Tasks" in html, "Report missing open tasks section"
    
    test_step("Generate inspection report", test_generate_report)
    
    # Test 17: Authorization - other user can't access binder
    def test_authorization():
        # Create another user
        other_email = f"other_{int(time.time())}@example.com"
        requests.post(
            f"{BASE_URL}/auth/register",
            json={"email": other_email, "password": "pass123"}
        )
        
        # Login as other user
        response = requests.post(
            f"{BASE_URL}/auth/token",
            data={"username": other_email, "password": "pass123"}
        )
        other_token = response.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}
        
        # Try to access original user's binder
        response = requests.get(f"{BASE_URL}/binders/{binder_id}/tasks", headers=other_headers)
        assert response.status_code == 404, "Other user shouldn't access another user's binder"
    
    test_step("Authorization enforcement", test_authorization)
    
    # Print summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"✓ Passed: {tests_passed}")
    print(f"✗ Failed: {tests_failed}")
    print(f"Total:   {tests_passed + tests_failed}")
    print("=" * 70)
    
    if tests_failed == 0:
        print("\n🎉 All tests passed! ComplianceBinder is functioning as intended.")
        return 0
    else:
        print(f"\n⚠️  {tests_failed} test(s) failed. Please review the failures above.")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(test_app())
