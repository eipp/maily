# AI Mesh Network

The AI Mesh Network is an advanced AI-driven feature that creates a collaborative network of specialized AI agents with shared memory and dynamic task delegation.

## Overview

The AI Mesh Network enables complex AI tasks to be broken down and distributed among specialized agents, each with their own expertise and capabilities. This approach allows for more sophisticated reasoning, better task specialization, and improved overall performance compared to using a single AI model.

Key features include:

- **Collaborative Agent Network**: Multiple specialized AI agents working together on complex tasks
- **Shared Memory**: Persistent memory that allows agents to build on each other's work
- **Dynamic Task Delegation**: Intelligent distribution of subtasks to the most appropriate agents
- **Model Fallback Chain**: Automatic fallback to alternative models if the primary model is unavailable
- **Resilient Architecture**: Designed to handle failures gracefully with circuit breakers and retry mechanisms

## Architecture

The AI Mesh Network consists of the following components:

1. **Agent Coordinator**: Orchestrates the network of agents, manages task delegation, and synthesizes results
2. **Specialized Agents**: Individual AI agents with specific capabilities (content, design, analytics, etc.)
3. **Shared Memory**: Persistent storage for facts, context, decisions, and feedback
4. **Task Management**: Handles task submission, processing, and result delivery

## API Endpoints

The AI Mesh Network exposes the following REST API endpoints:

### Networks

- `POST /api/mesh/networks`: Create a new AI Mesh Network
- `GET /api/mesh/networks`: List all AI Mesh Networks
- `GET /api/mesh/networks/{network_id}`: Get details of a specific network
- `DELETE /api/mesh/networks/{network_id}`: Delete a network

### Tasks

- `POST /api/mesh/networks/{network_id}/tasks`: Submit a task to a network
- `POST /api/mesh/networks/{network_id}/tasks/{task_id}/process`: Process a task
- `GET /api/mesh/networks/{network_id}/tasks/{task_id}`: Get details of a task
- `GET /api/mesh/networks/{network_id}/tasks`: List tasks for a network

### Streaming Endpoints

- `POST /api/mesh/networks/{network_id}/tasks/stream`: Submit a task with streaming response
- `GET /api/mesh/tasks/{task_id}/stream`: Get streaming updates for a task
- `GET /api/mesh/tasks/{task_id}/events`: Get SSE events for a task
- `POST /api/mesh/generate/stream`: Direct streaming from LLMs

### Agents

- `POST /api/mesh/networks/{network_id}/agents`: Add an agent to a network
- `DELETE /api/mesh/networks/{network_id}/agents/{agent_id}`: Remove an agent from a network
- `GET /api/mesh/networks/{network_id}/agents`: List agents for a network

### Memory

- `POST /api/mesh/networks/{network_id}/memory`: Add a memory item to the shared memory
- `GET /api/mesh/networks/{network_id}/memory`: Get shared memory for a network

### Health and Stats

- `GET /api/mesh/health`: Check health of the AI Mesh Network service
- `GET /api/mesh/stats/cost`: Get cost statistics for models, users, and networks
- `GET /api/mesh/stats/usage`: Get usage statistics for models and API calls
- `GET /api/mesh/stats/models`: Get detailed information about available models and their capabilities

### Security

- `POST /api/mesh/security/api-keys`: Create a new API key
- `GET /api/mesh/security/api-keys`: List API keys for a user (admin only)
- `DELETE /api/mesh/security/api-keys/{api_key}`: Revoke an API key
- `GET /api/mesh/security/audit-logs`: Get audit logs with filtering (admin only)
- `POST /api/mesh/security/retention-policy`: Set data retention policy (admin only)
- `GET /api/mesh/security/retention-policy`: Get current data retention policy

## Usage Examples

### Creating a Network

```bash
curl -X POST http://localhost:8080/api/mesh/networks \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Email Campaign Assistant",
    "description": "AI network for creating and optimizing email campaigns",
    "max_iterations": 10,
    "timeout_seconds": 300
  }'
```

### Using Intelligent Model Selection

```bash
curl -X POST http://localhost:8080/api/mesh/networks/{network_id}/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create an email campaign for a new product launch",
    "context": {
      "product_name": "TechPro X1",
      "product_description": "Advanced AI-powered development tool"
    },
    "model_selection": {
      "task_complexity": "MEDIUM",
      "requires_vision": false,
      "requires_function_calling": false,
      "cost_sensitive": true
    }
  }'
```

### Submitting a Task

```bash
curl -X POST http://localhost:8080/api/mesh/networks/{network_id}/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create an email campaign for a new product launch targeting tech professionals",
    "context": {
      "product_name": "TechPro X1",
      "product_description": "Advanced AI-powered development tool",
      "target_audience": "Software developers and IT professionals",
      "key_features": ["AI code completion", "Automated testing", "Performance optimization"]
    },
    "priority": 1
  }'
```

### Processing a Task

```bash
curl -X POST http://localhost:8080/api/mesh/networks/{network_id}/tasks/{task_id}/process
```

