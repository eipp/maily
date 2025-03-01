"""Integration tests for MailyDocs API endpoints."""

import pytest
from fastapi.testclient import TestClient
import json
from unittest.mock import patch, AsyncMock, MagicMock

from main import app
from db.documents import DocumentsRepository


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_current_user():
    """Mock current user for authentication."""
    return {
        "id": "user_test123",
        "email": "test@example.com",
        "is_admin": False
    }


@pytest.fixture
def mock_documents_repo():
    """Mock documents repository."""
    repo = AsyncMock(spec=DocumentsRepository)

    # Setup return values
    repo.create_document.return_value = "doc_test123"
    repo.get_document.return_value = {
        "id": "doc_test123",
        "status": "completed",
        "type": "pdf",
        "title": "Test Document",
        "file_url": "https://example.com/documents/doc_test123.pdf",
        "preview_url": "https://example.com/documents/previews/doc_test123.png",
        "personalized": False,
        "interactive": False,
        "blockchain_verified": False,
        "created_at": "2023-12-01T12:00:00Z",
        "metadata": {"test": True}
    }

    repo.get_document_analytics.return_value = {
        "document_id": "doc_test123",
        "views": 10,
        "unique_views": 5,
        "average_view_time": 120.5,
        "completion_rate": 0.75,
        "engagement_by_section": {"sect_1": 0.8},
        "created_at": "2023-12-01T12:00:00Z",
        "updated_at": "2023-12-01T14:00:00Z"
    }

    repo.list_templates.return_value = [
        {
            "id": "tmpl_test123",
            "name": "Test Template",
            "type": "pdf",
            "description": "A test template"
        }
    ]

    repo.delete_document.return_value = True

    return repo


@pytest.mark.parametrize("auth", [True, False])
def test_create_document_auth(client, auth, mock_documents_repo, mock_current_user):
    """Test document creation endpoint authentication."""
    # Setup document data
    document_data = {
        "type": "pdf",
        "title": "Test Document",
        "sections": [
            {
                "id": "sect_1",
                "title": "Introduction",
                "type": "text",
                "content": "This is a test document"
            }
        ],
        "blockchain_verify": False
    }

    # Setup authentication
    headers = {}
    if auth:
        headers["Authorization"] = "Bearer valid_token"

    # Mock dependencies
    with patch("endpoints.mailydocs.get_current_user", return_value=mock_current_user if auth else None):
        with patch("endpoints.mailydocs.DocumentsRepository", return_value=mock_documents_repo):
            with patch("endpoints.mailydocs.DocumentGenerator"):
                # Make request
                response = client.post(
                    "/api/mailydocs/documents",
                    json=document_data,
                    headers=headers
                )

    # Assertions
    if auth:
        assert response.status_code == 200
        assert response.json()["id"] is not None
        assert response.json()["status"] == "pending"
    else:
        assert response.status_code == 401


def test_get_document(client, mock_documents_repo, mock_current_user):
    """Test retrieving a document."""
    # Mock dependencies
    with patch("endpoints.mailydocs.get_current_user", return_value=mock_current_user):
        with patch("endpoints.mailydocs.DocumentsRepository", return_value=mock_documents_repo):
            # Make request
            response = client.get(
                "/api/mailydocs/documents/doc_test123",
                headers={"Authorization": "Bearer valid_token"}
            )

    # Assertions
    assert response.status_code == 200
    assert response.json()["id"] == "doc_test123"
    assert response.json()["title"] == "Test Document"


def test_get_document_not_found(client, mock_documents_repo, mock_current_user):
    """Test retrieving a non-existent document."""
    # Mock repository to return None
    mock_documents_repo.get_document.return_value = None

    # Mock dependencies
    with patch("endpoints.mailydocs.get_current_user", return_value=mock_current_user):
        with patch("endpoints.mailydocs.DocumentsRepository", return_value=mock_documents_repo):
            # Make request
            response = client.get(
                "/api/mailydocs/documents/doc_nonexistent",
                headers={"Authorization": "Bearer valid_token"}
            )

    # Assertions
    assert response.status_code == 404


def test_get_document_unauthorized(client, mock_documents_repo, mock_current_user):
    """Test retrieving a document with incorrect owner."""
    # Change document owner
    document = mock_documents_repo.get_document.return_value
    document["user_id"] = "another_user"

    # Mock dependencies
    with patch("endpoints.mailydocs.get_current_user", return_value=mock_current_user):
        with patch("endpoints.mailydocs.DocumentsRepository", return_value=mock_documents_repo):
            # Make request
            response = client.get(
                "/api/mailydocs/documents/doc_test123",
                headers={"Authorization": "Bearer valid_token"}
            )

    # Assertions
    assert response.status_code == 403


def test_get_document_analytics(client, mock_documents_repo, mock_current_user):
    """Test retrieving document analytics."""
    # Mock dependencies
    with patch("endpoints.mailydocs.get_current_user", return_value=mock_current_user):
        with patch("endpoints.mailydocs.DocumentsRepository", return_value=mock_documents_repo):
            # Make request
            response = client.get(
                "/api/mailydocs/documents/doc_test123/analytics",
                headers={"Authorization": "Bearer valid_token"}
            )

    # Assertions
    assert response.status_code == 200
    assert response.json()["document_id"] == "doc_test123"
    assert response.json()["views"] == 10
    assert response.json()["unique_views"] == 5


def test_list_templates(client, mock_documents_repo, mock_current_user):
    """Test listing document templates."""
    # Mock dependencies
    with patch("endpoints.mailydocs.get_current_user", return_value=mock_current_user):
        with patch("endpoints.mailydocs.DocumentsRepository", return_value=mock_documents_repo):
            # Make request
            response = client.get(
                "/api/mailydocs/templates",
                headers={"Authorization": "Bearer valid_token"}
            )

    # Assertions
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == "tmpl_test123"
    assert response.json()[0]["name"] == "Test Template"


def test_delete_document(client, mock_documents_repo, mock_current_user):
    """Test deleting a document."""
    # Set document owner
    document = mock_documents_repo.get_document.return_value
    document["user_id"] = mock_current_user["id"]

    # Mock dependencies
    with patch("endpoints.mailydocs.get_current_user", return_value=mock_current_user):
        with patch("endpoints.mailydocs.DocumentsRepository", return_value=mock_documents_repo):
            # Make request
            response = client.delete(
                "/api/mailydocs/documents/doc_test123",
                headers={"Authorization": "Bearer valid_token"}
            )

    # Assertions
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert mock_documents_repo.delete_document.called


def test_document_verification(client, mock_documents_repo, mock_current_user):
    """Test document blockchain verification."""
    # Setup document with verification info
    document = mock_documents_repo.get_document.return_value
    document["blockchain_verified"] = True
    document["verification_info"] = {
        "hash": "0x1234567890abcdef",
        "timestamp": "2023-12-01T12:30:00Z",
        "block_number": 12345
    }
    document["verification_url"] = "https://etherscan.io/tx/0x1234567890abcdef"

    # Mock dependencies
    with patch("endpoints.mailydocs.get_current_user", return_value=mock_current_user):
        with patch("endpoints.mailydocs.DocumentsRepository", return_value=mock_documents_repo):
            # Make request
            response = client.post(
                "/api/mailydocs/documents/doc_test123/verify",
                headers={"Authorization": "Bearer valid_token"}
            )

    # Assertions
    assert response.status_code == 200
    assert response.json()["verified"] is True
    assert "verification_info" in response.json()
