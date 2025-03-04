#!/bin/bash
# Script to run chaos testing experiments sequentially

set -e

NAMESPACE="maily-production"
TEST_DURATION=1800  # 30 minutes total test time
REPORT_DIR="chaos-reports"
LOG_FILE="$REPORT_DIR/chaos-test-$(date +%Y%m%d-%H%M%S).log"

# Create report directory
mkdir -p "$REPORT_DIR"

echo "Starting chaos testing at $(date)" | tee -a "$LOG_FILE"

# Function to run a chaos experiment
run_experiment() {
    local experiment_file=$1
    local duration=$2
    local description=$3
    
    experiment_name=$(basename "$experiment_file" .yaml)
    
    echo "====================================" | tee -a "$LOG_FILE"
    echo "Starting experiment: $description" | tee -a "$LOG_FILE"
    echo "Experiment file: $experiment_file" | tee -a "$LOG_FILE"
    echo "Duration: $duration seconds" | tee -a "$LOG_FILE"
    echo "Time: $(date)" | tee -a "$LOG_FILE"
    
    # Apply the experiment with paused=false
    kubectl apply -f "$experiment_file" | tee -a "$LOG_FILE"
    
    # Unpause the experiment
    kubectl patch $(kubectl get -f "$experiment_file" -o name) --type=merge -p '{"spec":{"paused":false}}' | tee -a "$LOG_FILE"
    
    echo "Experiment $experiment_name is running..." | tee -a "$LOG_FILE"
    
    # Monitor the system during chaos test
    echo "Monitoring system..." | tee -a "$LOG_FILE"
    
    # Start time
    start_time=$(date +%s)
    end_time=$((start_time + duration))
    current_time=$start_time
    
    while [ $current_time -lt $end_time ]; do
        # Print services status
        echo "----- Services Status at $(date) -----" | tee -a "$LOG_FILE"
        kubectl get pods -n "$NAMESPACE" -o wide | tee -a "$LOG_FILE"
        
        # Check endpoints and services
        echo "----- API Health at $(date) -----" | tee -a "$LOG_FILE"
        curl -s -o /dev/null -w "%{http_code}" https://api.mailyapp.com/health || echo "API unreachable" | tee -a "$LOG_FILE"
        
        # Wait 30 seconds before checking again
        sleep 30
        current_time=$(date +%s)
    done
    
    # Pause the experiment after completion
    echo "Pausing experiment $experiment_name..." | tee -a "$LOG_FILE"
    kubectl patch $(kubectl get -f "$experiment_file" -o name) --type=merge -p '{"spec":{"paused":true}}' | tee -a "$LOG_FILE"
    
    # Wait for system recovery
    echo "Waiting for system to recover (120s)..." | tee -a "$LOG_FILE"
    sleep 120
    
    # Verify system recovered
    echo "----- System Status after Recovery -----" | tee -a "$LOG_FILE"
    kubectl get pods -n "$NAMESPACE" -o wide | tee -a "$LOG_FILE"
    
    echo "Experiment $experiment_name completed at $(date)" | tee -a "$LOG_FILE"
    echo "====================================" | tee -a "$LOG_FILE"
}

# Main execution

# 1. Pod Failure Experiment
run_experiment "kubernetes/chaos-testing/pod-failure-experiment.yaml" 300 "Random Pod Failure Test"

# 2. Network Delay Experiment
run_experiment "kubernetes/chaos-testing/network-delay-experiment.yaml" 300 "Network Latency Test"

# 3. CPU Stress Experiment
run_experiment "kubernetes/chaos-testing/stress-cpu-experiment.yaml" 300 "CPU Resource Stress Test"

# Generate summary report
echo "====================================" | tee -a "$LOG_FILE"
echo "Chaos Testing Complete at $(date)" | tee -a "$LOG_FILE"
echo "Final System Status:" | tee -a "$LOG_FILE"
kubectl get pods -n "$NAMESPACE" -o wide | tee -a "$LOG_FILE"
kubectl get svc -n "$NAMESPACE" | tee -a "$LOG_FILE"

# Check system metrics
echo "====================================" | tee -a "$LOG_FILE"
echo "System Metrics After Testing:" | tee -a "$LOG_FILE"
echo "CPU Usage:" | tee -a "$LOG_FILE"
kubectl top pods -n "$NAMESPACE" | tee -a "$LOG_FILE"

echo "====================================" | tee -a "$LOG_FILE"
echo "Chaos Testing Report generated at: $LOG_FILE" | tee -a "$LOG_FILE"
echo "====================================" | tee -a "$LOG_FILE"
