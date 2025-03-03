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

### Agents

- `POST /api/mesh/networks/{network_id}/agents`: Add an agent to a network
- `DELETE /api/mesh/networks/{network_id}/agents/{agent_id}`: Remove an agent from a network
- `GET /api/mesh/networks/{network_id}/agents`: List agents for a network

### Memory

- `POST /api/mesh/networks/{network_id}/memory`: Add a memory item to the shared memory
- `GET /api/mesh/networks/{network_id}/memory`: Get shared memory for a network

### Health

- `GET /api/mesh/health`: Check health of the AI Mesh Network service

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

## Model Fallback Chain

The AI Mesh Network supports a fallback chain for LLM models in case the primary model is unavailable:

1. Claude 3.7 Sonnet (Primary)
2. GPT-4o (Fallback 1)
3. Gemini 2.0 (Fallback 2)

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

## Security Considerations

- **API Authentication**: All API endpoints require authentication
- **Data Isolation**: Each network's data is isolated from other networks
- **Input Validation**: All inputs are validated to prevent injection attacks
- **Content Safety**: Content generated by agents is filtered for safety and compliance

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
