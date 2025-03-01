# Maily Diagnostics Tools Guide

## Overview

This document provides comprehensive information about Maily's diagnostics tools. These tools are designed to help identify issues and verify the correct functioning of various components in the Maily infrastructure. They can be used during development, testing, and in production environments.

## Quick Start

To run all diagnostics at once:

```bash
./tools/run_diagnostics.sh
```

To run a specific diagnostic test:

```bash
./tools/run_diagnostics.sh [blockchain|redis|api|db|security]
```

Add the `-v` flag for more detailed output:

```bash
./tools/run_diagnostics.sh -v redis
```

## Available Diagnostic Tools

### Blockchain Diagnostics

Tests the blockchain integration, including provider connectivity, smart contract validity, and transaction capabilities.

**What it tests:**
- Blockchain service configuration
- Connection to blockchain provider
- Smart contract validity and accessibility
- Account setup and balance
- Network status and gas price

**How to run:**
```bash
./tools/run_diagnostics.sh blockchain
```

**Direct script usage:**
```bash
python3 tools/blockchain_diagnostics.py --format json --output results.json
```

### Redis Diagnostics

Tests Redis connectivity, performance, memory usage, and caching configuration.

**What it tests:**
- Redis connection and configuration
- Memory usage and fragmentation
- Key space usage
- Persistence configuration
- Performance benchmarks
- Eviction and expiry policy
- Cache hit rate

**How to run:**
```bash
./tools/run_diagnostics.sh redis
```

**Direct script usage:**
```bash
python3 tools/redis_diagnostics.py --format json --output results.json
```

### API Diagnostics

Validates API endpoints, authentication, rate limiting, and performance.

**What it tests:**
- API availability and response times
- Authentication and authorization
- Rate limiting functionality
- Error handling
- Endpoint validation

**How to run:**
```bash
./tools/run_diagnostics.sh api
```

### Database Diagnostics

Checks database connectivity, performance, and structure.

**What it tests:**
- Database connection
- Query performance
- Schema validation
- Index usage
- Database health metrics

**How to run:**
```bash
./tools/run_diagnostics.sh db
```

### Security Diagnostics

Verifies security configurations, headers, and policies.

**What it tests:**
- Security headers
- TLS configuration
- CORS settings
- Authentication security
- Input validation

**How to run:**
```bash
./tools/run_diagnostics.sh security
```

## Configuration

Diagnostics use environment variables from your current environment. For production diagnostics, ensure you have the necessary production environment variables set.

Key environment variables that affect diagnostics:

- `BLOCKCHAIN_ENABLED`: Enables/disables blockchain testing
- `BLOCKCHAIN_PROVIDER_URL`: Blockchain provider URL for testing
- `REDIS_URL`: Redis connection string
- `REDIS_SSL`: Whether Redis uses SSL
- `API_URL`: API base URL for testing
- `DATABASE_URL`: Database connection string

## Interpreting Results

Diagnostic results are stored in the `./diagnostic_reports/` directory with the following structure:

- `diagnostics_summary_[timestamp].txt`: Overall summary of all tests
- `blockchain_diagnostics.json`: Detailed blockchain test results
- `redis_diagnostics.json`: Detailed Redis test results

Each test result is categorized as:
- **PASSED**: Test completed successfully
- **WARNING**: Test completed but with potential issues detected
- **FAILED**: Test failed or identified critical issues
- **SKIPPED**: Test was skipped (typically due to configuration)

### Understanding Warning vs. Failure

- **Warnings** indicate potential issues that might require attention but don't necessarily indicate system failure (e.g., high memory usage, suboptimal configuration)
- **Failures** indicate critical issues that likely require immediate attention (e.g., connection failures, invalid configuration)

## Adding New Diagnostics

To add a new diagnostic test:

1. Create a new Python script in the `tools/` directory following the pattern of existing scripts
2. Implement a class that performs the diagnostics and reports results
3. Add a corresponding function to `run_diagnostics.sh`
4. Update the main function in `run_diagnostics.sh` to include your new test

## Scheduling Regular Diagnostics

For production systems, it's recommended to schedule regular diagnostic runs:

### Using Cron

```bash
# Run diagnostics daily at 2 AM and save results
0 2 * * * cd /path/to/maily && ./tools/run_diagnostics.sh > /var/log/maily/diagnostics.log 2>&1
```

### Kubernetes CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: maily-diagnostics
spec:
  schedule: "0 2 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: diagnostics
            image: maily/api:latest
            command: ["/bin/sh", "-c", "./tools/run_diagnostics.sh"]
          restartPolicy: OnFailure
```

## Troubleshooting

### Common Issues

#### Python Dependencies

If you encounter Python module errors, ensure all dependencies are installed:

```bash
pip install -r requirements.txt
```

#### Permission Issues

Ensure the diagnostic scripts are executable:

```bash
chmod +x tools/run_diagnostics.sh
```

#### Environment Configuration

Most diagnostic failures stem from incorrect environment configuration. Verify your environment variables match your target environment.

## Integrating with Monitoring

The diagnostics output can be integrated with monitoring systems:

### Prometheus Integration

Use the `--format json` option and a parsing script to convert diagnostics results to Prometheus metrics.

### Grafana Dashboard

A sample Grafana dashboard for visualizing diagnostics is available in `monitoring/grafana/dashboards/diagnostics.json`.

## Best Practices

1. Run full diagnostics after any major deployment
2. Schedule regular diagnostics in production environments
3. Compare results over time to identify trends
4. Address warnings before they become failures
5. Use diagnostics as a pre-check before significant operations

## Support

For issues or enhancements to the diagnostics tools, please open an issue in the repository with the tag `diagnostics`.
