"""Tests for AI & ML components."""

import os
import sys
import unittest
import asyncio
from unittest.mock import patch, MagicMock

# Add the parent directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the AI & ML components
from ai.wandb_integration import wandb_registry
from ai.dvc_integration import dvc_versioning
from ai.arize_integration import arize_observability
from ai.anthropic_integration import enhanced_claude_service
from ai.stability_integration import stability_ai_service
from ai.helicone_integration import helicone_service
from ai.litellm_integration import litellm_service
from ai.service_integration import enhanced_ai_service


class TestWandbIntegration(unittest.TestCase):
    """Tests for Weights & Biases integration."""

    def setUp(self):
        """Set up the test case."""
        # Mock the wandb module
        self.wandb_mock = MagicMock()
        self.wandb_patcher = patch('ai.wandb_integration.wandb', self.wandb_mock)
        self.wandb_patcher.start()

        # Set up a test instance with a mock API key
        self.wandb_registry = wandb_registry
        self.wandb_registry.api_key = "test_api_key"
        self.wandb_registry.enabled = True

    def tearDown(self):
        """Tear down the test case."""
        self.wandb_patcher.stop()

    def test_log_model_usage(self):
        """Test logging model usage."""
        # Set up the mock
        self.wandb_mock.init.return_value.id = "test_run_id"

        # Call the method
        result = self.wandb_registry.log_model_usage(
            model_name="test_model",
            provider="test_provider",
            prompt="test_prompt",
            response="test_response",
            metadata={"test_key": "test_value"}
        )

        # Check the result
        self.assertEqual(result, "test_run_id")

        # Check that wandb.init was called with the correct arguments
        self.wandb_mock.init.assert_called_once()
        _, kwargs = self.wandb_mock.init.call_args
        self.assertEqual(kwargs["project"], "maily-ai")
        self.assertEqual(kwargs["job_type"], "inference")
        self.assertEqual(kwargs["config"]["model_name"], "test_model")
        self.assertEqual(kwargs["config"]["provider"], "test_provider")
        self.assertEqual(kwargs["config"]["test_key"], "test_value")

        # Check that wandb.log was called with the correct arguments
        self.wandb_mock.log.assert_called_once()
        args, _ = self.wandb_mock.log.call_args
        self.assertEqual(args[0]["prompt"], "test_prompt")
        self.assertEqual(args[0]["response"], "test_response")

        # Check that wandb.finish was called
        self.wandb_mock.init.return_value.finish.assert_called_once()


class TestDVCIntegration(unittest.TestCase):
    """Tests for DVC integration."""

    def setUp(self):
        """Set up the test case."""
        # Mock the subprocess module
        self.subprocess_mock = MagicMock()
        self.subprocess_patcher = patch('ai.dvc_integration.subprocess', self.subprocess_mock)
        self.subprocess_patcher.start()

        # Mock the os module
        self.os_mock = MagicMock()
        self.os_patcher = patch('ai.dvc_integration.os', self.os_mock)
        self.os_patcher.start()

        # Set up a test instance
        self.dvc_versioning = dvc_versioning
        self.dvc_versioning.enabled = True

    def tearDown(self):
        """Tear down the test case."""
        self.subprocess_patcher.stop()
        self.os_patcher.stop()

    def test_add_model(self):
        """Test adding a model."""
        # Set up the mocks
        self.os_mock.path.join.return_value = "test_path"
        self.os_mock.makedirs.return_value = None

        # Mock the open function
        open_mock = MagicMock()
        with patch('builtins.open', open_mock):
            # Call the method
            result = self.dvc_versioning.add_model(
                model_name="test_model",
                model_version="test_version",
                model_data={"test_key": "test_value"}
            )

        # Check the result
        self.assertTrue(result)

        # Check that os.makedirs was called with the correct arguments
        self.os_mock.makedirs.assert_called_once()

        # Check that subprocess.run was called with the correct arguments
        self.subprocess_mock.run.assert_called()


