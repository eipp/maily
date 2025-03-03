# Architecture Decision Record: Circuit Breaker Implementation

## Status
Accepted

## Context
The Maily platform relies on multiple external dependencies, including databases, third-party APIs, and other microservices. When these dependencies fail or experience performance degradation, it can lead to cascading failures throughout the system. We need a reliable mechanism to prevent these failures from propagating and to provide graceful degradation of functionality when dependencies are unavailable.

## Decision
We have decided to implement the Circuit Breaker pattern across our services, starting with the AI service's database interactions and external LLM provider integrations. The implementation follows these key principles:

1. **Configurable failure thresholds**: Circuit breakers open after a specific number of failures (default: 3-5)
2. **Automatic recovery**: Circuit breakers automatically transition to a half-open state after a configured recovery timeout
3. **Fallback mechanisms**: Each circuit breaker provides meaningful fallback behavior when the circuit is open
4. **Monitoring and observability**: Circuit breaker state changes are logged for monitoring
5. **Excluded exceptions**: Certain exceptions (e.g., rate limits) don't count as circuit breaker failures

## Implementation Details

### 1. Core Circuit Breaker Interface
The circuit breaker implementation supports both synchronous and asynchronous functions through dedicated decorators:

```python
# Synchronous decorator
@circuit_breaker(
    name="service_name",
    failure_threshold=3,
    recovery_timeout=60.0,
    fallback_function=lambda *args, **kwargs: fallback_value
)
def some_function(arg1, arg2):
    pass

# Asynchronous decorator
@async_circuit_breaker(
    name="service_name",
    failure_threshold=3,
    recovery_timeout=60.0,
    fallback_function=async_fallback_function
)
async def some_async_function(arg1, arg2):
    pass
```

### 2. Database Service Circuit Breakers
Database operations in the AI service are protected by circuit breakers with fallback mechanisms:

```python
@circuit_breaker(
    name="database_get_session",
    failure_threshold=3,
    recovery_timeout=60.0,
    fallback_function=lambda session_id: {
        "id": session_id,
        "user_id": "unknown",
        "status": "error",
        "messages": [],
        "agents": [],
        "metadata": {"error": "Database service temporarily unavailable"},
        "created_at": None,
        "updated_at": None
    }
)
def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    # Database access logic
```

### 3. External API Circuit Breakers
External API calls to LLM providers are protected by circuit breakers:

```python
@async_circuit_breaker(
    name="openai",
    failure_threshold=3,
    recovery_timeout=60.0,
    excluded_exceptions=[openai.RateLimitError],
    fallback_function=lambda *args, **kwargs: "OpenAI service is currently unavailable. Please try again later."
)
async def _openai_completion(self, messages, model, max_tokens, temperature, user_id) -> str:
    # OpenAI API call logic
```

### 4. Circuit Breaker States
The circuit breaker can be in one of three states:
- **CLOSED**: Normal operation, requests flow through
- **OPEN**: Failing dependency detected, requests are blocked and fallback is used
- **HALF_OPEN**: Testing if the dependency has recovered, allowing limited requests

### 5. Recovery Mechanism
When a circuit breaker is open, it automatically transitions to a half-open state after the recovery timeout. In the half-open state, a limited number of requests are allowed through to test if the dependency has recovered. If these succeed, the circuit breaker closes; if they fail, it returns to the open state.

## Consequences

### Positive
- Prevents cascading failures across the system
- Reduces load on struggling dependencies, giving them time to recover
- Provides graceful degradation with meaningful fallbacks
- Improves overall system resilience and stability
- Enables automated recovery without manual intervention

### Negative
- Adds complexity to the codebase
- May lead to inconsistent user experiences when fallbacks are used
- Requires careful tuning of thresholds and timeouts
- May mask underlying issues that should be addressed

## Further Considerations
1. We should expand circuit breaker implementation to all critical external dependencies
2. We should add metrics collection for circuit breaker state changes
3. Circuit breaker settings should eventually be configurable via environment variables
4. We should establish guidelines for creating effective fallback mechanisms