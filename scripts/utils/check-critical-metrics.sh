#!/bin/bash
set -e

# Maily Critical Metrics Check Script
# This script checks critical production metrics using Datadog API

# Color codes for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}Checking Maily Critical Production Metrics${NC}"
echo "Timestamp: $(date)"

# Check for required environment variables
if [ -z "$DATADOG_API_KEY" ] || [ -z "$DATADOG_APP_KEY" ]; then
    # Try to load from .env file
    if [ -f ".env.production" ]; then
        export $(grep -v '^#' .env.production | grep "DATADOG_" | xargs)
    fi
    
    # Check again
    if [ -z "$DATADOG_API_KEY" ] || [ -z "$DATADOG_APP_KEY" ]; then
        echo -e "${RED}Error: DATADOG_API_KEY and DATADOG_APP_KEY environment variables are required.${NC}"
        exit 1
    fi
fi

# Check for curl
command -v curl >/dev/null 2>&1 || { echo -e "${RED}Error: curl is required but not installed. Aborting.${NC}"; exit 1; }
command -v jq >/dev/null 2>&1 || { echo -e "${RED}Error: jq is required but not installed. Aborting.${NC}"; exit 1; }

# Datadog API base URL
DD_API_URL="https://api.datadoghq.eu/api/v1"

# Get metrics function
get_metric() {
    local metric=$1
    local query=$2
    local from=$3
    local to=$4
    
    echo -e "${YELLOW}Checking ${metric}...${NC}"
    
    # Construct API URL with proper URI encoding
    local encoded_query=$(echo $query | sed 's/ /%20/g' | sed 's/\[/%5B/g' | sed 's/\]/%5D/g' | sed "s/'/%27/g" | sed 's/:/%3A/g' | sed 's/,/%2C/g')
    local url="${DD_API_URL}/query?from=${from}&to=${to}&query=${encoded_query}"
    
    # Make API request
    local response=$(curl -s -X GET "$url" \
        -H "Content-Type: application/json" \
        -H "DD-API-KEY: ${DATADOG_API_KEY}" \
        -H "DD-APPLICATION-KEY: ${DATADOG_APP_KEY}")
    
    # Check for errors
    if echo "$response" | jq -e '.errors' >/dev/null; then
        echo -e "${RED}Error checking ${metric}:${NC}"
        echo "$response" | jq '.errors'
        return 1
    fi
    
    # Get the latest value
    local values=$(echo "$response" | jq -r '.series[0].pointlist[-1][1]')
    
    if [ "$values" = "null" ] || [ -z "$values" ]; then
        echo -e "${YELLOW}No data available for ${metric}${NC}"
        return 0
    fi
    
    # Format value
    local formatted_value=$(printf "%.2f" $values)
    
    echo -e "${GREEN}${metric}: ${formatted_value}${NC}"
    
    # Return value for thresholds
    echo "$formatted_value"
}

# Current time in seconds since epoch
now=$(date +%s)
# 1 hour ago
hour_ago=$((now - 3600))

echo "Checking metrics from $(date -r $hour_ago) to $(date)"

# Check API error rate
api_error_rate=$(get_metric "API Error Rate (%)" "sum:maily.api.errors{*}.as_count() / sum:maily.api.requests{*}.as_count() * 100" "$hour_ago" "$now")
if (( $(echo "$api_error_rate > 5" | bc -l) )); then
    echo -e "${RED}⚠️ API Error Rate is high: ${api_error_rate}% (threshold: 5%)${NC}"
fi

# Check API response time
api_response_time=$(get_metric "API Response Time (ms)" "p95:maily.api.response.time{*}" "$hour_ago" "$now")
if (( $(echo "$api_response_time > 1000" | bc -l) )); then
    echo -e "${RED}⚠️ API Response Time is high: ${api_response_time}ms (threshold: 1000ms)${NC}"
fi

# Check AI service response time
ai_response_time=$(get_metric "AI Service Response Time (ms)" "p95:maily.ai.response.time{*}" "$hour_ago" "$now")
if (( $(echo "$ai_response_time > 5000" | bc -l) )); then
    echo -e "${RED}⚠️ AI Response Time is high: ${ai_response_time}ms (threshold: 5000ms)${NC}"
fi

# Check blockchain verification success rate
blockchain_success=$(get_metric "Blockchain Verification Success Rate (%)" "sum:maily.blockchain.verification.success{*}.as_count() / sum:maily.blockchain.verification.total{*}.as_count() * 100" "$hour_ago" "$now")
if (( $(echo "$blockchain_success < 95" | bc -l) )); then
    echo -e "${RED}⚠️ Blockchain Verification Success Rate is low: ${blockchain_success}% (threshold: 95%)${NC}"
fi

# Check Redis operation latency
redis_latency=$(get_metric "Redis Operation Latency (ms)" "avg:redis.command.latency{*}" "$hour_ago" "$now")
if (( $(echo "$redis_latency > 10" | bc -l) )); then
    echo -e "${RED}⚠️ Redis Operation Latency is high: ${redis_latency}ms (threshold: 10ms)${NC}"
fi

echo -e "\n${GREEN}Metric check completed.${NC}"
echo "For detailed metrics, visit: https://app.datadoghq.eu/dashboard/maily-production"