class TestArizeIntegration(unittest.TestCase):
    """Tests for Arize AI integration."""

    def setUp(self):
        """Set up the test case."""
        # Mock the arize module
        self.arize_mock = MagicMock()
        self.arize_patcher = patch('ai.arize_integration.arize', self.arize_mock)
        self.arize_patcher.start()

        # Set up a test instance with mock API keys
        self.arize_observability = arize_observability
        self.arize_observability.api_key = "test_api_key"
        self.arize_observability.space_key = "test_space_key"
        self.arize_observability.enabled = True
        self.arize_observability.client = MagicMock()
        self.arize_observability.client.log.return_value.status_code = 200

    def tearDown(self):
        """Tear down the test case."""
        self.arize_patcher.stop()

    def test_log_prediction(self):
        """Test logging a prediction."""
        # Call the method
        result = self.arize_observability.log_prediction(
            model_id="test_model",
            model_version="test_version",
            prediction_id="test_prediction_id",
            features={"test_key": "test_value"},
            prediction="test_prediction",
            actual="test_actual",
            tags={"test_tag": "test_value"}
        )

        # Check the result
        self.assertTrue(result)

        # Check that client.log was called
        self.arize_observability.client.log.assert_called_once()


class TestAnthropicIntegration(unittest.TestCase):
    """Tests for Anthropic integration."""

    def setUp(self):
        """Set up the test case."""
        # Mock the anthropic module
        self.anthropic_mock = MagicMock()
        self.anthropic_patcher = patch('ai.anthropic_integration.anthropic', self.anthropic_mock)
        self.anthropic_patcher.start()

        # Set up a test instance with a mock API key
        self.enhanced_claude_service = enhanced_claude_service
        self.enhanced_claude_service.api_key = "test_api_key"
        self.enhanced_claude_service.enabled = True
        self.enhanced_claude_service.client = MagicMock()

        # Mock the response
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="test_content")]
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20
        mock_response.id = "test_id"
        self.enhanced_claude_service.client.messages.create.return_value = mock_response

    def tearDown(self):
        """Tear down the test case."""
        self.anthropic_patcher.stop()

    async def test_generate_content(self):
        """Test generating content."""
        # Call the method
        result = await self.enhanced_claude_service.generate_content(
            prompt="test_prompt",
            model="test_model",
            system_prompt="test_system_prompt",
            temperature=0.7,
            max_tokens=100,
            metadata={"test_key": "test_value"}
        )

        # Check the result
        self.assertEqual(result["content"], "test_content")
        self.assertEqual(result["model"], "test_model")
        self.assertEqual(result["usage"]["input_tokens"], 10)
        self.assertEqual(result["usage"]["output_tokens"], 20)
        self.assertEqual(result["usage"]["total_tokens"], 30)
        self.assertEqual(result["id"], "test_id")

        # Check that client.messages.create was called with the correct arguments
        self.enhanced_claude_service.client.messages.create.assert_called_once()
        _, kwargs = self.enhanced_claude_service.client.messages.create.call_args
        self.assertEqual(kwargs["model"], "test_model")
        self.assertEqual(kwargs["max_tokens"], 100)
        self.assertEqual(kwargs["temperature"], 0.7)
        self.assertEqual(kwargs["messages"][0]["role"], "user")
        self.assertEqual(kwargs["messages"][0]["content"], "test_prompt")
        self.assertEqual(kwargs["system"], "test_system_prompt")
        self.assertEqual(kwargs["metadata"], {"test_key": "test_value"})


