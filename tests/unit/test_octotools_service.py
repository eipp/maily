import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
import json
import os

# Import the OctoTools service
from apps.api.octotools_integration.octotools_service import OctoToolsService


class TestOctoToolsService(unittest.TestCase):
    """Test cases for the OctoToolsService class."""

    def setUp(self):
        """Set up test fixtures."""
        # Mock the environment variables
        self.env_patcher = patch.dict(os.environ, {
            "OCTOTOOLS_API_URL": "http://test-octotools-api.com/api",
            "OCTOTOOLS_API_KEY": "test-octotools-key"
        })
        self.env_patcher.start()

        # Mock the httpx.AsyncClient
        self.client_patcher = patch('httpx.AsyncClient')
        self.mock_client_class = self.client_patcher.start()
        self.mock_client = MagicMock()
        self.mock_client_class.return_value = self.mock_client

        # Configure the mock client
        self.mock_client.post = AsyncMock()
        self.mock_client.get = AsyncMock()
        self.mock_client.aclose = AsyncMock()

        # Create an OctoToolsService instance
        self.octotools_service = OctoToolsService()

    def tearDown(self):
        """Tear down test fixtures."""
        self.env_patcher.stop()
        self.client_patcher.stop()

    @pytest.mark.asyncio
    async def test_register_tool(self):
        """Test registering a tool."""
        # Configure the mock client to return a success response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "tool_id": "test-tool-id"
        }
        self.mock_client.post.return_value = mock_response

        # Call the method
        result = await self.octotools_service.register_tool(
            user_id="test-user",
            tool_name="test-tool",
            description="Test tool description",
            parameters={"param1": "string", "param2": "number", "param3": "boolean?"},
            platform="test-platform"
        )

        # Verify the result
        self.assertTrue(result["success"])
        self.assertEqual(result["tool_id"], "test-tool-id")

        # Verify the client was called correctly
        self.mock_client.post.assert_called_once()
        call_args = self.mock_client.post.call_args
        self.assertEqual(call_args[0][0], "/tools/register")

        # Verify the payload
        payload = call_args[1]["json"]
        self.assertEqual(payload["user_id"], "test-user")
        self.assertEqual(payload["tool_name"], "test-tool")
        self.assertEqual(payload["description"], "Test tool description")

        # Verify the parameters were formatted correctly
        parameters = payload["parameters"]
        self.assertEqual(len(parameters), 3)

        # Check param1
        param1 = next(p for p in parameters if p["name"] == "param1")
        self.assertEqual(param1["type"], "string")
        self.assertTrue(param1["required"])

        # Check param2
        param2 = next(p for p in parameters if p["name"] == "param2")
        self.assertEqual(param2["type"], "number")
        self.assertTrue(param2["required"])

        # Check param3
        param3 = next(p for p in parameters if p["name"] == "param3")
        self.assertEqual(param3["type"], "boolean")
        self.assertFalse(param3["required"])

    @pytest.mark.asyncio
    async def test_register_tool_error(self):
        """Test registering a tool with an error response."""
        # Configure the mock client to return an error response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Error registering tool"
        self.mock_client.post.return_value = mock_response

        # Call the method
        result = await self.octotools_service.register_tool(
            user_id="test-user",
            tool_name="test-tool",
            description="Test tool description",
            parameters={"param1": "string"},
            platform="test-platform"
        )

        # Verify the result
        self.assertFalse(result["success"])
        self.assertIn("Error registering tool", result["error"])

    @pytest.mark.asyncio
    async def test_register_tool_exception(self):
        """Test registering a tool with an exception."""
        # Configure the mock client to raise an exception
        self.mock_client.post.side_effect = Exception("Test exception")

        # Call the method
        result = await self.octotools_service.register_tool(
            user_id="test-user",
            tool_name="test-tool",
            description="Test tool description",
            parameters={"param1": "string"},
            platform="test-platform"
        )

        # Verify the result
        self.assertFalse(result["success"])
        self.assertIn("Test exception", result["error"])

    @pytest.mark.asyncio
    async def test_deregister_tool(self):
        """Test deregistering a tool."""
        # Configure the mock client to return a success response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True
        }
        self.mock_client.post.return_value = mock_response

        # Call the method
        result = await self.octotools_service.deregister_tool(
            user_id="test-user",
            tool_name="test-tool"
        )

        # Verify the result
        self.assertTrue(result["success"])

        # Verify the client was called correctly
        self.mock_client.post.assert_called_once()
        call_args = self.mock_client.post.call_args
        self.assertEqual(call_args[0][0], "/tools/deregister")

        # Verify the payload
        payload = call_args[1]["json"]
        self.assertEqual(payload["user_id"], "test-user")
        self.assertEqual(payload["tool_name"], "test-tool")

    @pytest.mark.asyncio
    async def test_invoke_tool(self):
        """Test invoking a tool."""
        # Configure the mock client to return a success response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "result": {
                "data": "Tool invocation result"
            }
        }
        self.mock_client.post.return_value = mock_response

        # Call the method
        result = await self.octotools_service.invoke_tool(
            user_id="test-user",
            tool_name="test-tool",
            parameters={"param1": "value1"}
        )

        # Verify the result
        self.assertTrue(result["success"])
        self.assertEqual(result["result"]["data"], "Tool invocation result")

        # Verify the client was called correctly
        self.mock_client.post.assert_called_once()
        call_args = self.mock_client.post.call_args
        self.assertEqual(call_args[0][0], "/tools/invoke")

        # Verify the payload
        payload = call_args[1]["json"]
        self.assertEqual(payload["user_id"], "test-user")
        self.assertEqual(payload["tool_name"], "test-tool")
        self.assertEqual(payload["parameters"]["param1"], "value1")

    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test listing tools."""
        # Configure the mock client to return a success response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "tools": [
                {
                    "tool_id": "tool1",
                    "tool_name": "Tool 1",
                    "description": "Tool 1 description"
                },
                {
                    "tool_id": "tool2",
                    "tool_name": "Tool 2",
                    "description": "Tool 2 description"
                }
            ]
        }
        self.mock_client.get.return_value = mock_response

        # Call the method
        result = await self.octotools_service.list_tools("test-user")

        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["tool_id"], "tool1")
        self.assertEqual(result[1]["tool_id"], "tool2")

        # Verify the client was called correctly
        self.mock_client.get.assert_called_once()
        call_args = self.mock_client.get.call_args
        self.assertEqual(call_args[0][0], "/tools/list/test-user")

    @pytest.mark.asyncio
    async def test_list_tools_error(self):
        """Test listing tools with an error response."""
        # Configure the mock client to return an error response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Error listing tools"
        self.mock_client.get.return_value = mock_response

        # Call the method
        result = await self.octotools_service.list_tools("test-user")

        # Verify the result is an empty list
        self.assertEqual(result, [])

    @pytest.mark.asyncio
    async def test_close(self):
        """Test closing the client."""
        # Call the method
        await self.octotools_service.close()

        # Verify the client was closed
        self.mock_client.aclose.assert_called_once()
