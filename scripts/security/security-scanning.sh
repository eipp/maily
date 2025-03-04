#!/bin/bash
# security-scanning.sh
# Script to perform security scanning for Maily

set -e

# Default values
SCAN_TYPE="all"
OUTPUT_DIR="security-scan-results"
SEVERITY_THRESHOLD="medium"
SCAN_TARGET="."
DOCKER_IMAGE=""
API_URL=""
ENVIRONMENT="production"
SKIP_DEPENDENCY_CHECK=false
SKIP_DOCKER_SCAN=false
SKIP_CODE_SCAN=false
SKIP_SECRET_SCAN=false
SKIP_INFRASTRUCTURE_SCAN=false
SKIP_API_SCAN=false
FAIL_ON_SEVERITY=false
REPORT_FORMAT="html"
SCAN_TIMEOUT=3600

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --scan-type)
      SCAN_TYPE="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --severity-threshold)
      SEVERITY_THRESHOLD="$2"
      shift 2
      ;;
    --scan-target)
      SCAN_TARGET="$2"
      shift 2
      ;;
    --docker-image)
      DOCKER_IMAGE="$2"
      shift 2
      ;;
    --api-url)
      API_URL="$2"
      shift 2
      ;;
    --environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --skip-dependency-check)
      SKIP_DEPENDENCY_CHECK=true
      shift
      ;;
    --skip-docker-scan)
      SKIP_DOCKER_SCAN=true
      shift
      ;;
    --skip-code-scan)
      SKIP_CODE_SCAN=true
      shift
      ;;
    --skip-secret-scan)
      SKIP_SECRET_SCAN=true
      shift
      ;;
    --skip-infrastructure-scan)
      SKIP_INFRASTRUCTURE_SCAN=true
      shift
      ;;
    --skip-api-scan)
      SKIP_API_SCAN=true
      shift
      ;;
    --fail-on-severity)
      FAIL_ON_SEVERITY=true
      shift
      ;;
    --report-format)
      REPORT_FORMAT="$2"
      shift 2
      ;;
    --scan-timeout)
      SCAN_TIMEOUT="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Function to check if a tool is installed
check_tool() {
  if ! command -v "$1" &> /dev/null; then
    echo "Error: $1 is not installed. Please install it first."
    return 1
  fi
  return 0
}

# Function to determine severity level numeric value
severity_to_number() {
  case "$1" in
    "critical") echo 4 ;;
    "high") echo 3 ;;
    "medium") echo 2 ;;
    "low") echo 1 ;;
    "info") echo 0 ;;
    *) echo -1 ;;
  esac
}

# Function to check if a finding exceeds the severity threshold
exceeds_threshold() {
  local finding_severity="$1"
  local threshold="$2"
  
  local finding_value=$(severity_to_number "$finding_severity")
  local threshold_value=$(severity_to_number "$threshold")
  
  if [ "$finding_value" -ge "$threshold_value" ]; then
    return 0  # True, exceeds threshold
  else
    return 1  # False, does not exceed threshold
  fi
}

# Function to run dependency check
run_dependency_check() {
  echo "Running dependency check..."
  
  if ! check_tool "dependency-check"; then
    echo "Installing OWASP Dependency Check..."
    mkdir -p "$HOME/tools/dependency-check"
    curl -L "https://github.com/jeremylong/DependencyCheck/releases/download/v7.4.4/dependency-check-7.4.4-release.zip" -o "$HOME/tools/dependency-check.zip"
    unzip -q "$HOME/tools/dependency-check.zip" -d "$HOME/tools"
    export PATH="$PATH:$HOME/tools/dependency-check/bin"
    rm "$HOME/tools/dependency-check.zip"
  fi
  
  # Run dependency check
  dependency-check \
    --project "Maily" \
    --scan "$SCAN_TARGET" \
    --format "HTML" \
    --format "JSON" \
    --out "$OUTPUT_DIR/dependency-check" \
    --suppression ".dependency-check-suppression.xml" \
    --failOnCVSS 7
  
  echo "Dependency check completed. Results saved to $OUTPUT_DIR/dependency-check"
}

# Function to run Docker image scan
run_docker_scan() {
  echo "Running Docker image scan..."
  
  if [ -z "$DOCKER_IMAGE" ]; then
    echo "No Docker image specified. Skipping Docker scan."
    return
  fi
  
  if ! check_tool "trivy"; then
    echo "Installing Trivy..."
    curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin
  fi
  
  # Run Trivy scan
  trivy image \
    --format json \
    --output "$OUTPUT_DIR/docker-scan.json" \
    --severity "$SEVERITY_THRESHOLD,high,critical" \
    "$DOCKER_IMAGE"
  
  # Generate HTML report
  if [ "$REPORT_FORMAT" = "html" ]; then
    trivy image \
      --format template \
      --template "@contrib/html.tpl" \
      --output "$OUTPUT_DIR/docker-scan.html" \
      --severity "$SEVERITY_THRESHOLD,high,critical" \
      "$DOCKER_IMAGE"
  fi
  
  echo "Docker image scan completed. Results saved to $OUTPUT_DIR/docker-scan.json"
}