class TestStabilityIntegration(unittest.TestCase):
    """Tests for Stability AI integration."""

    def setUp(self):
        """Set up the test case."""
        # Mock the aiohttp module
        self.aiohttp_mock = MagicMock()
        self.aiohttp_patcher = patch('ai.stability_integration.aiohttp', self.aiohttp_mock)
        self.aiohttp_patcher.start()

        # Set up a test instance with a mock API key
        self.stability_ai_service = stability_ai_service
        self.stability_ai_service.api_key = "test_api_key"
        self.stability_ai_service.api_host = "test_api_host"
        self.stability_ai_service.enabled = True

        # Mock the response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json.return_value = {
            "artifacts": [
                {
                    "base64": "test_base64",
                    "seed": 123,
                    "finish_reason": "SUCCESS"
                }
            ]
        }
        self.aiohttp_mock.ClientSession.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

    def tearDown(self):
        """Tear down the test case."""
        self.aiohttp_patcher.stop()

    async def test_generate_image(self):
        """Test generating an image."""
        # Call the method
        result = await self.stability_ai_service.generate_image(
            prompt="test_prompt",
            negative_prompt="test_negative_prompt",
            width=512,
            height=512,
            cfg_scale=7.0,
            steps=30,
            samples=1,
            engine_id="test_engine_id"
        )

        # Check the result
        self.assertEqual(len(result["images"]), 1)
        self.assertEqual(result["images"][0]["base64"], "test_base64")
        self.assertEqual(result["images"][0]["seed"], 123)
        self.assertEqual(result["images"][0]["finish_reason"], "SUCCESS")
        self.assertEqual(result["engine_id"], "test_engine_id")
        self.assertEqual(result["prompt"], "test_prompt")
        self.assertEqual(result["negative_prompt"], "test_negative_prompt")

        # Check that aiohttp.ClientSession.post was called with the correct arguments
        self.aiohttp_mock.ClientSession.return_value.__aenter__.return_value.post.assert_called_once()
        args, kwargs = self.aiohttp_mock.ClientSession.return_value.__aenter__.return_value.post.call_args
        self.assertEqual(args[0], "test_api_host/v1/generation/test_engine_id/text-to-image")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test_api_key")
        self.assertEqual(kwargs["json"]["text_prompts"][0]["text"], "test_prompt")
        self.assertEqual(kwargs["json"]["text_prompts"][0]["weight"], 1.0)
        self.assertEqual(kwargs["json"]["text_prompts"][1]["text"], "test_negative_prompt")
        self.assertEqual(kwargs["json"]["text_prompts"][1]["weight"], -1.0)
        self.assertEqual(kwargs["json"]["cfg_scale"], 7.0)
        self.assertEqual(kwargs["json"]["height"], 512)
        self.assertEqual(kwargs["json"]["width"], 512)
        self.assertEqual(kwargs["json"]["samples"], 1)
        self.assertEqual(kwargs["json"]["steps"], 30)


class TestHeliconeIntegration(unittest.TestCase):
    """Tests for Helicone integration."""

    def setUp(self):
        """Set up the test case."""
        # Mock the aiohttp module
        self.aiohttp_mock = MagicMock()
        self.aiohttp_patcher = patch('ai.helicone_integration.aiohttp', self.aiohttp_mock)
        self.aiohttp_patcher.start()

        # Set up a test instance with a mock API key
        self.helicone_service = helicone_service
        self.helicone_service.api_key = "test_api_key"
        self.helicone_service.base_url = "test_base_url"
        self.helicone_service.enabled = True

        # Mock the response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json.return_value = {"test_key": "test_value"}
        self.aiohttp_mock.ClientSession.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

    def tearDown(self):
        """Tear down the test case."""
        self.aiohttp_patcher.stop()

    async def test_get_cost_metrics(self):
        """Test getting cost metrics."""
        # Call the method
        result = await self.helicone_service.get_cost_metrics(
            start_date="2025-01-01",
            end_date="2025-01-31",
            user_id="test_user_id",
            model="test_model"
        )

        # Check the result
        self.assertEqual(result["test_key"], "test_value")

        # Check that aiohttp.ClientSession.get was called with the correct arguments
        self.aiohttp_mock.ClientSession.return_value.__aenter__.return_value.get.assert_called_once()
        args, kwargs = self.aiohttp_mock.ClientSession.return_value.__aenter__.return_value.get.call_args
        self.assertEqual(args[0], "test_base_url/v1/metrics/cost")
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test_api_key")
        self.assertEqual(kwargs["params"]["startDate"], "2025-01-01")
        self.assertEqual(kwargs["params"]["endDate"], "2025-01-31")
        self.assertEqual(kwargs["params"]["userId"], "test_user_id")
        self.assertEqual(kwargs["params"]["model"], "test_model")