### Getting Task Results

```bash
curl -X GET http://localhost:8080/api/mesh/networks/{network_id}/tasks/{task_id}
```

### Using Streaming Responses

```bash
# Submit a task with streaming response
curl -N -X POST http://localhost:8080/api/mesh/networks/{network_id}/tasks/stream \
  -H "Content-Type: application/json" \
  -d '{
    "task": "Create an email campaign for a new product launch",
    "context": {
      "product_name": "TechPro X1",
      "target_audience": "Software developers"
    },
    "priority": 1
  }'
```

### Using Server-Sent Events (SSE)

```javascript
// JavaScript example using EventSource
const eventSource = new EventSource(`http://localhost:8080/api/mesh/tasks/${taskId}/events`);

eventSource.addEventListener('started', (event) => {
  const data = JSON.parse(event.data);
  console.log('Task started:', data);
});

eventSource.addEventListener('result', (event) => {
  const data = JSON.parse(event.data);
  console.log('Task result:', data);
});

eventSource.addEventListener('complete', (event) => {
  const data = JSON.parse(event.data);
  console.log('Task completed:', data);
  eventSource.close();
});

eventSource.addEventListener('error', (event) => {
  console.error('Error in SSE stream:', event);
  eventSource.close();
});
```

### Using Direct LLM Streaming

```bash
# Stream directly from an LLM
curl -N -X POST http://localhost:8080/api/mesh/generate/stream \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a short introduction email for TechPro X1",
    "model": "claude-3-7-sonnet",
    "temperature": 0.7,
    "max_tokens": 1000
  }'
```

### Retrieving Cost and Usage Statistics

```bash
curl -X GET http://localhost:8080/api/mesh/stats/cost
```

Sample response:
```json
{
  "total_cost": 1.28,
  "per_model": {
    "claude-3-7-sonnet": 0.65,
    "gpt-4o": 0.45,
    "gemini-1.5-pro": 0.18
  },
  "per_user": {
    "user123": 0.85,
    "user456": 0.43
  },
  "per_network": {
    "network-1": 0.76,
    "network-2": 0.52
  },
  "time_period": "2025-03-01T00:00:00Z to 2025-03-05T23:59:59Z"
}
```

```bash
curl -X GET http://localhost:8080/api/mesh/stats/usage
```

Sample response:
```json
{
  "total_calls": 256,
  "successful_calls": 245,
  "failed_calls": 11,
  "per_model": {
    "claude-3-7-sonnet": 120,
    "gpt-4o": 98,
    "gemini-1.5-pro": 38
  },
  "average_latency": {
    "claude-3-7-sonnet": 0.85,
    "gpt-4o": 0.92,
    "gemini-1.5-pro": 0.75
  },
  "time_period": "2025-03-01T00:00:00Z to 2025-03-05T23:59:59Z"
}
```

## Default Agents

When creating a new AI Mesh Network without specifying agents, the following default agents are created:

1. **Coordinator Agent**: Coordinates tasks and delegates to specialized agents
2. **Content Specialist**: Specializes in generating and refining content
3. **Design Specialist**: Specializes in design and layout considerations
4. **Analytics Specialist**: Specializes in data analysis and performance insights
5. **Personalization Specialist**: Specializes in audience targeting and personalization

## Custom Agents

You can create custom agents with specific capabilities by providing agent configurations when creating a network or by adding agents to an existing network.

Example of creating a custom agent:

```bash
curl -X POST http://localhost:8080/api/mesh/networks/{network_id}/agents \
  -H "Content-Type: application/json" \
  -d '{
    "agent_config": {
      "name": "SEO Specialist",
      "type": "seo",
      "model": "claude-3-7-sonnet",
      "description": "Specializes in search engine optimization",
      "parameters": {
        "temperature": 0.4,
        "max_tokens": 4000
      },
      "capabilities": ["keyword_analysis", "seo_optimization", "content_recommendations"]
    }
  }'
