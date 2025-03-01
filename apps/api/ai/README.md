# Maily AI Service

This module provides a unified AI service for the Maily platform, integrating various AI capabilities for email marketing tasks.

## Overview

The Maily AI Service provides a comprehensive set of AI capabilities:

- Text generation with multiple model providers (OpenAI, Anthropic, Google)
- Email campaign creation and management
- Contact discovery and audience segmentation
- Monitoring and observability integrations (Langfuse, Weights & Biases, Arize)

## Usage

### Basic Import

```python
from apps.api.ai import AIService

# Create an instance
ai_service = AIService()

# Generate text
response = await ai_service.generate_text(
    prompt="Write an email subject line for a product launch",
    model="gpt-4"
)
```

### Email Marketing Features

The AI service provides specialized methods for email marketing:

```python
# Create an email campaign
campaign = await ai_service.create_email_campaign(
    campaign_data={
        "objective": "Product launch",
        "audience": "Existing customers",
        "key_points": ["New features", "Special pricing"]
    }
)

# Discover contacts
contacts = await ai_service.discover_contacts(
    discovery_data={
        "industry": "Technology",
        "location": "San Francisco",
        "interests": ["AI", "Machine Learning"]
    }
)

# Segment audience
segments = await ai_service.segment_audience(
    audience_data={
        "contacts": contacts,
        "engagement_metrics": {"open_rate": "high"},
        "demographics": {"industry": "Technology"}
    }
)
```

### Monitoring

The service includes built-in monitoring:

```python
# Get performance metrics
metrics = ai_service.get_performance_metrics()

# Check health
health = await ai_service.check_health()
```

## Configuration

The service can be configured using environment variables:

```
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
GOOGLE_API_KEY=your_google_key
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
```

## Examples

For complete examples, see the `examples` directory:

```
apps/api/ai/examples/ai_service_example.py
```
