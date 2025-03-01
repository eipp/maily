import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from services.document_generator import DocumentGenerator, DocumentGenerationError
from ai.tools.document_generator_tool import DocumentGeneratorTool


@pytest.fixture
def document_data():
    """Sample document data for testing."""
    return {
        "id": "doc_test123",
        "type": "pdf",
        "title": "Test Document",
        "template_id": None,
        "sections": [
            {
                "id": "sect_1",
                "title": "Introduction",
                "type": "text",
                "content": "This is a test document"
            }
        ],
        "user_id": "user_123",
        "campaign_id": None,
        "recipient_data": None,
        "blockchain_verify": False,
        "interactive_elements": None,
        "metadata": {"test": True}
    }


@pytest.fixture
def mock_docs_repo():
    """Mock document repository."""
    repo = AsyncMock()
    repo.create_document.return_value = "doc_test123"
    repo.get_document.return_value = {
        "id": "doc_test123",
        "status": "completed",
        "type": "pdf",
        "title": "Test Document",
        "file_url": "https://example.com/documents/doc_test123.pdf",
        "preview_url": "https://example.com/documents/previews/doc_test123.png",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    repo.update_document.return_value = True
    repo.get_template.return_value = None
    return repo


@pytest.mark.asyncio
async def test_document_generator_create_document(document_data, mock_docs_repo):
    """Test creating a document."""
    generator = DocumentGenerator(mock_docs_repo)

    # Mock internal methods
    generator._generate_document = AsyncMock()

    # Create document
    result = await generator.create_document(document_data)

    # Assertions
    assert result["id"] == document_data["id"]
    assert result["status"] == "pending"
    assert mock_docs_repo.create_document.called
    assert generator._generate_document.called


@pytest.mark.asyncio
async def test_document_generator_get_document(mock_docs_repo):
    """Test retrieving a document."""
    generator = DocumentGenerator(mock_docs_repo)

    # Get document
    result = await generator.get_document("doc_test123")

    # Assertions
    assert result["id"] == "doc_test123"
    assert result["status"] == "completed"
    assert mock_docs_repo.get_document.called


@pytest.mark.asyncio
async def test_document_generator_generate_document_success(document_data, mock_docs_repo):
    """Test document generation process."""
    generator = DocumentGenerator(mock_docs_repo)

    # Mock generation methods
    generator._generate_by_type = AsyncMock(return_value=("path/to/file.pdf", "url/to/file.pdf", "url/to/preview.png"))
    generator._process_sections = AsyncMock()
    generator._verify_document = AsyncMock(return_value=None)

    # Generate document
    await generator._generate_document(document_data["id"], document_data)

    # Assertions
    assert mock_docs_repo.update_document.called
    assert generator._generate_by_type.called
    assert generator._process_sections.called


@pytest.mark.asyncio
async def test_document_generator_generate_document_failure(document_data, mock_docs_repo):
    """Test document generation failure handling."""
    generator = DocumentGenerator(mock_docs_repo)

    # Mock generation methods to fail
    generator._generate_by_type = AsyncMock(side_effect=Exception("Generation failed"))

    # Generate document
    await generator._generate_document(document_data["id"], document_data)

    # Assertions
    mock_docs_repo.update_document.assert_called_with(
        document_data["id"],
        {"status": "failed", "metadata": {"error": "Generation failed"}}
    )


@pytest.mark.asyncio
async def test_document_generator_tool_run(document_data):
    """Test DocumentGeneratorTool async run method."""
    # Create tool
    tool = DocumentGeneratorTool()

    # Mock the generator
    tool.generator = AsyncMock()
    tool.generator.create_document.return_value = {
        "id": document_data["id"],
        "status": "pending",
        "created_at": datetime.utcnow().isoformat() + "Z"
    }

    # Run the tool
    result = await tool._arun(
        document_type=document_data["type"],
        title=document_data["title"],
        content={"sections": document_data["sections"]},
        metadata=document_data["metadata"]
    )

    # Assertions
    assert result["success"] is True
    assert result["document_id"] == document_data["id"]
    assert tool.generator.create_document.called


@pytest.mark.asyncio
async def test_document_generator_tool_error_handling():
    """Test DocumentGeneratorTool error handling."""
    # Create tool
    tool = DocumentGeneratorTool()

    # Mock the generator to fail
    tool.generator = AsyncMock()
    tool.generator.create_document.side_effect = Exception("Test error")

    # Run the tool
    result = await tool._arun(
        document_type="pdf",
        title="Test Document",
        content={"sections": []}
    )

    # Assertions
    assert result["success"] is False
    assert "error" in result
    assert result["message"] == "Document generation failed"