class TestLiteLLMIntegration(unittest.TestCase):
    """Tests for LiteLLM integration."""

    def setUp(self):
        """Set up the test case."""
        # Mock the litellm module
        self.litellm_mock = MagicMock()
        self.litellm_patcher = patch('ai.litellm_integration.litellm', self.litellm_mock)
        self.litellm_patcher.start()

        # Set up a test instance
        self.litellm_service = litellm_service
        self.litellm_service.enabled = True

        # Mock the response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content="test_content"))]
        mock_response.model = "test_model"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 30
        mock_response.id = "test_id"
        self.litellm_mock.acompletion.return_value = mock_response
        self.litellm_mock.acompletion_with_fallbacks.return_value = mock_response

    def tearDown(self):
        """Tear down the test case."""
        self.litellm_patcher.stop()

    async def test_generate_completion(self):
        """Test generating a completion."""
        # Call the method
        result = await self.litellm_service.generate_completion(
            prompt="test_prompt",
            model="test_model",
            max_tokens=100,
            temperature=0.7,
            fallbacks=["test_fallback_1", "test_fallback_2"],
            metadata={"test_key": "test_value"}
        )

        # Check the result
        self.assertEqual(result["content"], "test_content")
        self.assertEqual(result["model"], "test_model")
        self.assertEqual(result["usage"]["prompt_tokens"], 10)
        self.assertEqual(result["usage"]["completion_tokens"], 20)
        self.assertEqual(result["usage"]["total_tokens"], 30)
        self.assertEqual(result["id"], "test_id")

        # Check that litellm.acompletion_with_fallbacks was called with the correct arguments
        self.litellm_mock.acompletion_with_fallbacks.assert_called_once()
        args, kwargs = self.litellm_mock.acompletion_with_fallbacks.call_args
        self.assertEqual(kwargs["fallbacks"], ["test_fallback_1", "test_fallback_2"])
        self.assertEqual(kwargs["messages"][0]["role"], "user")
        self.assertEqual(kwargs["messages"][0]["content"], "test_prompt")
        self.assertEqual(kwargs["max_tokens"], 100)
        self.assertEqual(kwargs["temperature"], 0.7)
        self.assertEqual(kwargs["model"], "test_model")
        self.assertEqual(kwargs["metadata"], {"test_key": "test_value"})

    async def test_route_request(self):
        """Test routing a request."""
        # Call the method
        result = await self.litellm_service.route_request(
            prompt="test_prompt",
            task_type="creative",
            max_tokens=100,
            temperature=0.5,
            metadata={"test_key": "test_value"}
        )

        # Check the result
        self.assertEqual(result["content"], "test_content")

        # Check that litellm.acompletion_with_fallbacks was called
        self.litellm_mock.acompletion_with_fallbacks.assert_called_once()


class TestServiceIntegration(unittest.TestCase):
    """Tests for service integration."""

    def setUp(self):
        """Set up the test case."""
        # Mock the enhanced_ai_service
        self.enhanced_ai_service = enhanced_ai_service

        # Mock the components
        self.enhanced_ai_service.octotools_service = MagicMock()
        self.enhanced_ai_service.wandb_registry = MagicMock()
        self.enhanced_ai_service.dvc_versioning = MagicMock()
        self.enhanced_ai_service.arize_observability = MagicMock()
        self.enhanced_ai_service.enhanced_claude_service = MagicMock()
        self.enhanced_ai_service.stability_ai_service = MagicMock()
        self.enhanced_ai_service.helicone_service = MagicMock()
        self.enhanced_ai_service.litellm_service = MagicMock()

        # Set up the litellm_service mock
        self.enhanced_ai_service.litellm_service.enabled = True
        self.enhanced_ai_service.litellm_service.route_request.return_value = {
            "content": "test_content",
            "model": "test_model",
            "usage": {"total_tokens": 30}
        }

        # Set up the stability_ai_service mock
        self.enhanced_ai_service.stability_ai_service.enabled = True
        self.enhanced_ai_service.stability_ai_service.generate_email_banner.return_value = {
            "images": [{"base64": "test_base64"}]
        }

        # Set up the octotools_service mock
        self.enhanced_ai_service.octotools_service.create_email_campaign.return_value = {
            "campaign_id": "test_campaign_id"
        }

    async def test_create_email_campaign(self):
        """Test creating an email campaign."""
        # Call the method
        result = await self.enhanced_ai_service.create_email_campaign(
            campaign_data={
                "name": "test_campaign",
                "subject": "test_subject",
                "audience": "test_audience",
                "objective": "test_objective",
                "task_type": "creative",
                "generate_banner": True,
                "user_id": 123
            }
        )

        # Check the result
        self.assertEqual(result["campaign_id"], "test_campaign_id")
        self.assertEqual(result["ai_info"]["model"], "test_model")

        # Check that litellm_service.route_request was called
        self.enhanced_ai_service.litellm_service.route_request.assert_called_once()

        # Check that stability_ai_service.generate_email_banner was called
        self.enhanced_ai_service.stability_ai_service.generate_email_banner.assert_called_once()

        # Check that octotools_service.create_email_campaign was called
        self.enhanced_ai_service.octotools_service.create_email_campaign.assert_called_once()


def run_async_test(test_case):
    """Run an async test case."""
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test_case)


if __name__ == '__main__':
    # Run the tests
    unittest.main()
