# Maily Scripts Documentation

This document provides an overview of all the scripts created for the Maily project, organized by sprint and functionality.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Sprint 1: Security & Infrastructure](#sprint-1-security--infrastructure)
  - [Deploy Secrets to AWS Secrets Manager](#deploy-secrets-to-aws-secrets-manager)
  - [Enable WAF Rules in CloudFlare](#enable-waf-rules-in-cloudflare)
  - [Deploy EKS Cluster](#deploy-eks-cluster)
  - [Set up CI/CD Pipeline](#set-up-cicd-pipeline)
- [Sprint 2: Core Features & Data Storage](#sprint-2-core-features--data-storage)
  - [Complete Email Service Integration](#complete-email-service-integration)
  - [Finish Campaign Service](#finish-campaign-service)
  - [Deploy Analytics Service](#deploy-analytics-service)
  - [Set up Production RDS](#set-up-production-rds)
  - [Configure Database Backups](#configure-database-backups)
  - [Set up Redis Cluster](#set-up-redis-cluster)
- [Sprint 3: Testing & Hardening](#sprint-3-testing--hardening)
  - [Load Testing](#load-testing)
  - [Security Scanning](#security-scanning)
  - [SSL/TLS Configuration](#ssltls-configuration)
  - [DNS Configuration](#dns-configuration)
- [Verification](#verification)
  - [Verify All Scripts](#verify-all-scripts)

## Overview

These scripts automate the deployment, configuration, and management of the Maily application infrastructure and services. They are designed to be modular, reusable, and maintainable, following infrastructure-as-code best practices.

## Prerequisites

Before using these scripts, ensure you have the following tools installed:

- AWS CLI
- Terraform
- kubectl
- Helm
- jq
- curl
- git
- Docker
- Node.js and npm

Additionally, you should have appropriate credentials and access to:

- AWS account
- CloudFlare account
- GitHub repository
- Docker registry

## Sprint 1: Security & Infrastructure

### Deploy Secrets to AWS Secrets Manager

**Script**: `scripts/deploy-secrets-to-aws.sh`

**Purpose**: Securely store application secrets in AWS Secrets Manager.

**Usage**:
```bash
./scripts/deploy-secrets-to-aws.sh --region us-east-1 --env production
```

**Options**:
- `--region`: AWS region (default: us-east-1)
- `--env`: Environment (default: production)
- `--env-file`: Path to environment file (default: .env.production)
- `--prefix`: Prefix for secret names (default: maily)
- `--dry-run`: Run without making changes

### Enable WAF Rules in CloudFlare

**Script**: `scripts/deploy-cloudflare-waf.sh`

**Purpose**: Configure CloudFlare Web Application Firewall (WAF) rules for enhanced security.

**Usage**:
```bash
./scripts/deploy-cloudflare-waf.sh --api-token YOUR_API_TOKEN --zone-id YOUR_ZONE_ID
```

**Options**:
- `--api-token`: CloudFlare API token
- `--zone-id`: CloudFlare zone ID
- `--rules-file`: Path to WAF rules JSON file (default: infrastructure/cloudflare/waf-rules.json)
- `--dry-run`: Run without making changes

### Deploy EKS Cluster

**Script**: `scripts/deploy-eks-cluster.sh`

**Purpose**: Provision an Amazon EKS cluster for Kubernetes workloads.

**Usage**:
```bash
./scripts/deploy-eks-cluster.sh --region us-east-1 --cluster-name maily-production
```

**Options**:
- `--region`: AWS region (default: us-east-1)
- `--cluster-name`: EKS cluster name (default: maily-production)
- `--node-type`: EC2 instance type for worker nodes (default: t3.medium)
- `--node-count`: Number of worker nodes (default: 3)
- `--dry-run`: Run without making changes

### Set up CI/CD Pipeline

**Script**: `scripts/setup-cicd-pipeline.sh`

**Purpose**: Configure GitHub Actions for continuous integration and deployment.

**Usage**:
```bash
./scripts/setup-cicd-pipeline.sh --repo-owner your-org --repo-name maily
```

**Options**:
- `--repo-owner`: GitHub repository owner
- `--repo-name`: GitHub repository name
- `--branch`: Default branch (default: main)
- `--environments`: Comma-separated list of environments (default: staging,production)
- `--dry-run`: Run without making changes

## Sprint 2: Core Features & Data Storage

### Complete Email Service Integration

**Script**: `scripts/complete-email-service-integration.sh`

**Purpose**: Finalize the email service integration with the Maily platform.

**Usage**:
```bash
./scripts/complete-email-service-integration.sh
```

**Options**:
- `--provider`: Email service provider (default: aws-ses)
- `--region`: AWS region (default: us-east-1)
- `--dry-run`: Run without making changes

### Finish Campaign Service

**Script**: `scripts/finish-campaign-service.sh`

**Purpose**: Complete the implementation of the campaign service.

**Usage**:
```bash
./scripts/finish-campaign-service.sh
```

**Options**:
- `--dry-run`: Run without making changes

### Deploy Analytics Service

**Script**: `scripts/deploy-analytics-service.sh`

**Purpose**: Deploy the analytics service to the Kubernetes cluster.

**Usage**:
```bash
./scripts/deploy-analytics-service.sh
```

**Options**:
- `--namespace`: Kubernetes namespace (default: production)
- `--dry-run`: Run without making changes

### Set up Production RDS

**Script**: `scripts/setup-production-rds.sh`

**Purpose**: Provision and configure an Amazon RDS instance for production use.

**Usage**:
```bash
./scripts/setup-production-rds.sh --region us-east-1 --db-instance-class db.t3.medium
```

**Options**:
- `--region`: AWS region (default: us-east-1)
- `--db-instance-class`: RDS instance class (default: db.t3.medium)
- `--db-allocated-storage`: Allocated storage in GB (default: 20)
- `--db-max-allocated-storage`: Maximum storage in GB (default: 100)
- `--db-name`: Database name (default: maily)
- `--db-username`: Database username (default: maily_admin)
- `--environment`: Environment (default: production)
- `--project-name`: Project name (default: maily)
- `--dry-run`: Run without making changes

### Configure Database Backups

**Script**: `scripts/configure-database-backups.sh`

**Purpose**: Set up automated backups for the RDS database.

**Usage**:
```bash
./scripts/configure-database-backups.sh --region us-east-1 --db-instance-identifier maily-production
```

**Options**:
- `--region`: AWS region (default: us-east-1)
- `--db-instance-identifier`: RDS instance identifier (default: maily-production)
- `--backup-retention-period`: Backup retention period in days (default: 7)
- `--backup-window`: Backup window (default: 03:00-04:00)
- `--enable-automated-backups`: Enable automated backups (default: true)
- `--enable-snapshot-copy`: Enable snapshot copy to another region (default: true)
- `--snapshot-copy-region`: Region to copy snapshots to (default: us-west-2)
- `--dry-run`: Run without making changes

### Set up Redis Cluster

**Script**: `scripts/setup-redis-cluster.sh`

**Purpose**: Provision and configure an Amazon ElastiCache Redis cluster.

**Usage**:
```bash
./scripts/setup-redis-cluster.sh --region us-east-1 --cluster-name maily-redis
```

**Options**:
- `--region`: AWS region (default: us-east-1)
- `--cluster-name`: Redis cluster name (default: maily-redis)
- `--node-type`: Node type (default: cache.t3.medium)
- `--num-shards`: Number of shards (default: 2)
- `--replicas-per-shard`: Replicas per shard (default: 1)
- `--environment`: Environment (default: production)
- `--project-name`: Project name (default: maily)
- `--dry-run`: Run without making changes

## Sprint 3: Testing & Hardening

### Load Testing

**Script**: `scripts/testing/load-testing/consolidated-load-test.sh`

**Purpose**: Perform load testing on the Maily application.

**Usage**:
```bash
./scripts/testing/load-testing/consolidated-load-test.sh --api-base-url https://api.justmaily.com --test-type api
```

**Options**:
- `--api-base-url`: API base URL (default: https://api.justmaily.com)
- `--test-duration`: Test duration (default: 5m)
- `--virtual-users`: Number of virtual users (default: 50)
- `--test-type`: Test type (api, web, email) (default: api)
- `--output-format`: Output format (json, html) (default: json)
- `--output-file`: Output file (default: load-test-results.json)
- `--dry-run`: Run without making changes

### Security Scanning

**Script**: `scripts/security/security-scan.sh`

**Purpose**: Perform security scanning on the Maily application.

**Usage**:
```bash
./scripts/security/security-scan.sh --scan-type all --output-dir security-scan-results
```

**Options**:
- `--scan-type`: Scan type (all, dependency, docker, code, secret, infrastructure, api) (default: all)
- `--output-dir`: Output directory (default: security-scan-results)
- `--severity-threshold`: Severity threshold (info, low, medium, high, critical) (default: medium)
- `--scan-target`: Scan target (default: .)
- `--docker-image`: Docker image to scan
- `--api-url`: API URL to scan
- `--dry-run`: Run without making changes

### SSL/TLS Configuration

**Script**: `scripts/configure-ssl-tls.sh`

**Purpose**: Configure SSL/TLS for the Maily application.

**Usage**:
```bash
./scripts/configure-ssl-tls.sh --domain justmaily.com --environment production
```

**Options**:
- `--domain`: Domain name (default: justmaily.com)
- `--environment`: Environment (default: production)
- `--use-lets-encrypt`: Use Let's Encrypt (default: true)
- `--certificate-path`: Path to certificate file
- `--private-key-path`: Path to private key file
- `--cloudflare-api-token`: CloudFlare API token
- `--kubernetes-namespace`: Kubernetes namespace (default: default)
- `--ingress-name`: Ingress name (default: maily-ingress)
- `--dry-run`: Run without making changes

### DNS Configuration

**Script**: `scripts/configure-dns.sh`

**Purpose**: Configure DNS for the Maily application.

**Usage**:
```bash
./scripts/configure-dns.sh --domain justmaily.com --dns-provider cloudflare
```

**Options**:
- `--domain`: Domain name (default: justmaily.com)
- `--environment`: Environment (default: production)
- `--dns-provider`: DNS provider (cloudflare, route53) (default: cloudflare)
- `--cloudflare-api-token`: CloudFlare API token
- `--route53-access-key`: Route 53 access key
- `--route53-secret-key`: Route 53 secret key
- `--route53-hosted-zone-id`: Route 53 hosted zone ID
- `--load-balancer-hostname`: Load balancer hostname
- `--load-balancer-ip`: Load balancer IP
- `--dry-run`: Run without making changes

## Verification

### Verify All Scripts

**Script**: `scripts/verify-all-scripts.sh`

**Purpose**: Verify that all scripts are working properly.

**Usage**:
```bash
./scripts/verify-all-scripts.sh
```

This script performs the following checks:
1. Verifies that all scripts exist and are executable
2. Runs each script in dry-run mode to check for syntax errors
3. Validates Terraform modules
4. Validates CloudFlare WAF rules JSON
5. Validates GitHub Actions workflow YAML
6. Provides a summary of passed and failed verifications

## Conclusion

These scripts provide a comprehensive automation solution for deploying, configuring, and managing the Maily application. They follow infrastructure-as-code best practices and are designed to be modular, reusable, and maintainable.

For any issues or questions, please contact the DevOps team.
