#!/bin/bash
# Maily Unified Deployment System
# A user-friendly, one-command deployment process from testing to production
# This script consolidates all deployment phases into one streamlined process

set -e

###############################
### CONFIGURATION VARIABLES ###
###############################

# Main configuration
DEPLOYMENT_VERSION="v1.0.0"
LOG_DIR="deployment_logs"
LOG_FILE="$LOG_DIR/deployment-$(date +%Y%m%d-%H%M%S).log"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
STAGING_NAMESPACE="maily-staging"
PROD_NAMESPACE="maily-production"
DRY_RUN=false
SKIP_CONFIRMATION=false
SKIP_STAGING=false
SKIP_MONITORING_WAIT=false
START_PHASE=1
END_PHASE=3

# Color and formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

#######################
### HELPER FUNCTIONS ###
#######################

# Display help information
show_help() {
  echo "Maily Unified Deployment System"
  echo "Usage: $0 [options]"
  echo ""
  echo "Options:"
  echo "  --help                    Show this help message"
  echo "  --version VERSION         Set deployment version (default: v1.0.0)"
  echo "  --dry-run                 Execute in dry-run mode without applying changes"
  echo "  --skip-staging            Skip staging deployment and go straight to production"
  echo "  --skip-confirmation       Run without confirmation prompts (non-interactive mode)"
  echo "  --skip-monitoring         Skip monitoring wait periods"
  echo "  --start-phase PHASE       Start at specified phase (1-3)"
  echo "  --end-phase PHASE         End at specified phase (1-3)"
  echo "  --staging-namespace NAME  Set staging namespace (default: maily-staging)"
  echo "  --prod-namespace NAME     Set production namespace (default: maily-production)"
  echo ""
  echo "Examples:"
  echo "  $0 --dry-run              # Test without applying changes"
  echo "  $0 --version v2.1.0       # Deploy specific version"
  echo "  $0 --skip-staging         # Skip staging and deploy directly to production"
  echo "  $0 --start-phase 2        # Start from phase 2 (initial production)"
  echo ""
}

# Print header
print_header() {
  clear
  echo -e "${BOLD}${BLUE}"
  echo "┌─────────────────────────────────────────────┐"
  echo "│       MAILY UNIFIED DEPLOYMENT SYSTEM       │"
  echo "└─────────────────────────────────────────────┘"
  echo -e "${NC}"
  echo "Deployment Version: $DEPLOYMENT_VERSION"
  echo "Started at: $(date)"
  echo "Log file: $LOG_FILE"
  echo ""
}

# Log a message to file and console
log() {
  local level=$1
  local message=$2
  local color=""
  local prefix=""
  
  case $level in
    "INFO")
      color="${BLUE}"
      prefix="ℹ️ INFO"
      ;;
    "SUCCESS")
      color="${GREEN}"
      prefix="✅ SUCCESS"
      ;;
    "WARNING")
      color="${YELLOW}"
      prefix="⚠️ WARNING"
      ;;
    "ERROR")
      color="${RED}"
      prefix="❌ ERROR"
      ;;
    "STEP")
      color="${CYAN}"
      prefix="🔄 STEP"
      ;;
    "SECTION")
      color="${PURPLE}${BOLD}"
      prefix="🔶 SECTION"
      ;;
  esac
  
  echo -e "${color}${prefix}:${NC} $message"
  echo "[$(date +"%Y-%m-%d %H:%M:%S")] [$level] $message" >> "$LOG_FILE"
}

# Interactive confirmation
confirm() {
  local message=$1
  local default=${2:-n}
  
  if [ "$SKIP_CONFIRMATION" = true ]; then
    return 0
  fi
  
  local prompt
  if [ "$default" = "y" ]; then
    prompt="[Y/n]"
  else
    prompt="[y/N]"
  fi
  
  echo -e "${YELLOW}${message} ${prompt}${NC}"
  read -r response
  
  if [ -z "$response" ]; then
    response=$default
  fi
  
  if [[ "$response" =~ ^[Yy]$ ]]; then
    return 0
  else
    return 1
  fi
}

