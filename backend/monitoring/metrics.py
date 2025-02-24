from prometheus_client import Counter, Histogram

# Request metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])

# Model metrics
MODEL_LATENCY = Histogram('model_inference_duration_seconds', 'Model inference latency', ['model_name'])

# Cache metrics
CACHE_HITS = Counter('cache_hits_total', 'Cache hit count', ['cache_type'])
CACHE_MISSES = Counter('cache_misses_total', 'Cache miss count', ['cache_type']) 