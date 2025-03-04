#!/bin/bash
# setup-datadog-monitoring.sh
# Script to set up Datadog monitoring for Maily with focus on AI and blockchain components

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}======================================================${NC}"
echo -e "${GREEN}Maily Datadog Monitoring Setup${NC}"
echo -e "${GREEN}======================================================${NC}"
echo ""

# Check for required command line tools
check_commands() {
  echo -e "${GREEN}Checking for required command line tools...${NC}"
  
  local REQUIRED_COMMANDS=("kubectl" "helm" "jq")
  local MISSING_COMMANDS=()
  
  for cmd in "${REQUIRED_COMMANDS[@]}"; do
    if ! command -v "$cmd" &> /dev/null; then
      MISSING_COMMANDS+=("$cmd")
    fi
  done
  
  if [ ${#MISSING_COMMANDS[@]} -ne 0 ]; then
    echo -e "${RED}The following required commands are missing:${NC}"
    for cmd in "${MISSING_COMMANDS[@]}"; do
      echo -e "${RED}- $cmd${NC}"
    done
    echo ""
    echo -e "Please install these tools before continuing."
    exit 1
  fi
  
  echo -e "${GREEN}✓ All required tools are installed${NC}"
  echo ""
}

# Check for Datadog API key
check_datadog_api_key() {
  echo -e "${GREEN}Checking for Datadog API key...${NC}"
  
  if [ -z "${DATADOG_API_KEY}" ]; then
    echo -e "${YELLOW}DATADOG_API_KEY environment variable is not set.${NC}"
    
    read -p "Would you like to enter your Datadog API key now? (y/n): " ENTER_API_KEY
    if [[ "$ENTER_API_KEY" == "y" || "$ENTER_API_KEY" == "Y" ]]; then
      read -sp "Enter your Datadog API key: " DATADOG_API_KEY
      echo ""
      export DATADOG_API_KEY
    else
      echo -e "${RED}Datadog API key is required for monitoring setup.${NC}"
      exit 1
    fi
  fi
  
  echo -e "${GREEN}✓ Datadog API key is set${NC}"
  echo ""
}

# Check for Datadog RUM configuration
check_datadog_rum_config() {
  echo -e "${GREEN}Checking for Datadog RUM configuration...${NC}"
  
  if [ -z "${DATADOG_RUM_APP_ID}" ] || [ -z "${DATADOG_RUM_CLIENT_TOKEN}" ]; then
    echo -e "${YELLOW}DATADOG_RUM_APP_ID or DATADOG_RUM_CLIENT_TOKEN environment variables are not set.${NC}"
    
    read -p "Would you like to enter your Datadog RUM configuration now? (y/n): " ENTER_RUM_CONFIG
    if [[ "$ENTER_RUM_CONFIG" == "y" || "$ENTER_RUM_CONFIG" == "Y" ]]; then
      read -p "Enter your Datadog RUM Application ID: " DATADOG_RUM_APP_ID
      read -sp "Enter your Datadog RUM Client Token: " DATADOG_RUM_CLIENT_TOKEN
      echo ""
      export DATADOG_RUM_APP_ID
      export DATADOG_RUM_CLIENT_TOKEN
    else
      echo -e "${YELLOW}Datadog RUM configuration is not set. RUM features will be disabled.${NC}"
      export DATADOG_RUM_APP_ID="disabled"
      export DATADOG_RUM_CLIENT_TOKEN="disabled"
    fi
  fi
  
  echo -e "${GREEN}✓ Datadog RUM configuration is set${NC}"
  echo ""
}

# Create Kubernetes namespace for monitoring
create_monitoring_namespace() {
  echo -e "${GREEN}Creating Kubernetes namespace for monitoring...${NC}"
  
  kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
  
  echo -e "${GREEN}✓ Created monitoring namespace${NC}"
  echo ""
}

# Create Kubernetes secret for Datadog API key
create_datadog_secret() {
  echo -e "${GREEN}Creating Kubernetes secret for Datadog API key...${NC}"
  
  kubectl create secret generic datadog-secret \
    --from-literal=api-key=${DATADOG_API_KEY} \
    --from-literal=app-key=${DATADOG_APP_KEY:-""} \
    --namespace=monitoring \
    --dry-run=client -o yaml | kubectl apply -f -
  
  echo -e "${GREEN}✓ Created Datadog secret${NC}"
  echo ""
}

# Create Kubernetes secret for Datadog RUM configuration
create_datadog_rum_secret() {
  echo -e "${GREEN}Creating Kubernetes secret for Datadog RUM configuration...${NC}"
  
  kubectl create secret generic datadog-rum-secret \
    --from-literal=rum-app-id=${DATADOG_RUM_APP_ID} \
    --from-literal=rum-client-token=${DATADOG_RUM_CLIENT_TOKEN} \
    --namespace=monitoring \
    --dry-run=client -o yaml | kubectl apply -f -
  
  echo -e "${GREEN}✓ Created Datadog RUM secret${NC}"
  echo ""
}

# Create Kubernetes ConfigMap for Datadog compliance checks
create_datadog_compliance_configmap() {
  echo -e "${GREEN}Creating Kubernetes ConfigMap for Datadog compliance checks...${NC}"
  
  cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: datadog-compliance
  namespace: monitoring
data:
  compliance.yaml: |
    compliance_checks:
      kubernetes:
        - name: "CIS-Kubernetes"
          enabled: true
      docker:
        - name: "CIS-Docker"
          enabled: true
      custom:
        - name: "GDPR"
          enabled: true
        - name: "SOC2"
          enabled: true
        - name: "CCPA"
          enabled: true
EOF
  
  echo -e "${GREEN}✓ Created Datadog compliance ConfigMap${NC}"
  echo ""
}

# Create Kubernetes ConfigMap for Datadog security policies
create_datadog_security_configmap() {
  echo -e "${GREEN}Creating Kubernetes ConfigMap for Datadog security policies...${NC}"
  
  cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: datadog-security
  namespace: monitoring
data:
  security-policies.yaml: |
    policies:
      - name: "Detect privilege escalation"
        enabled: true
        rules:
          - id: "privilege_escalation"
            expression: "process.cap.effective.includes('CAP_SYS_ADMIN')"
      - name: "Detect unauthorized network connections"
        enabled: true
        rules:
          - id: "unauthorized_connection"
            expression: "network.protocol == 'tcp' && !network.destination.ip.in(['10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16'])"
      - name: "Detect sensitive file access"
        enabled: true
        rules:
          - id: "sensitive_file_access"
            expression: "file.path.startswith('/etc/') && file.path.endswith('.conf') && process.name != 'root'"
EOF
  
  echo -e "${GREEN}✓ Created Datadog security ConfigMap${NC}"
  echo ""
}

# Create Kubernetes ConfigMap for Datadog synthetics
create_datadog_synthetics_configmap() {
  echo -e "${GREEN}Creating Kubernetes ConfigMap for Datadog synthetics...${NC}"
  
  cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: ConfigMap
metadata:
  name: datadog-synthetics
  namespace: monitoring
data:
  synthetics.yaml: |
    synthetics:
      - name: "API Health Check"
        type: "api"
        request:
          url: "https://api.justmaily.com/health"
          method: "GET"
          timeout: 30
        assertions:
          - type: "statusCode"
            operator: "is"
            target: 200
        locations:
          - "aws:us-east-1"
          - "aws:eu-west-1"
        options:
          tick_every: 60
          min_failure_duration: 300
          min_location_failed: 1
      - name: "Web App Health Check"
        type: "browser"
        request:
          url: "https://justmaily.com"
          method: "GET"
        assertions:
          - type: "statusCode"
            operator: "is"
            target: 200
        locations:
          - "aws:us-east-1"
          - "aws:eu-west-1"
        options:
          tick_every: 300
          min_failure_duration: 600
          min_location_failed: 1
EOF
  
  echo -e "${GREEN}✓ Created Datadog synthetics ConfigMap${NC}"
  echo ""
}

# Install Datadog Helm chart
install_datadog() {
  echo -e "${GREEN}Installing Datadog Helm chart...${NC}"
  
  # Add Datadog Helm repository
  helm repo add datadog https://helm.datadoghq.com
  helm repo update
  
  # Process the values file to replace environment variables
  envsubst < "$(dirname "$0")/../kubernetes/monitoring/datadog-values.yaml" > /tmp/datadog-values.yaml
  
  # Install Datadog Helm chart
  helm upgrade --install datadog datadog/datadog \
    --namespace monitoring \
    -f /tmp/datadog-values.yaml
  
  echo -e "${GREEN}✓ Installed Datadog Helm chart${NC}"
  echo ""
}

# Create Datadog dashboard for AI services
create_ai_dashboard() {
  echo -e "${GREEN}Creating Datadog dashboard for AI services...${NC}"
  
  if [ -z "${DATADOG_APP_KEY}" ]; then
    echo -e "${YELLOW}DATADOG_APP_KEY environment variable is not set. Skipping dashboard creation.${NC}"
    return
  fi
  
  # Create dashboard JSON
  cat <<EOF > /tmp/ai-dashboard.json
{
  "title": "Maily AI Services Dashboard",
  "description": "Dashboard for monitoring Maily AI services",
  "widgets": [
    {
      "definition": {
        "type": "timeseries",
        "title": "AI Request Count",
        "requests": [
          {
            "q": "sum:maily.ai_request_count{service:ai} by {model}",
            "display_type": "line"
          }
        ]
      }
    },
    {
      "definition": {
        "type": "timeseries",
        "title": "AI Request Latency",
        "requests": [
          {
            "q": "avg:maily.ai_request_latency{service:ai} by {model}",
            "display_type": "line"
          }
        ]
      }
    },
    {
      "definition": {
        "type": "timeseries",
        "title": "AI Token Usage",
        "requests": [
          {
            "q": "sum:maily.ai_token_usage{service:ai} by {model}",
            "display_type": "area"
          }
        ]
      }
    },
    {
      "definition": {
        "type": "timeseries",
        "title": "AI Model Performance",
        "requests": [
          {
            "q": "avg:maily.ai_model_performance{service:ai} by {model}",
            "display_type": "line"
          }
        ]
      }
    },
    {
      "definition": {
        "type": "timeseries",
        "title": "AI Error Rate",
        "requests": [
          {
            "q": "sum:maily.ai_error_rate{service:ai} by {model}",
            "display_type": "line"
          }
        ]
      }
    }
  ],
  "layout_type": "ordered"
}
EOF
  
  # Create dashboard using Datadog API
  curl -X POST -H "Content-type: application/json" \
    -H "DD-API-KEY: ${DATADOG_API_KEY}" \
    -H "DD-APPLICATION-KEY: ${DATADOG_APP_KEY}" \
    -d @/tmp/ai-dashboard.json \
    "https://api.datadoghq.com/api/v1/dashboard"
  
  echo -e "${GREEN}✓ Created Datadog dashboard for AI services${NC}"
  echo ""
}

# Create Datadog dashboard for blockchain services
create_blockchain_dashboard() {
  echo -e "${GREEN}Creating Datadog dashboard for blockchain services...${NC}"
  
  if [ -z "${DATADOG_APP_KEY}" ]; then
    echo -e "${YELLOW}DATADOG_APP_KEY environment variable is not set. Skipping dashboard creation.${NC}"
    return
  fi
  
  # Create dashboard JSON
  cat <<EOF > /tmp/blockchain-dashboard.json
{
  "title": "Maily Blockchain Services Dashboard",
  "description": "Dashboard for monitoring Maily blockchain services",
  "widgets": [
    {
      "definition": {
        "type": "timeseries",
        "title": "Blockchain Transaction Count",
        "requests": [
          {
            "q": "sum:maily.blockchain_transaction_count{service:blockchain} by {contract}",
            "display_type": "line"
          }
        ]
      }
    },
    {
      "definition": {
        "type": "timeseries",
        "title": "Blockchain Gas Used",
        "requests": [
          {
            "q": "sum:maily.blockchain_gas_used{service:blockchain} by {contract}",
            "display_type": "area"
          }
        ]
      }
    },
    {
      "definition": {
        "type": "timeseries",
        "title": "Blockchain Block Time",
        "requests": [
          {
            "q": "avg:maily.blockchain_block_time{service:blockchain}",
            "display_type": "line"
          }
        ]
      }
    },
    {
      "definition": {
        "type": "timeseries",
        "title": "Blockchain Contract Calls",
        "requests": [
          {
            "q": "sum:maily.blockchain_contract_calls{service:blockchain} by {contract,method}",
            "display_type": "line"
          }
        ]
      }
    },
    {
      "definition": {
        "type": "timeseries",
        "title": "Blockchain Error Rate",
        "requests": [
          {
            "q": "sum:maily.blockchain_error_rate{service:blockchain} by {contract}",
            "display_type": "line"
          }
        ]
      }
    }
  ],
  "layout_type": "ordered"
}
EOF
  
  # Create dashboard using Datadog API
  curl -X POST -H "Content-type: application/json" \
    -H "DD-API-KEY: ${DATADOG_API_KEY}" \
    -H "DD-APPLICATION-KEY: ${DATADOG_APP_KEY}" \
    -d @/tmp/blockchain-dashboard.json \
    "https://api.datadoghq.com/api/v1/dashboard"
  
  echo -e "${GREEN}✓ Created Datadog dashboard for blockchain services${NC}"
  echo ""
}

# Create Datadog dashboard for WebSocket services
create_websocket_dashboard() {
  echo -e "${GREEN}Creating Datadog dashboard for WebSocket services...${NC}"
  
  if [ -z "${DATADOG_APP_KEY}" ]; then
    echo -e "${YELLOW}DATADOG_APP_KEY environment variable is not set. Skipping dashboard creation.${NC}"
    return
  fi
  
  # Create dashboard JSON
  cat <<EOF > /tmp/websocket-dashboard.json
{
  "title": "Maily WebSocket Services Dashboard",
  "description": "Dashboard for monitoring Maily WebSocket services",
  "widgets": [
    {
      "definition": {
        "type": "timeseries",
        "title": "WebSocket Connection Count",
        "requests": [
          {
            "q": "sum:maily.websocket_connection_count{service:websocket}",
            "display_type": "line"
          }
        ]
      }
    },
    {
      "definition": {
        "type": "timeseries",
        "title": "WebSocket Message Rate",
        "requests": [
          {
            "q": "sum:maily.websocket_message_rate{service:websocket,direction:inbound}",
            "display_type": "line",
            "name": "Inbound"
          },
          {
            "q": "sum:maily.websocket_message_rate{service:websocket,direction:outbound}",
            "display_type": "line",
            "name": "Outbound"
          }
        ]
      }
    },
    {
      "definition": {
        "type": "timeseries",
        "title": "WebSocket Error Rate",
        "requests": [
          {
            "q": "sum:maily.websocket_error_rate{service:websocket} by {error_type}",
            "display_type": "line"
          }
        ]
      }
    },
    {
      "definition": {
        "type": "timeseries",
        "title": "WebSocket Latency",
        "requests": [
          {
            "q": "avg:maily.websocket_latency{service:websocket}",
            "display_type": "line"
          }
        ]
      }
    }
  ],
  "layout_type": "ordered"
}
EOF
  
  # Create dashboard using Datadog API
  curl -X POST -H "Content-type: application/json" \
    -H "DD-API-KEY: ${DATADOG_API_KEY}" \
    -H "DD-APPLICATION-KEY: ${DATADOG_APP_KEY}" \
    -d @/tmp/websocket-dashboard.json \
    "https://api.datadoghq.com/api/v1/dashboard"
  
  echo -e "${GREEN}✓ Created Datadog dashboard for WebSocket services${NC}"
  echo ""
}

# Create Datadog monitors for AI services
create_ai_monitors() {
  echo -e "${GREEN}Creating Datadog monitors for AI services...${NC}"
  
  if [ -z "${DATADOG_APP_KEY}" ]; then
    echo -e "${YELLOW}DATADOG_APP_KEY environment variable is not set. Skipping monitor creation.${NC}"
    return
  fi
  
  # Create monitor for AI service health
  curl -X POST -H "Content-type: application/json" \
    -H "DD-API-KEY: ${DATADOG_API_KEY}" \
    -H "DD-APPLICATION-KEY: ${DATADOG_APP_KEY}" \
    -d '{
      "name": "Maily AI Service Health",
      "type": "service check",
      "query": "\"ai_service_check\".over(\"service:ai\").by(\"host\").last(3).count_by_status()",
      "message": "Maily AI Service is not responding. @slack-maily-alerts",
      "tags": ["service:ai", "env:production"],
      "options": {
        "thresholds": {
          "critical": 3,
          "warning": 2,
          "ok": 1
        },
        "notify_no_data": true,
        "no_data_timeframe": 10,
        "new_host_delay": 300,
        "notify_audit": false,
        "timeout_h": 0,
        "include_tags": true
      }
    }' \
    "https://api.datadoghq.com/api/v1/monitor"
  
  # Create monitor for AI service latency
  curl -X POST -H "Content-type: application/json" \
    -H "DD-API-KEY: ${DATADOG_API_KEY}" \
    -H "DD-APPLICATION-KEY: ${DATADOG_APP_KEY}" \
    -d '{
      "name": "Maily AI Service High Latency",
      "type": "metric alert",
      "query": "avg(last_5m):avg:maily.ai_request_latency{service:ai} by {model} > 2000",
      "message": "Maily AI Service is experiencing high latency. @slack-maily-alerts",
      "tags": ["service:ai", "env:production"],
      "options": {
        "thresholds": {
          "critical": 2000,
          "warning": 1000
        },
        "notify_no_data": false,
        "new_host_delay": 300,
        "notify_audit": false,
        "timeout_h": 0,
        "include_tags": true
      }
    }' \
    "https://api.datadoghq.com/api/v1/monitor"
  
  # Create monitor for AI service error rate
  curl -X POST -H "Content-type: application/json" \
    -H "DD-API-KEY: ${DATADOG_API_KEY}" \
    -H "DD-APPLICATION-KEY: ${DATADOG_APP_KEY}" \
    -d '{
      "name": "Maily AI Service High Error Rate",
      "type": "metric alert",
      "query": "avg(last_5m):sum:maily.ai_error_rate{service:ai} by {model} > 0.05",
      "message": "Maily AI Service is experiencing a high error rate. @slack-maily-alerts",
      "tags": ["service:ai", "env:production"],
      "options": {
        "thresholds": {
          "critical": 0.05,
          "warning": 0.02
        },
        "notify_no_data": false,
        "new_host_delay": 300,
        "notify_audit": false,
        "timeout_h": 0,
        "include_tags": true
      }
    }' \
    "https://api.datadoghq.com/api/v1/monitor"
  
  echo -e "${GREEN}✓ Created Datadog monitors for AI services${NC}"
  echo ""
}

