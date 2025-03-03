import pytest
import asyncio
import json
import os

from apps.api.services.octotools_service import OctoToolsService

# Create octotools service instance for testing
octotools_service = OctoToolsService()

class MockLangfuse:
    def trace(self, name, user_id, metadata):
        print(f"Creating trace: {name}, user_id: {user_id}, metadata: {metadata}")

        class MockTrace:
            def span(self, name):
                print(f"Creating span: {name}")

                class MockSpan:
                    def __enter__(self):
                        print("Entering span")
                        return self

                    def __exit__(self, *args):
                        print("Exiting span")

                    def add_observation(self, name, value):
                        print(f"Adding observation: {name}")

                return MockSpan()

            def error(self, name, message):
                print(f"Error: {name}, message: {message}")

        return MockTrace()

async def test_create_email_campaign():
    # Test without Langfuse
    print("\nTesting without Langfuse:")
    result = await octotools_service.create_email_campaign({
        'objective': 'test',
        'audience': 'test',
        'from_email': 'test@example.com',
        'recipients': ['test@example.com']
    })
    print(f"Result: {result}")

    # Test with Langfuse
    print("\nTesting with Langfuse:")
    langfuse_client = MockLangfuse()
    result = await octotools_service.create_email_campaign({
        'objective': 'test',
        'audience': 'test'
    }, langfuse_client)
    print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(test_create_email_campaign())
