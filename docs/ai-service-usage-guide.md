# Maily AI Service Usage Guide

This guide provides instructions for using the Maily AI Service in your applications.

## Overview

The Maily AI Service provides a unified interface for AI capabilities in the Maily platform:

- Text generation with multiple model providers (OpenAI, Anthropic, Google)
- Email campaign creation and management
- Contact discovery and audience segmentation
- Monitoring and observability
- Platform integration

## Getting Started

### Basic Import

```python
from apps.api.ai import AIService

# Create an instance
ai_service = AIService()
```

### Text Generation

Generate text with different AI models:

```python
# Basic text generation
response = await ai_service.generate_text(
    prompt="Write an email subject line for a product launch",
    model="gpt-4",
    temperature=0.7
)

print(response.content)

# With function calling
response = await ai_service.generate_text(
    prompt="Create a summary of user activity",
    model="gpt-4",
    tools=[{
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
)
```

## Email Marketing Features

### Creating Email Campaigns

```python
campaign_result = await ai_service.create_email_campaign({
    "objective": "Product launch announcement",
    "audience": "Existing customers interested in productivity tools",
    "brand_voice": "professional",
    "key_points": [
        "New AI-powered features",
        "20% faster performance",
        "Available on all platforms"
    ]
})

print(f"Subject: {campaign_result['subject']}")
print(f"Preview: {campaign_result['preview']}")
```

### Discovering Contacts

```python
contacts = await ai_service.discover_contacts({
    "industry": "Technology",
    "location": "San Francisco",
    "interests": ["AI", "Machine Learning"],
    "company_size": "50-200"
})

print(f"Found {len(contacts['results'])} potential contacts")
```

### Segmenting Audiences

```python
segments = await ai_service.segment_audience({
    "contacts": contacts_data,
    "engagement_metrics": {"open_rate": "high", "click_rate": "medium"},
    "demographics": {"industry": "Technology", "role": "Marketing"}
})

print(f"Created {len(segments['segments'])} segments")
for segment in segments['segments']:
    print(f"Segment: {segment['name']} - {segment['count']} contacts")
```

## Monitoring and Observability

The service includes built-in monitoring features:

```python
# Check health of AI providers
health = await ai_service.check_health()
print(f"Service status: {health['status']}")

# Get performance metrics
metrics = ai_service.get_performance_metrics()
print(f"Average latency: {metrics['latency']['avg_ms']}ms")
print(f"Success rate: {metrics['success_rate']}%")
```

## Configuration

Configure the service using environment variables:

```
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
WANDB_API_KEY=your_wandb_key
```

## Complete Example

For a complete usage example, see:

```
apps/api/ai/examples/ai_service_example.py
```