# Create Datadog monitors for blockchain services
create_blockchain_monitors() {
  echo -e "${GREEN}Creating Datadog monitors for blockchain services...${NC}"
  
  if [ -z "${DATADOG_APP_KEY}" ]; then
    echo -e "${YELLOW}DATADOG_APP_KEY environment variable is not set. Skipping monitor creation.${NC}"
    return
  fi
  
  # Create monitor for blockchain service health
  curl -X POST -H "Content-type: application/json" \
    -H "DD-API-KEY: ${DATADOG_API_KEY}" \
    -H "DD-APPLICATION-KEY: ${DATADOG_APP_KEY}" \
    -d '{
      "name": "Maily Blockchain Service Health",
      "type": "service check",
      "query": "\"blockchain_service_check\".over(\"service:blockchain\").by(\"host\").last(3).count_by_status()",
      "message": "Maily Blockchain Service is not responding. @slack-maily-alerts",
      "tags": ["service:blockchain", "env:production"],
      "options": {
        "thresholds": {
          "critical": 3,
          "warning": 2,
          "ok": 1
        },
        "notify_no_data": true,
        "no_data_timeframe": 10,
        "new_host_delay": 300,
        "notify_audit": false,
        "timeout_h": 0,
        "include_tags": true
      }
    }' \
    "https://api.datadoghq.com/api/v1/monitor"
  
  # Create monitor for blockchain service error rate
  curl -X POST -H "Content-type: application/json" \
    -H "DD-API-KEY: ${DATADOG_API_KEY}" \
    -H "DD-APPLICATION-KEY: ${DATADOG_APP_KEY}" \
    -d '{
      "name": "Maily Blockchain Service High Error Rate",
      "type": "metric alert",
      "query": "avg(last_5m):sum:maily.blockchain_error_rate{service:blockchain} by {contract} > 0.05",
      "message": "Maily Blockchain Service is experiencing a high error rate. @slack-maily-alerts",
      "tags": ["service:blockchain", "env:production"],
      "options": {
        "thresholds": {
          "critical": 0.05,
          "warning": 0.02
        },
        "notify_no_data": false,
        "new_host_delay": 300,
        "notify_audit": false,
        "timeout_h": 0,
        "include_tags": true
      }
    }' \
    "https://api.datadoghq.com/api/v1/monitor"
  
  # Create monitor for blockchain gas usage
  curl -X POST -H "Content-type: application/json" \
    -H "DD-API-KEY: ${DATADOG_API_KEY}" \
    -H "DD-APPLICATION-KEY: ${DATADOG_APP_KEY}" \
    -d '{
      "name": "Maily Blockchain Service High Gas Usage",
      "type": "metric alert",
      "query": "avg(last_15m):sum:maily.blockchain_gas_used{service:blockchain} > 1000000",
      "message": "Maily Blockchain Service is experiencing high gas usage. @slack-maily-alerts",
      "tags": ["service:blockchain", "env:production"],
      "options": {
        "thresholds": {
          "critical": 1000000,
          "warning": 500000
        },
        "notify_no_data": false,
        "new_host_delay": 300,
        "notify_audit": false,
        "timeout_h": 0,
        "include_tags": true
      }
    }' \
    "https://api.datadoghq.com/api/v1/monitor"
  
  echo -e "${GREEN}✓ Created Datadog monitors for blockchain services${NC}"
  echo ""
}

