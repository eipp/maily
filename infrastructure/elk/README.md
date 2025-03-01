# ELK Stack Integration for Maily

This directory contains the configuration files for the Elasticsearch, Logstash, and Kibana (ELK) stack integration for Maily. The ELK stack provides centralized logging capabilities with powerful search, visualization, and analysis features.

## Components

The ELK stack consists of the following components:

- **Elasticsearch**: A distributed, RESTful search and analytics engine that stores all the log data.
- **Logstash**: A data processing pipeline that ingests, transforms, and enriches data from multiple sources before sending it to Elasticsearch.
- **Kibana**: A visualization platform for exploring, visualizing, and building dashboards based on the data in Elasticsearch.
- **Filebeat**: A lightweight shipper for forwarding logs from servers and containers to Logstash or Elasticsearch.

## Directory Structure

```
infrastructure/elk/
├── filebeat/              # Filebeat configuration
├── logstash/
│   ├── config/            # Logstash main configuration
│   └── pipeline/          # Logstash pipeline configurations
└── README.md              # This file
```

## Deployment Options

### Development Environment

For development environments, use the Docker Compose setup in `docker-compose.elk.yml` at the root of the project:

```bash
# Start the ELK stack
docker-compose -f docker-compose.elk.yml up -d

# Check status
docker-compose -f docker-compose.elk.yml ps

# View logs
docker-compose -f docker-compose.elk.yml logs -f elasticsearch
docker-compose -f docker-compose.elk.yml logs -f logstash
docker-compose -f docker-compose.elk.yml logs -f kibana
docker-compose -f docker-compose.elk.yml logs -f filebeat
```

The services will be available at:
- Elasticsearch: http://localhost:9200
- Kibana: http://localhost:5601
- Logstash: TCP/UDP port 5001, Beats port 5044

### Production Environment

For production environments, use the Kubernetes manifests in the `infrastructure/kubernetes/monitoring/` directory:

```bash
# Create the monitoring namespace if it doesn't exist
kubectl create namespace monitoring

# Apply the manifests
kubectl apply -f infrastructure/kubernetes/monitoring/elasticsearch-secrets.yaml
kubectl apply -f infrastructure/kubernetes/monitoring/elasticsearch.yaml
kubectl apply -f infrastructure/kubernetes/monitoring/logstash.yaml
kubectl apply -f infrastructure/kubernetes/monitoring/kibana.yaml
kubectl apply -f infrastructure/kubernetes/monitoring/filebeat.yaml
kubectl apply -f infrastructure/kubernetes/monitoring/elasticsearch-ilm.yaml
kubectl apply -f infrastructure/kubernetes/monitoring/kibana-dashboards.yaml

# Check deployment status
kubectl get pods -n monitoring
```

## Log Collection

### Structured Logging

The ELK stack is configured to parse and understand JSON-formatted logs. All Maily applications should use structured logging with the following format:

```json
{
  "timestamp": "2025-02-28T12:34:56.789Z",
  "level": "info",
  "message": "User logged in successfully",
  "service": "maily-api",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "123456",
  "method": "POST",
  "path": "/api/auth/login",
  "status_code": 200,
  "duration_ms": 42
}
```

### Log Fields

Common fields that should be included in logs:

- `timestamp`: ISO 8601 formatted timestamp
- `level`: Log level (info, warn, error, debug)
- `message`: The log message
- `service`: The service/application name
- `request_id`: Unique identifier for the request (for request tracing)
- `user_id`: User identifier (when applicable)
- `tenant_id`: Tenant/organization identifier (when applicable)

Service-specific fields:

- API logs: `method`, `path`, `status_code`, `duration_ms`
- Worker logs: `job_id`, `worker_type`, `execution_time`
- Web logs: `route`, `page`

### Log Levels

Use appropriate log levels:

- `error`: Error conditions requiring immediate attention
- `warn`: Warning conditions that might require attention
- `info`: Normal but significant events
- `debug`: Detailed debug information (not in production)
- `trace`: Very detailed debug information (not in production)

## Kibana Dashboards

Pre-configured dashboards are available in Kibana:

1. **API Monitoring Dashboard**: Shows API performance metrics, status codes, and errors
2. **System Overview Dashboard**: Provides a system-wide view of logs across all services

To access custom dashboards:
1. Open Kibana (http://localhost:5601 in development or https://kibana.maily.com in production)
2. Navigate to Dashboard section
3. Select the desired dashboard

## Log Retention and Lifecycle

By default, logs are kept for:

- Regular logs: 30 days (with hot-warm-cold storage tiers)
- High-volume logs: 7 days

These settings can be modified in the Elasticsearch ILM policies.

## Security Considerations

In production:

1. **Change Default Passwords**: Modify all default passwords in the `elasticsearch-secrets.yaml` file
2. **Enable TLS**: Configure SSL/TLS for all communication
3. **Set Up Role-Based Access Control**: Create specific roles and users in Elasticsearch
4. **Network Policies**: Restrict access to the ELK components using Kubernetes network policies

## Troubleshooting

Common issues and their solutions:

### Logs Not Appearing in Kibana

1. Check Filebeat is running: `kubectl get pods -n monitoring | grep filebeat`
2. Check Logstash is receiving logs: `kubectl logs -n monitoring deployment/logstash`
3. Verify Elasticsearch indices exist: `curl -X GET "localhost:9200/_cat/indices?v"`

### Elasticsearch Not Starting

1. Check for memory issues: `kubectl describe pod -n monitoring elasticsearch-0`
2. Verify storage: `kubectl get pvc -n monitoring`

### Kibana Connection Issues

1. Verify Elasticsearch is healthy: `curl -X GET "localhost:9200/_cluster/health?pretty"`
2. Check Kibana logs: `kubectl logs -n monitoring deployment/kibana`

## Extending the Setup

### Adding New Log Patterns

To add new log sources or patterns:

1. Update the Logstash pipeline configuration in `infrastructure/elk/logstash/pipeline/maily.conf`
2. Update the Filebeat configuration in `infrastructure/elk/filebeat/filebeat.yml`
3. Restart the affected components

### Creating New Dashboards

1. Use Kibana's Discover tab to explore your data
2. Create visualizations in the Visualize tab
3. Combine visualizations into dashboards in the Dashboard tab
4. Export and import dashboards between environments using Kibana's Management section

## Monitoring the ELK Stack

The ELK stack itself is monitored with Prometheus. Metrics are exposed at:

- Elasticsearch: port 9114
- Kibana: Monitoring page in the UI
- Logstash: port 9600

## Resources

- [Elasticsearch Documentation](https://www.elastic.co/guide/en/elasticsearch/reference/current/index.html)
- [Logstash Documentation](https://www.elastic.co/guide/en/logstash/current/index.html)
- [Kibana Documentation](https://www.elastic.co/guide/en/kibana/current/index.html)
- [Filebeat Documentation](https://www.elastic.co/guide/en/beats/filebeat/current/index.html)