# Display a progress animation while a command runs
run_with_spinner() {
  local message=$1
  local command=$2
  local temp_log=$(mktemp)
  
  echo -e "${CYAN}$message${NC}"
  echo "Command: $command" >> "$LOG_FILE"
  
  # Start the command in background and save its PID
  eval "$command" > "$temp_log" 2>&1 &
  local pid=$!
  
  # Define spinner characters
  local spinner=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
  local i=0
  
  # Display spinner while command is running
  while kill -0 $pid 2>/dev/null; do
    echo -ne "\r${spinner[$i]} Working..."
    i=$(( (i + 1) % ${#spinner[@]} ))
    sleep 0.1
  done
  
  # Capture the exit status of the command
  wait $pid
  local status=$?
  
  # Clear spinner line
  echo -ne "\r                      \r"
  
  # Log the output
  cat "$temp_log" >> "$LOG_FILE"
  rm "$temp_log"
  
  # Return the exit status
  return $status
}

# Check if a command exists
command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Check if all required tools are installed
check_requirements() {
  log "STEP" "Checking required tools..."
  
  local missing_tools=()
  
  # Check for kubectl
  if ! command_exists kubectl; then
    missing_tools+=("kubectl")
  fi
  
  # Check for jq if available (optional)
  if ! command_exists jq; then
    log "WARNING" "jq is not installed. Some features like JSON parsing may be limited."
  fi
  
  # Check for curl (for monitoring)
  if ! command_exists curl; then
    missing_tools+=("curl")
  fi
  
  # Report missing tools
  if [ ${#missing_tools[@]} -gt 0 ]; then
    log "ERROR" "The following required tools are missing: ${missing_tools[*]}"
    log "ERROR" "Please install these tools and try again."
    exit 1
  fi
  
  # Check kubectl connection
  if ! kubectl get ns &>/dev/null; then
    log "ERROR" "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
    exit 1
  fi
  
  log "SUCCESS" "All required tools are available"
}

# Display the deployment plan
show_deployment_plan() {
  log "SECTION" "DEPLOYMENT PLAN"
  
  log "INFO" "This unified deployment process will perform the following steps:"
  echo ""
  echo -e "  ${BOLD}Phase 1: Testing & Validation${NC}"
  echo "    • Deploy all changes to staging environment"
  echo "    • Run automated tests to validate changes"
  echo "    • Run chaos testing to validate resilience"
  echo "    • Verify SLA monitoring and alerting"
  echo ""
  echo -e "  ${BOLD}Phase 2: Initial Production Deployment${NC}"
  echo "    • Update non-critical services first"
  echo "    • Apply resource limits and probes"
  echo "    • Deploy logging and tracing configuration"
  echo "    • Monitor for performance impacts"
  echo ""
  echo -e "  ${BOLD}Phase 3: Full Production Deployment${NC}"
  echo "    • Update critical services"
  echo "    • Deploy secret rotation system"
  echo "    • Enable SLA monitoring in production"
  echo "    • Schedule chaos testing for resilience validation"
  echo ""
  
  echo "Starting at phase: $START_PHASE"
  echo "Ending at phase: $END_PHASE"
  
  if [ "$SKIP_STAGING" = true ]; then
    log "WARNING" "Staging deployment will be SKIPPED as requested"
  fi
  
  if [ "$DRY_RUN" = true ]; then
    log "WARNING" "This is a DRY RUN. No actual changes will be applied."
  fi
  
  echo ""
}

# Call external phase scripts
run_phase() {
  local phase=$1
  local phase_script="$SCRIPT_DIR/deploy-phases/phase$phase-$(echo $phase_desc | tr '[:upper:]' '[:lower:]' | tr ' ' '-').sh"
  
  if [[ -f "$phase_script" ]]; then
    # Source the phase script
    source "$phase_script"
    
    # Call the appropriate function
    case $phase in
      1)
        deploy_to_staging
        ;;
      2)
        deploy_to_prod_initial
        ;;
      3)
        deploy_to_prod_full
        ;;
      *)
        log "ERROR" "Invalid phase: $phase"
        exit 1
        ;;
    esac
  else
    log "ERROR" "Phase script not found: $phase_script"
    exit 1
  fi
}

# Parse command line arguments
parse_args() {
  while [[ $# -gt 0 ]]; do
    case $1 in
      --help)
        show_help
        exit 0
        ;;
      --version)
        DEPLOYMENT_VERSION="$2"
        shift 2
        ;;
      --dry-run)
        DRY_RUN=true
        shift
        ;;
      --skip-staging)
        SKIP_STAGING=true
        shift
        ;;
      --skip-confirmation)
        SKIP_CONFIRMATION=true
        shift
        ;;
      --skip-monitoring)
        SKIP_MONITORING_WAIT=true
        shift
        ;;
      --start-phase)
        START_PHASE="$2"
        shift 2
        ;;
      --end-phase)
        END_PHASE="$2"
        shift 2
        ;;
      --staging-namespace)
        STAGING_NAMESPACE="$2"
        shift 2
        ;;
      --prod-namespace)
        PROD_NAMESPACE="$2"
        shift 2
        ;;
      *)
        log "ERROR" "Unknown option: $1"
        show_help
        exit 1
        ;;
    esac
  done
  
  # Validate phase values
  if [[ ! "$START_PHASE" =~ ^[1-3]$ ]]; then
    log "ERROR" "Invalid start phase: $START_PHASE. Must be 1, 2, or 3."
    exit 1
  fi
  
  if [[ ! "$END_PHASE" =~ ^[1-3]$ ]]; then
    log "ERROR" "Invalid end phase: $END_PHASE. Must be 1, 2, or 3."
    exit 1
  fi
  
  if [ "$START_PHASE" -gt "$END_PHASE" ]; then
    log "ERROR" "Start phase ($START_PHASE) cannot be greater than end phase ($END_PHASE)."
    exit 1
  fi
}

# Main execution function
main() {
  # Create log directory if it doesn't exist
  mkdir -p "$LOG_DIR"
  
  # Print header and deployment information
  print_header
  
  # Check for required tools
  check_requirements
  
  # Show deployment plan
  show_deployment_plan
  
  # Confirm deployment plan
  if ! confirm "Do you want to proceed with this deployment plan?" "y"; then
    log "INFO" "Deployment cancelled by user."
    exit 0
  fi
  
  # Execute deployment phases based on configuration
  for phase in $(seq $START_PHASE $END_PHASE); do
    case $phase in
      1)
        phase_desc="Staging"
        ;;
      2)
        phase_desc="Prod Initial"
        ;;
      3)
        phase_desc="Prod Full"
        ;;
    esac
    
    log "SECTION" "Starting Phase $phase: $phase_desc"
    run_phase $phase
  done
  
  # Final success message
  log "SUCCESS" "Deployment completed successfully!"
  log "INFO" "Deployment log saved to: $LOG_FILE"
  
  if [ "$DRY_RUN" = true ]; then
    log "WARNING" "This was a DRY RUN. No actual changes were applied."
  fi
}

# Parse command line arguments
parse_args "$@"

# Execute main function
main