# Create Datadog monitors for WebSocket services
create_websocket_monitors() {
  echo -e "${GREEN}Creating Datadog monitors for WebSocket services...${NC}"
  
  if [ -z "${DATADOG_APP_KEY}" ]; then
    echo -e "${YELLOW}DATADOG_APP_KEY environment variable is not set. Skipping monitor creation.${NC}"
    return
  fi
  
  # Create monitor for WebSocket service health
  curl -X POST -H "Content-type: application/json" \
    -H "DD-API-KEY: ${DATADOG_API_KEY}" \
    -H "DD-APPLICATION-KEY: ${DATADOG_APP_KEY}" \
    -d '{
      "name": "Maily WebSocket Service Health",
      "type": "service check",
      "query": "\"websocket_service_check\".over(\"service:websocket\").by(\"host\").last(3).count_by_status()",
      "message": "Maily WebSocket Service is not responding. @slack-maily-alerts",
      "tags": ["service:websocket", "env:production"],
      "options": {
        "thresholds": {
          "critical": 3,
          "warning": 2,
          "ok": 1
        },
        "notify_no_data": true,
        "no_data_timeframe": 10,
        "new_host_delay": 300,
        "notify_audit": false,
        "timeout_h": 0,
        "include_tags": true
      }
    }' \
    "https://api.datadoghq.com/api/v1/monitor"
  
  # Create monitor for WebSocket connection count
  curl -X POST -H "Content-type: application/json" \
    -H "DD-API-KEY: ${DATADOG_API_KEY}" \
    -H "DD-APPLICATION-KEY: ${DATADOG_APP_KEY}" \
    -d '{
      "name": "Maily WebSocket Service Connection Count",
      "type": "metric alert",
      "query": "avg(last_5m):sum:maily.websocket_connection_count{service:websocket} > 10000",
      "message": "Maily WebSocket Service has a high number of connections. @slack-maily-alerts",
      "tags": ["service:websocket", "env:production"],
      "options": {
        "thresholds": {
          "critical": 10000,
          "warning": 8000
        },
        "notify_no_data": false,
        "new_host_delay": 300,
        "notify_audit": false,
        "timeout_h": 0,
        "include_tags": true
      }
    }' \
    "https://api.datadoghq.com/api/v1/monitor"
  
  # Create monitor for WebSocket error rate
  curl -X POST -H "Content-type: application/json" \
    -H "DD-API-KEY: ${DATADOG_API_KEY}" \
    -H "DD-APPLICATION-KEY: ${DATADOG_APP_KEY}" \
    -d '{
      "name": "Maily WebSocket Service High Error Rate",
      "type": "metric alert",
      "query": "avg(last_5m):sum:maily.websocket_error_rate{service:websocket} > 0.05",
      "message": "Maily WebSocket Service is experiencing a high error rate. @slack-maily-alerts",
      "tags": ["service:websocket", "env:production"],
      "options": {
        "thresholds": {
          "critical": 0.05,
          "warning": 0.02
        },
        "notify_no_data": false,
        "new_host_delay": 300,
        "notify_audit": false,
        "timeout_h": 0,
        "include_tags": true
      }
    }' \
    "https://api.datadoghq.com/api/v1/monitor"
  
  echo -e "${GREEN}✓ Created Datadog monitors for WebSocket services${NC}"
  echo ""
}

# Main function
main() {
  check_commands
  check_datadog_api_key
  check_datadog_rum_config
  create_monitoring_namespace
  create_datadog_secret
  create_datadog_rum_secret
  create_datadog_compliance_configmap
  create_datadog_security_configmap
  create_datadog_synthetics_configmap
  install_datadog
  create_ai_dashboard
  create_blockchain_dashboard
  create_websocket_dashboard
  create_ai_monitors
  create_blockchain_monitors
  create_websocket_monitors
  
  echo -e "${GREEN}======================================================${NC}"
  echo -e "${GREEN}Datadog Monitoring Setup Complete${NC}"
  echo -e "${GREEN}======================================================${NC}"
  echo ""
  echo -e "Next steps:"
  echo -e "1. Log in to the Datadog dashboard to verify the installation"
  echo -e "2. Configure additional monitors and dashboards as needed"
  echo -e "3. Set up notification channels for alerts"
  echo -e "4. Verify that metrics are being collected from all services"
  echo ""
}

# Run the script
main
