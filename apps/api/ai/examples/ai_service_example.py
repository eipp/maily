"""
AI Service Example

This module demonstrates how to use the Maily AI Service for various tasks.
"""

import asyncio
import os
import json
from typing import Dict, Any, List

from apps.api.ai import AIService

# Create an instance of the AI service
ai_service = AIService()

async def generate_text_example():
    """Example of text generation."""
    print("\n=== Text Generation Example ===")

    # Basic text generation
    response = await ai_service.generate_text(
        prompt="Write an email subject line for a product launch",
        model="gpt-4",
        temperature=0.7
    )

    print(f"Subject line: {response.content}")
    print(f"Model: {response.model}")
    print(f"Tokens: {response.usage.get('total_tokens', 0)}")

    # Function calling example
    tools = [{
        "type": "function",
        "function": {
            "name": "get_user_activity",
            "description": "Get a user's recent activity",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string"},
                    "days": {"type": "integer"}
                },
                "required": ["user_id"]
            }
        }
    }]

    response = await ai_service.generate_text(
        prompt="Get activity for user 12345",
        model="gpt-4",
        temperature=0.2,
        tools=tools
    )

    print("\nFunction calling example:")
    if hasattr(response, 'tool_calls') and response.tool_calls:
        print(f"Tool calls: {json.dumps(response.tool_calls, indent=2)}")
    else:
        print(f"Response: {response.content}")

async def create_email_campaign_example():
    """Example of email campaign creation."""
    print("\n=== Email Campaign Creation Example ===")

    campaign_data = {
        "objective": "Product launch announcement",
        "audience": "Existing customers interested in productivity tools",
        "brand_voice": "professional",
        "key_points": [
            "New AI-powered features",
            "20% faster performance",
            "Available on all platforms"
        ]
    }

    result = await ai_service.create_email_campaign(campaign_data)

    print(f"Subject: {result.get('subject', 'N/A')}")
    print(f"Preview: {result.get('preview', 'N/A')[:100]}...")

async def discover_contacts_example():
    """Example of contact discovery."""
    print("\n=== Contact Discovery Example ===")

    discovery_data = {
        "industry": "Technology",
        "location": "San Francisco",
        "interests": ["AI", "Machine Learning"],
        "company_size": "50-200"
    }

    result = await ai_service.discover_contacts(discovery_data)

    print(f"Found {len(result.get('results', []))} potential contacts")
    if result.get('results'):
        print("Sample contact:")
        print(json.dumps(result['results'][0], indent=2))

async def segment_audience_example():
    """Example of audience segmentation."""
    print("\n=== Audience Segmentation Example ===")

    # Mock contacts data
    contacts_data = [
        {"id": "1", "name": "John Doe", "email": "john@example.com", "engagement": "high", "industry": "Technology"},
        {"id": "2", "name": "Jane Smith", "email": "jane@example.com", "engagement": "medium", "industry": "Healthcare"},
        # ... more contacts
    ]

    segmentation_data = {
        "contacts": contacts_data,
        "engagement_metrics": {"open_rate": "high", "click_rate": "medium"},
        "demographics": {"industry": "Technology", "role": "Marketing"}
    }

    result = await ai_service.segment_audience(segmentation_data)

    print(f"Created {len(result.get('segments', []))} segments")
    for segment in result.get('segments', []):
        print(f"Segment: {segment.get('name')} - {segment.get('count')} contacts")

async def main():
    """Run all examples."""
    # Set API key for testing
    os.environ["OPENAI_API_KEY"] = "your-api-key-here"

    await generate_text_example()
    await create_email_campaign_example()
    await discover_contacts_example()
    await segment_audience_example()

if __name__ == "__main__":
    asyncio.run(main())
