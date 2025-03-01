# Maily Architecture

## Overview

Maily is designed with a modular, microservices-based architecture built around hexagonal (ports and adapters) principles to ensure domain logic remains isolated from external technologies.

## Architectural Layers

Maily's architecture is divided into four main layers:

### 1. Frontend Layer
- **Technologies**: Next.js, React, Tailwind CSS
- **Key Components**:
  - Chat-centric UI for natural language interactions
  - Visual Canvas for email design with real-time collaboration

### 2. Backend Layer
- **Technologies**: FastAPI, PostgreSQL, Redis, Temporal
- **Key Components**:
  - RESTful APIs for all platform operations
  - Supabase for persistent data and authentication
  - Redis for high-speed caching

### 3. AI & Data Layer
- **Technologies**: OctoTools, Vercel AI SDK, Vector Database
- **Key Components**:
  - AI Agent Orchestration for specialized tasks
  - Multi-model support (OpenAI, Anthropic, Google)
  - Adapter pattern for model integration

### 4. Trust Infrastructure Layer
- **Technologies**: Ethereum, Polygon
- **Key Components**:
  - Smart contracts for verification and certificates
  - Performance-based rewards and incentives
  - Cross-chain support

## Microservices

Maily implements the following core microservices:

1. **Email Processing Service**: Handles email generation and dispatch
2. **Contact Management Service**: Manages contacts and segmentation
3. **Analytics Service**: Processes campaign performance data
4. **Canvas Service**: Manages visual creation environment
5. **Blockchain Service**: Handles blockchain interactions

## Hexagonal Architecture Implementation

### Adapter Pattern

The adapter pattern is fully implemented throughout the codebase:

```python
# Interface (Port)
class BaseModelAdapter(ABC):
    @abstractmethod
    async def generate(self, request: ModelRequest) -> ModelResponse:
        pass

    @abstractmethod
    async def stream_generate(self, request: ModelRequest) -> AsyncIterator[ModelResponse]:
        pass
```

```python
# Concrete Adapter Implementation
class OpenAIAdapter(BaseModelAdapter):
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def generate(self, request: ModelRequest) -> ModelResponse:
        # OpenAI-specific implementation
        response = await self.client.chat.completions.create(...)
        return ModelResponse(...)
```

```python
# Factory
class ModelAdapterFactory:
    def __init__(self):
        self._adapters: Dict[str, BaseModelAdapter] = {}
        self._adapter_classes: Dict[str, Type[BaseModelAdapter]] = {
            "openai": OpenAIAdapter,
            "anthropic": AnthropicAdapter,
            "google": GoogleAIAdapter,
        }

    def get_adapter(self, provider: str, api_key: Optional[str] = None) -> BaseModelAdapter:
        # Factory implementation logic
```

## Authentication

Maily supports two primary authentication methods:

1. **JWT Authentication**: Using Auth0 as the identity provider
2. **API Key Authentication**: For programmatic access

Both methods are implemented in a middleware layer that handles authentication before request processing.

## Data Architecture

Maily implements a multi-database approach:

- **PostgreSQL**: Primary persistent datastore for structured data
- **Redis**: High-speed caching and transient data with defined TTLs
- **Vector Database**: Stores embeddings for AI-powered features
- **Blockchain**: Provides immutable trust verification

## Data Flow Example

When a campaign is scheduled:
1. Campaign Management Service creates a workflow in Temporal
2. At the scheduled time, Temporal triggers the Email Processing Service
3. Results are stored in PostgreSQL and cached in Redis
4. Performance metrics are recorded on blockchain
5. Tokens are distributed based on performance