# Function to run code scan
run_code_scan() {
  echo "Running code scan..."
  
  if ! check_tool "semgrep"; then
    echo "Installing Semgrep..."
    python3 -m pip install semgrep
  fi
  
  # Run Semgrep scan
  semgrep \
    --config=auto \
    --json \
    --output="$OUTPUT_DIR/code-scan.json" \
    --severity="$SEVERITY_THRESHOLD" \
    "$SCAN_TARGET"
  
  # Generate HTML report
  if [ "$REPORT_FORMAT" = "html" ]; then
    semgrep \
      --config=auto \
      --sarif \
      --output="$OUTPUT_DIR/code-scan.sarif" \
      --severity="$SEVERITY_THRESHOLD" \
      "$SCAN_TARGET"
    
    # Convert SARIF to HTML (requires sarif-tools)
    if check_tool "sarif-to-html"; then
      sarif-to-html "$OUTPUT_DIR/code-scan.sarif" "$OUTPUT_DIR/code-scan.html"
    else
      echo "sarif-to-html not found. Install with: npm install -g @microsoft/sarif-tools"
    fi
  fi
  
  echo "Code scan completed. Results saved to $OUTPUT_DIR/code-scan.json"
}

# Function to run secret scan
run_secret_scan() {
  echo "Running secret scan..."
  
  if ! check_tool "gitleaks"; then
    echo "Installing Gitleaks..."
    curl -L "https://github.com/zricethezav/gitleaks/releases/download/v8.16.3/gitleaks_8.16.3_linux_x64.tar.gz" -o /tmp/gitleaks.tar.gz
    tar -xzf /tmp/gitleaks.tar.gz -C /tmp
    sudo mv /tmp/gitleaks /usr/local/bin/
    rm /tmp/gitleaks.tar.gz
  fi
  
  # Run Gitleaks scan
  gitleaks detect \
    --source="$SCAN_TARGET" \
    --report-format="json" \
    --report-path="$OUTPUT_DIR/secret-scan.json" \
    --no-git
  
  # Generate HTML report
  if [ "$REPORT_FORMAT" = "html" ]; then
    # Convert JSON to HTML using a simple script
    cat > /tmp/gitleaks-to-html.py << 'EOF'
import json
import sys
import os
from datetime import datetime

def generate_html(input_file, output_file):
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Gitleaks Scan Report</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
            h1, h2, h3 { color: #333; }
            .finding { margin-bottom: 20px; padding: 15px; background-color: #f9f9f9; border-radius: 5px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
            .finding h3 { margin-top: 0; color: #d9534f; }
            .finding-details { margin-left: 20px; }
            .finding-meta { color: #666; font-size: 0.9em; }
            .secret { background-color: #f2dede; padding: 5px; border-radius: 3px; }
            .high { border-left: 5px solid #d9534f; }
            .medium { border-left: 5px solid #f0ad4e; }
            .low { border-left: 5px solid #5bc0de; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Gitleaks Scan Report</h1>
            <p>Scan completed on """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
            <h2>Findings: """ + str(len(data)) + """</h2>
    """
    
    for i, finding in enumerate(data):
        severity = "high" if finding.get("rule", {}).get("severity", "") == "high" else "medium"
        html += f"""
            <div class="finding {severity}">
                <h3>Finding #{i+1}: {finding.get("rule", {}).get("description", "Unknown")}</h3>
                <div class="finding-details">
                    <p><strong>File:</strong> {finding.get("file", "Unknown")}</p>
                    <p><strong>Line:</strong> {finding.get("startLine", "Unknown")}</p>
                    <p><strong>Rule:</strong> {finding.get("rule", {}).get("id", "Unknown")}</p>
                    <p><strong>Severity:</strong> {finding.get("rule", {}).get("severity", "Unknown")}</p>
                    <p><strong>Secret:</strong> <span class="secret">{finding.get("secret", "Unknown")}</span></p>
                    <p class="finding-meta">Match: {finding.get("match", "Unknown")}</p>
                </div>
            </div>
        """
    
    html += """
        </div>
    </body>
    </html>
    """
    
    with open(output_file, 'w') as f:
        f.write(html)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python gitleaks-to-html.py input.json output.html")
        sys.exit(1)
    
    generate_html(sys.argv[1], sys.argv[2])
EOF
    
    python3 /tmp/gitleaks-to-html.py "$OUTPUT_DIR/secret-scan.json" "$OUTPUT_DIR/secret-scan.html"
    rm /tmp/gitleaks-to-html.py
  fi
  
  echo "Secret scan completed. Results saved to $OUTPUT_DIR/secret-scan.json"
}

# Function to run infrastructure scan
run_infrastructure_scan() {
  echo "Running infrastructure scan..."
  
  if ! check_tool "tfsec"; then
    echo "Installing tfsec..."
    curl -L "https://github.com/aquasecurity/tfsec/releases/download/v1.28.1/tfsec-linux-amd64" -o /tmp/tfsec
    chmod +x /tmp/tfsec
    sudo mv /tmp/tfsec /usr/local/bin/
  fi
  
  # Run tfsec scan
  tfsec \
    --format json \
    --out "$OUTPUT_DIR/infrastructure-scan.json" \
    --minimum-severity "$SEVERITY_THRESHOLD" \
    ./infrastructure/terraform
  
  # Generate HTML report
  if [ "$REPORT_FORMAT" = "html" ]; then
    tfsec \
      --format html \
      --out "$OUTPUT_DIR/infrastructure-scan.html" \
      --minimum-severity "$SEVERITY_THRESHOLD" \
      ./infrastructure/terraform
  fi
  
  echo "Infrastructure scan completed. Results saved to $OUTPUT_DIR/infrastructure-scan.json"
}

# Function to run API scan
run_api_scan() {
  echo "Running API scan..."
  
  if [ -z "$API_URL" ]; then
    echo "No API URL specified. Skipping API scan."
    return
  fi
  
  if ! check_tool "zap-cli"; then
    echo "Installing OWASP ZAP CLI..."
    pip install --upgrade zapcli
  fi
  
  # Start ZAP daemon
  echo "Starting ZAP daemon..."
  zap-cli start
  
  # Run ZAP scan
  zap-cli -v quick-scan \
    --self-contained \
    --start-options "-config api.disablekey=true" \
    --spider \
    --ajax-spider \
    --scan \
    --recursive \
    "$API_URL"
  
  # Generate report
  zap-cli report \
    -o "$OUTPUT_DIR/api-scan.$REPORT_FORMAT" \
    -f "$REPORT_FORMAT"
  
  # Stop ZAP daemon
  zap-cli shutdown
  
  echo "API scan completed. Results saved to $OUTPUT_DIR/api-scan.$REPORT_FORMAT"
}

# Function to generate consolidated report
generate_consolidated_report() {
  echo "Generating consolidated report..."
  
  # Create HTML report
  cat > "$OUTPUT_DIR/consolidated-report.html" << EOF
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Maily Security Scan Report</title>
  <style>
    body {
      font-family: Arial, sans-serif;
      margin: 0;
      padding: 20px;
      background-color: #f5f5f5;
    }
    .container {
      max-width: 1200px;
      margin: 0 auto;
      background-color: white;
      padding: 20px;
      border-radius: 5px;
      box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    h1, h2, h3 {
      color: #333;
    }
    .summary {
      display: flex;
      flex-wrap: wrap;
      margin-bottom: 20px;
    }
    .summary-item {
      flex: 1;
      min-width: 200px;
      margin: 10px;
      padding: 15px;
      background-color: #f9f9f9;
      border-radius: 5px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .summary-item h3 {
      margin-top: 0;
    }
    .scan-section {
      margin-bottom: 30px;
    }
    .scan-section h2 {
      border-bottom: 1px solid #ddd;
      padding-bottom: 10px;
    }
    .finding {
      margin-bottom: 20px;
      padding: 15px;
      background-color: #f9f9f9;
      border-radius: 5px;
      box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .finding h3 {
      margin-top: 0;
    }
    .critical {
      border-left: 5px solid #d9534f;
    }
    .high {
      border-left: 5px solid #f0ad4e;
    }
    .medium {
      border-left: 5px solid #5bc0de;
    }
    .low {
      border-left: 5px solid #5cb85c;
    }
    .scan-links {
      margin-top: 20px;
    }
    .scan-links a {
      display: inline-block;
      margin-right: 10px;
      padding: 8px 15px;
      background-color: #f0f0f0;
      color: #333;
      text-decoration: none;
      border-radius: 3px;
    }
    .scan-links a:hover {
      background-color: #e0e0e0;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1>Maily Security Scan Report</h1>
    <p>Scan completed on $(date)</p>
    <p>Environment: $ENVIRONMENT</p>
    <p>Severity Threshold: $SEVERITY_THRESHOLD</p>
    
    <div class="summary">
      <div class="summary-item">
        <h3>Total Scans</h3>
        <p>$(find "$OUTPUT_DIR" -type f | wc -l)</p>
      </div>
      <div class="summary-item">
        <h3>Critical Findings</h3>
        <p>$(grep -r "critical" "$OUTPUT_DIR" | wc -l)</p>
      </div>
      <div class="summary-item">
        <h3>High Findings</h3>
        <p>$(grep -r "high" "$OUTPUT_DIR" | wc -l)</p>
      </div>
      <div class="summary-item">
        <h3>Medium Findings</h3>
        <p>$(grep -r "medium" "$OUTPUT_DIR" | wc -l)</p>
      </div>
    </div>
    
    <div class="scan-section">
      <h2>Scan Results</h2>
      <p>The following security scans were performed:</p>
      <ul>
EOF

  # Add links to individual reports
  if [ -f "$OUTPUT_DIR/dependency-check/dependency-check-report.html" ]; then
    echo "<li><a href=\"dependency-check/dependency-check-report.html\">Dependency Check Report</a></li>" >> "$OUTPUT_DIR/consolidated-report.html"
  fi
  
  if [ -f "$OUTPUT_DIR/docker-scan.html" ]; then
    echo "<li><a href=\"docker-scan.html\">Docker Image Scan Report</a></li>" >> "$OUTPUT_DIR/consolidated-report.html"
  fi
  
  if [ -f "$OUTPUT_DIR/code-scan.html" ]; then
    echo "<li><a href=\"code-scan.html\">Code Scan Report</a></li>" >> "$OUTPUT_DIR/consolidated-report.html"
  fi
  
  if [ -f "$OUTPUT_DIR/secret-scan.html" ]; then
    echo "<li><a href=\"secret-scan.html\">Secret Scan Report</a></li>" >> "$OUTPUT_DIR/consolidated-report.html"
  fi
  
  if [ -f "$OUTPUT_DIR/infrastructure-scan.html" ]; then
    echo "<li><a href=\"infrastructure-scan.html\">Infrastructure Scan Report</a></li>" >> "$OUTPUT_DIR/consolidated-report.html"
  fi
  
  if [ -f "$OUTPUT_DIR/api-scan.html" ]; then
    echo "<li><a href=\"api-scan.html\">API Scan Report</a></li>" >> "$OUTPUT_DIR/consolidated-report.html"
  fi
  
  # Close HTML
  cat >> "$OUTPUT_DIR/consolidated-report.html" << EOF
      </ul>
    </div>
    
    <div class="scan-section">
      <h2>Recommendations</h2>
      <p>Based on the scan results, the following actions are recommended:</p>
      <ul>
        <li>Review and address all critical and high severity findings</li>
        <li>Update dependencies with known vulnerabilities</li>
        <li>Remove any hardcoded secrets from the codebase</li>
        <li>Fix infrastructure security misconfigurations</li>
        <li>Implement proper input validation for API endpoints</li>
      </ul>
    </div>
  </div>
</body>
</html>
EOF

  echo "Consolidated report generated at $OUTPUT_DIR/consolidated-report.html"
}

# Run scans based on scan type
if [ "$SCAN_TYPE" = "all" ] || [ "$SCAN_TYPE" = "dependency" ]; then
  if [ "$SKIP_DEPENDENCY_CHECK" = false ]; then
    run_dependency_check
  fi
fi

if [ "$SCAN_TYPE" = "all" ] || [ "$SCAN_TYPE" = "docker" ]; then
  if [ "$SKIP_DOCKER_SCAN" = false ]; then
    run_docker_scan
  fi
fi

if [ "$SCAN_TYPE" = "all" ] || [ "$SCAN_TYPE" = "code" ]; then
  if [ "$SKIP_CODE_SCAN" = false ]; then
    run_code_scan
  fi
fi

if [ "$SCAN_TYPE" = "all" ] || [ "$SCAN_TYPE" = "secret" ]; then
  if [ "$SKIP_SECRET_SCAN" = false ]; then
    run_secret_scan
  fi
fi

if [ "$SCAN_TYPE" = "all" ] || [ "$SCAN_TYPE" = "infrastructure" ]; then
  if [ "$SKIP_INFRASTRUCTURE_SCAN" = false ]; then
    run_infrastructure_scan
  fi
fi

if [ "$SCAN_TYPE" = "all" ] || [ "$SCAN_TYPE" = "api" ]; then
  if [ "$SKIP_API_SCAN" = false ]; then
    run_api_scan
  fi
fi

# Generate consolidated report
generate_consolidated_report

echo "Security scanning completed. Results saved to $OUTPUT_DIR"

# Check if we should fail based on severity
if [ "$FAIL_ON_SEVERITY" = true ]; then
  if grep -q "critical\|high" "$OUTPUT_DIR"/*; then
    echo "Critical or high severity findings detected. Failing the build."
    exit 1
  fi
fi

exit 0

# Check for dry-run mode
DRY_RUN=false
for arg in "$@"; do
  if [[ "$arg" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "Running in dry-run mode. No changes will be made."
  fi
done