```

## Memory Types

The shared memory system supports the following types of memory items:

- **fact**: Factual information that is objectively true
- **context**: Contextual information about the task or domain
- **decision**: Decisions made during task processing
- **feedback**: Feedback on previous actions or results

## Model Selection and Optimization

The AI Mesh Network includes advanced model selection and optimization capabilities:

### Intelligent Model Selection

The system automatically selects the most appropriate model based on:

- **Task Complexity**: Matches model capabilities to the complexity of the task (LOW, MEDIUM, HIGH)
- **Required Capabilities**: Filters models based on required capabilities (e.g., vision, function calling)
- **Cost Sensitivity**: Optimizes for cost when budget is a priority
- **Performance History**: Uses historical performance data to refine selection

### Model Fallback Chain

The AI Mesh Network supports a fallback chain for LLM models in case the primary model is unavailable:

1. Claude 3.7 Sonnet (Primary)
2. GPT-4o (Fallback 1)
3. Gemini 2.0 (Fallback 2)

### Provider-Specific Optimizations

Each LLM provider has dedicated optimizations:

- **Claude**: Optimized for detailed reasoning and creative tasks with enhanced JSON mode
- **GPT**: Fine-tuned for function calling and structured outputs
- **Gemini**: Optimized for multimodal inputs and long context processing
- **Groq**: Configured for low-latency, cost-effective processing

### Cost Tracking

The system provides comprehensive cost tracking:

- **Per-Model Tracking**: Tracks costs for each model separately
- **Per-User Attribution**: Attributes costs to specific users
- **Budget Controls**: Automatically selects more cost-effective models when needed
- **Usage Reports**: Provides detailed usage and cost reports

## Performance Considerations

- **Concurrency**: The system is designed to handle multiple concurrent tasks across different networks
- **Resource Usage**: Each agent uses its own LLM instance, which can consume significant resources
- **Timeout Handling**: Tasks have configurable timeouts to prevent hanging operations
- **Rate Limiting**: API calls to LLM providers are rate-limited to avoid quota issues

## Integration with Other Services

The AI Mesh Network can be integrated with other services in the Maily platform:

- **Email Service**: For sending generated email campaigns
- **Analytics Service**: For providing data to the Analytics Specialist agent
- **Campaign Service**: For managing and tracking email campaigns
- **User Service**: For accessing user preferences and data

## Security Features

The AI Mesh Network implements robust security features:

### Authentication & Authorization

- **API Key Authentication**: HMAC-based API keys with strong cryptographic security
- **Role-Based Access Control**: Fine-grained permissions with user, admin, and service roles
- **Scoped Permissions**: Granular permission scopes (read, write, create, delete, admin)
- **Key Management**: API for creating, listing, and revoking API keys
- **Authorization Checks**: Comprehensive authorization checks for all operations

### Audit Logging

- **Comprehensive Audit Trail**: All operations are logged for accountability
- **Operation Tracking**: Detailed logging of who did what and when
- **Searchable Logs**: Query interface for filtering and retrieving audit logs
- **Enhanced Metadata**: Client IP, session ID, and operation details are captured
- **Structured Format**: JSON-formatted logs for easy analysis

### Data Retention

- **Configurable Policies**: Customizable retention periods for all data types
- **Automatic Cleanup**: Background process to clean up expired data
- **TTL-Based Storage**: All data stored with appropriate time-to-live settings
- **Resource Cleanup**: Automatic cleanup of associated resources when deleting networks
- **Admin Controls**: Administrative API for setting and viewing retention policies

### Input Validation & Sanitization

- **Strict Validation**: Comprehensive validation for all input parameters
- **Pattern Detection**: Detection of potentially dangerous patterns in inputs
- **Context Sanitization**: Sanitization of user-provided contexts to prevent injection
- **Error Reporting**: Clear error messages for validation failures
- **Security Headers**: Protection against common web vulnerabilities

### Example: Using API Key Authentication

```bash
# Create a new API key
curl -X POST http://localhost:8080/api/mesh/security/api-keys \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer admin-api-key" \
  -d '{
    "user_id": "user123",
    "role": "user",
    "scopes": ["read", "write"]
  }'

# Use the API key for operations
curl -X POST http://localhost:8080/api/mesh/networks \
  -H "Content-Type: application/json" \
  -H "X-API-Key: user123.1709747200.a1b2c3d4" \
  -d '{
    "name": "Secure Network",
    "description": "Network with strong security"
  }'
```

### Example: Viewing Audit Logs

```bash
# Get audit logs with filtering
curl -X GET "http://localhost:8080/api/mesh/security/audit-logs?user_id=user123&resource_type=network&action=create_network&limit=10" \
  -H "Authorization: Bearer admin-api-key"
```

### Example: Setting Data Retention Policy

```bash
# Set data retention policy
curl -X POST http://localhost:8080/api/mesh/security/retention-policy \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer admin-api-key" \
  -d '{
    "retention_days": 180
  }'
```

## Monitoring and Observability

The AI Mesh Network provides the following monitoring capabilities:

- **Health Checks**: Regular health checks for all components
- **Metrics**: Performance metrics for tasks, agents, and networks
- **Logging**: Detailed logging of all operations
- **Tracing**: Distributed tracing for complex task flows

## Future Enhancements

Planned enhancements for the AI Mesh Network include:

- **Agent Learning**: Agents that learn from past interactions and improve over time
- **Multi-Modal Support**: Support for image, audio, and video processing
- **External Tool Integration**: Allowing agents to use external tools and APIs
- **User Feedback Loop**: Incorporating user feedback to improve agent performance
- **Advanced Visualization**: Visual representation of agent interactions and task flows
- **Rate Limiting**: Advanced token bucket algorithm for API rate limiting
- **Long-term Memory**: Persistent memory storage beyond current retention periods
- **Advanced Testing**: Load testing and chaos testing frameworks
- **Enhanced Documentation**: Complete OpenAPI 3.1 specification and developer guides
