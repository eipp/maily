#!/bin/bash

# Script to check if the required tools for the enhancement plan are installed
# and provide guidance on how to install them.

echo "Checking for required tools for the Maily enhancement plan..."
echo ""

# Security & Compliance Tools
echo "=== Security & Compliance Tools ==="

# Check for Trivy
if command -v trivy &> /dev/null; then
    echo "✅ Trivy is installed"
else
    echo "❌ Trivy is not installed"
    echo "   Install with: brew install aquasecurity/trivy/trivy"
    echo "   Or visit: https://aquasecurity.github.io/trivy/latest/getting-started/installation/"
fi

# Check for Snyk
if command -v snyk &> /dev/null; then
    echo "✅ Snyk is installed"
else
    echo "❌ Snyk is not installed"
    echo "   Install with: npm install -g snyk"
    echo "   Or visit: https://docs.snyk.io/snyk-cli/install-the-snyk-cli"
fi

# Check for OWASP ZAP
if command -v zap.sh &> /dev/null || [ -d "/Applications/OWASP ZAP.app" ]; then
    echo "✅ OWASP ZAP is installed"
else
    echo "❌ OWASP ZAP is not installed"
    echo "   Install with: brew install --cask owasp-zap"
    echo "   Or visit: https://www.zaproxy.org/download/"
fi

# Check for SonarQube (just check for Docker as we'll use Docker for SonarQube)
if command -v docker &> /dev/null; then
    echo "✅ Docker is installed (required for SonarQube)"
else
    echo "❌ Docker is not installed (required for SonarQube)"
    echo "   Install from: https://docs.docker.com/get-docker/"
fi

# Check for Vault
if command -v vault &> /dev/null; then
    echo "✅ HashiCorp Vault is installed"
else
    echo "❌ HashiCorp Vault is not installed"
    echo "   Install with: brew install vault"
    echo "   Or visit: https://developer.hashicorp.com/vault/downloads"
fi

echo ""

# Infrastructure & Scalability Tools
echo "=== Infrastructure & Scalability Tools ==="

# Check for AWS CLI
if command -v aws &> /dev/null; then
    echo "✅ AWS CLI is installed"
else
    echo "❌ AWS CLI is not installed"
    echo "   Install with: brew install awscli"
    echo "   Or visit: https://aws.amazon.com/cli/"
fi

# Check for Terraform
if command -v terraform &> /dev/null; then
    echo "✅ Terraform is installed"
else
    echo "❌ Terraform is not installed"
    echo "   Install with: brew install terraform"
    echo "   Or visit: https://developer.hashicorp.com/terraform/downloads"
fi

# Check for kubectl
if command -v kubectl &> /dev/null; then
    echo "✅ kubectl is installed"
else
    echo "❌ kubectl is not installed"
    echo "   Install with: brew install kubectl"
    echo "   Or visit: https://kubernetes.io/docs/tasks/tools/"
fi

# Check for Redis CLI
if command -v redis-cli &> /dev/null; then
    echo "✅ Redis CLI is installed"
else
    echo "❌ Redis CLI is not installed"
    echo "   Install with: brew install redis"
    echo "   Or visit: https://redis.io/download"
fi

echo ""

# AI & ML Tools
echo "=== AI & ML Tools ==="

# Check for Python
if command -v python3 &> /dev/null; then
    echo "✅ Python is installed"
else
    echo "❌ Python is not installed"
    echo "   Install with: brew install python"
    echo "   Or visit: https://www.python.org/downloads/"
fi

# Check for pip
if command -v pip3 &> /dev/null; then
    echo "✅ pip is installed"
else
    echo "❌ pip is not installed"
    echo "   Install with: brew install python"
    echo "   Or visit: https://pip.pypa.io/en/stable/installation/"
fi

# Check for DVC
if command -v dvc &> /dev/null; then
    echo "✅ DVC is installed"
else
    echo "❌ DVC is not installed"
    echo "   Install with: pip install dvc"
    echo "   Or visit: https://dvc.org/doc/install"
fi

echo ""

# Developer Experience Tools
echo "=== Developer Experience Tools ==="

# Check for Node.js
if command -v node &> /dev/null; then
    echo "✅ Node.js is installed"
else
    echo "❌ Node.js is not installed"
    echo "   Install with: brew install node"
    echo "   Or visit: https://nodejs.org/en/download/"
fi

# Check for npm
if command -v npm &> /dev/null; then
    echo "✅ npm is installed"
else
    echo "❌ npm is not installed"
    echo "   Install with: brew install node"
    echo "   Or visit: https://nodejs.org/en/download/"
fi

# Check for Playwright
if command -v playwright &> /dev/null; then
    echo "✅ Playwright is installed"
else
    echo "❌ Playwright is not installed"
    echo "   Install with: npm init playwright@latest"
    echo "   Or visit: https://playwright.dev/docs/intro"
fi

# Check for GitHub CLI
if command -v gh &> /dev/null; then
    echo "✅ GitHub CLI is installed"
else
    echo "❌ GitHub CLI is not installed"
    echo "   Install with: brew install gh"
    echo "   Or visit: https://cli.github.com/manual/installation"
fi

echo ""

# Monitoring & Observability Tools
echo "=== Monitoring & Observability Tools ==="

# Check for Prometheus
if command -v prometheus &> /dev/null; then
    echo "✅ Prometheus is installed"
else
    echo "❌ Prometheus is not installed"
    echo "   Install with: brew install prometheus"
    echo "   Or visit: https://prometheus.io/docs/prometheus/latest/installation/"
fi

# Check for Grafana
if command -v grafana-server &> /dev/null; then
    echo "✅ Grafana is installed"
else
    echo "❌ Grafana is not installed"
    echo "   Install with: brew install grafana"
    echo "   Or visit: https://grafana.com/docs/grafana/latest/installation/"
fi

echo ""

# User Experience Tools
echo "=== User Experience Tools ==="

# Check for Lighthouse
if command -v lighthouse &> /dev/null; then
    echo "✅ Lighthouse is installed"
else
    echo "❌ Lighthouse is not installed"
    echo "   Install with: npm install -g lighthouse"
    echo "   Or visit: https://developers.google.com/web/tools/lighthouse#cli"
fi

echo ""
echo "Check complete. Please install any missing tools before proceeding with the enhancement plan."
echo "For more information, see the Enhancement Tools Reference document: docs/enhancement-tools-reference.md"
