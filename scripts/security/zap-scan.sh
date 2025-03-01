#!/bin/bash

# OWASP ZAP Automated Security Scan
# Usage: ./zap-scan.sh [environment]

ENV=${1:-staging}
BASE_URL="https://app.justmaily.com"
if [ "$ENV" = "staging" ]; then
  BASE_URL="https://staging.justmaily.com"
fi

# Create output directory
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="security_reports/${TIMESTAMP}"
mkdir -p $OUTPUT_DIR

echo "Starting ZAP scan for $BASE_URL"

# Start ZAP daemon
docker run -d --name zap \
  -v $(pwd)/${OUTPUT_DIR}:/zap/wrk/:rw \
  -t owasp/zap2docker-stable zap.sh \
  -daemon \
  -host 0.0.0.0 \
  -port 2375 \
  -config api.key=justmaily-zap-key

# Wait for ZAP to start
sleep 30

# Run Spider scan
docker exec zap zap-cli --api-key justmaily-zap-key spider $BASE_URL
docker exec zap zap-cli --api-key justmaily-zap-key wait-for-passive-scan

# Run Active Scan
docker exec zap zap-cli --api-key justmaily-zap-key active-scan \
  --recursive \
  --scanners all \
  --exclude-scanners script-active \
  $BASE_URL

# Generate reports
docker exec zap zap-cli --api-key justmaily-zap-key report \
  -o /zap/wrk/report.html \
  -f html

docker exec zap zap-cli --api-key justmaily-zap-key report \
  -o /zap/wrk/report.json \
  -f json

docker exec zap zap-cli --api-key justmaily-zap-key alerts \
  -f json \
  > ${OUTPUT_DIR}/alerts.json

# Stop ZAP
docker stop zap
docker rm zap

# Analyze results
echo "Analyzing security scan results..."
python3 scripts/security/analyze_zap_results.py ${OUTPUT_DIR}/alerts.json

# Upload reports to S3
aws s3 cp ${OUTPUT_DIR} s3://justmaily-security-reports/${TIMESTAMP} --recursive

# Send notification
if [ -f ${OUTPUT_DIR}/high_alerts.txt ]; then
  aws sns publish \
    --topic-arn arn:aws:sns:us-east-1:123456789012:security-alerts \
    --message "High severity security issues found. Check report: s3://justmaily-security-reports/${TIMESTAMP}"
fi

echo "Security scan completed. Reports available in ${OUTPUT_DIR}"
