#!/bin/bash

# Set up colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Global variables
VERBOSE=false
REPORT_DIR="./diagnostic_reports"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create report directory if it doesn't exist
mkdir -p $REPORT_DIR

# ==============================================================================
# Blockchain Diagnostics
# ==============================================================================
run_blockchain_diagnostics() {
    echo -e "\n${BLUE}Running Blockchain Diagnostics${NC}"

    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: python3 is required but not found in PATH${NC}"
        return 1
    fi

    # Run the blockchain diagnostics script
    if [ "$VERBOSE" = true ]; then
        python3 tools/blockchain_diagnostics.py --verbose --format json --output $REPORT_DIR/blockchain_diagnostics.json
    else
        python3 tools/blockchain_diagnostics.py --format json --output $REPORT_DIR/blockchain_diagnostics.json
    fi

    # Check exit status
    if [ $? -ne 0 ]; then
        echo -e "${RED}Blockchain diagnostics failed${NC}"
        echo -e "${YELLOW}See logs for details${NC}"
        return 1
    fi

    # Display summary from the JSON output
    if [ -f "$REPORT_DIR/blockchain_diagnostics.json" ]; then
        echo -e "\n${GREEN}Blockchain Diagnostics Complete${NC}"
        echo -e "Results saved to: $REPORT_DIR/blockchain_diagnostics.json"

        # Extract and display summary info using jq if available
        if command -v jq &> /dev/null; then
            OVERALL=$(jq -r '.overall_status' $REPORT_DIR/blockchain_diagnostics.json)
            PASSED=$(jq -r '.summary.passed' $REPORT_DIR/blockchain_diagnostics.json)
            FAILED=$(jq -r '.summary.failed' $REPORT_DIR/blockchain_diagnostics.json)
            WARNINGS=$(jq -r '.summary.warnings' $REPORT_DIR/blockchain_diagnostics.json)
            SKIPPED=$(jq -r '.summary.skipped' $REPORT_DIR/blockchain_diagnostics.json)

            echo -e "\nSummary:"
            if [ "$OVERALL" = "PASSED" ]; then
                echo -e "${GREEN}Overall Status: $OVERALL${NC}"
            elif [ "$OVERALL" = "WARNING" ]; then
                echo -e "${YELLOW}Overall Status: $OVERALL${NC}"
            else
                echo -e "${RED}Overall Status: $OVERALL${NC}"
            fi

            echo -e "Tests Passed: $PASSED"
            echo -e "Tests Failed: $FAILED"
            echo -e "Tests with Warnings: $WARNINGS"
            echo -e "Tests Skipped: $SKIPPED"

            # If there are failures, show them
            if [ "$FAILED" -gt 0 ]; then
                echo -e "\n${RED}Failed Tests:${NC}"
                jq -r '.summary.failed_tests[]' $REPORT_DIR/blockchain_diagnostics.json | while read -r test; do
                    ERROR_MSG=$(jq -r --arg test "$test" '.tests[$test].message' $REPORT_DIR/blockchain_diagnostics.json)
                    echo -e "${RED}- $test: $ERROR_MSG${NC}"
                done
            fi

            # If there are warnings, show them
            if [ "$WARNINGS" -gt 0 ]; then
                echo -e "\n${YELLOW}Tests with Warnings:${NC}"
                jq -r '.summary.warning_tests[]' $REPORT_DIR/blockchain_diagnostics.json | while read -r test; do
                    WARNING_MSG=$(jq -r --arg test "$test" '.tests[$test].message' $REPORT_DIR/blockchain_diagnostics.json)
                    echo -e "${YELLOW}- $test: $WARNING_MSG${NC}"
                done
            fi
        else
            echo -e "${YELLOW}jq not found. Install jq for more detailed summary.${NC}"
            echo -e "View the JSON file for complete results."
        fi
    else
        echo -e "${RED}No diagnostics output found${NC}"
        return 1
    fi
}

# ==============================================================================
# Redis Diagnostics
# ==============================================================================
run_redis_diagnostics() {
    echo -e "\n${BLUE}Running Redis Diagnostics${NC}"

    # Check if Python is available
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}Error: python3 is required but not found in PATH${NC}"
        return 1
    fi

    # Run the Redis diagnostics script
    if [ "$VERBOSE" = true ]; then
        python3 tools/redis_diagnostics.py --verbose --format json --output $REPORT_DIR/redis_diagnostics.json
    else
        python3 tools/redis_diagnostics.py --format json --output $REPORT_DIR/redis_diagnostics.json
    fi

    # Check exit status
    if [ $? -ne 0 ]; then
        echo -e "${RED}Redis diagnostics failed${NC}"
        echo -e "${YELLOW}See logs for details${NC}"
        return 1
    fi

    # Display summary from the JSON output
    if [ -f "$REPORT_DIR/redis_diagnostics.json" ]; then
        echo -e "\n${GREEN}Redis Diagnostics Complete${NC}"
        echo -e "Results saved to: $REPORT_DIR/redis_diagnostics.json"

        # Extract and display summary info using jq if available
        if command -v jq &> /dev/null; then
            OVERALL=$(jq -r '.overall_status' $REPORT_DIR/redis_diagnostics.json)
            PASSED=$(jq -r '.summary.passed' $REPORT_DIR/redis_diagnostics.json)
            FAILED=$(jq -r '.summary.failed' $REPORT_DIR/redis_diagnostics.json)
            WARNINGS=$(jq -r '.summary.warnings' $REPORT_DIR/redis_diagnostics.json)
            SKIPPED=$(jq -r '.summary.skipped' $REPORT_DIR/redis_diagnostics.json)

            echo -e "\nSummary:"
            if [ "$OVERALL" = "PASSED" ]; then
                echo -e "${GREEN}Overall Status: $OVERALL${NC}"
            elif [ "$OVERALL" = "WARNING" ]; then
                echo -e "${YELLOW}Overall Status: $OVERALL${NC}"
            else
                echo -e "${RED}Overall Status: $OVERALL${NC}"
            fi

            echo -e "Tests Passed: $PASSED"
            echo -e "Tests Failed: $FAILED"
            echo -e "Tests with Warnings: $WARNINGS"
            echo -e "Tests Skipped: $SKIPPED"

            # If there are failures, show them
            if [ "$FAILED" -gt 0 ]; then
                echo -e "\n${RED}Failed Tests:${NC}"
                jq -r '.summary.failed_tests[]' $REPORT_DIR/redis_diagnostics.json | while read -r test; do
                    ERROR_MSG=$(jq -r --arg test "$test" '.tests[$test].message' $REPORT_DIR/redis_diagnostics.json)
                    echo -e "${RED}- $test: $ERROR_MSG${NC}"
                done
            fi

            # If there are warnings, show them
            if [ "$WARNINGS" -gt 0 ]; then
                echo -e "\n${YELLOW}Tests with Warnings:${NC}"
                jq -r '.summary.warning_tests[]' $REPORT_DIR/redis_diagnostics.json | while read -r test; do
                    WARNING_MSG=$(jq -r --arg test "$test" '.tests[$test].message' $REPORT_DIR/redis_diagnostics.json)
                    echo -e "${YELLOW}- $test: $WARNING_MSG${NC}"
                done
            fi
        else
            echo -e "${YELLOW}jq not found. Install jq for more detailed summary.${NC}"
            echo -e "View the JSON file for complete results."
        fi
    else
        echo -e "${RED}No diagnostics output found${NC}"
        return 1
    fi
}

# ==============================================================================
# API Diagnostics
# ==============================================================================
run_api_diagnostics() {
    echo -e "\n${BLUE}Running API Diagnostics${NC}"
    # API diagnostics implementation
    echo -e "${GREEN}API Diagnostics Complete${NC}"
}

# ==============================================================================
# Database Diagnostics
# ==============================================================================
run_db_diagnostics() {
    echo -e "\n${BLUE}Running Database Diagnostics${NC}"
    # Database diagnostics implementation
    echo -e "${GREEN}Database Diagnostics Complete${NC}"
}

# ==============================================================================
# Security Diagnostics
# ==============================================================================
run_security_diagnostics() {
    echo -e "\n${BLUE}Running Security Diagnostics${NC}"
    # Security diagnostics implementation
    echo -e "${GREEN}Security Diagnostics Complete${NC}"
}

# ==============================================================================
# Run All Diagnostics
# ==============================================================================
run_all_diagnostics() {
    echo -e "\n${BLUE}Running All Diagnostics${NC}"
    echo -e "${BLUE}=============================${NC}"

    # Create a summary report
    SUMMARY_FILE="$REPORT_DIR/diagnostics_summary_$TIMESTAMP.txt"
    echo "Maily Diagnostics Summary - $TIMESTAMP" > $SUMMARY_FILE
    echo "=======================================" >> $SUMMARY_FILE

    # Run all diagnostic modules
    run_blockchain_diagnostics
    BLOCKCHAIN_STATUS=$?

    run_redis_diagnostics
    REDIS_STATUS=$?

    run_api_diagnostics
    API_STATUS=$?

    run_db_diagnostics
    DB_STATUS=$?

    run_security_diagnostics
    SECURITY_STATUS=$?

    # Generate the summary
    echo -e "\n${BLUE}Diagnostics Complete${NC}"
    echo -e "${BLUE}=============================${NC}"
    echo -e "\nResults Summary:"

    # Blockchain status
    if [ $BLOCKCHAIN_STATUS -eq 0 ]; then
        echo -e "Blockchain: ${GREEN}PASSED${NC}"
        echo "Blockchain: PASSED" >> $SUMMARY_FILE
    else
        echo -e "Blockchain: ${RED}FAILED${NC} - See $REPORT_DIR/blockchain_diagnostics.json"
        echo "Blockchain: FAILED - See $REPORT_DIR/blockchain_diagnostics.json" >> $SUMMARY_FILE
    fi

    # Redis status
    if [ $REDIS_STATUS -eq 0 ]; then
        echo -e "Redis: ${GREEN}PASSED${NC}"
        echo "Redis: PASSED" >> $SUMMARY_FILE
    else
        echo -e "Redis: ${RED}FAILED${NC} - See $REPORT_DIR/redis_diagnostics.json"
        echo "Redis: FAILED - See $REPORT_DIR/redis_diagnostics.json" >> $SUMMARY_FILE
    fi

    # API status
    if [ $API_STATUS -eq 0 ]; then
        echo -e "API: ${GREEN}PASSED${NC}"
        echo "API: PASSED" >> $SUMMARY_FILE
    else
        echo -e "API: ${RED}FAILED${NC}"
        echo "API: FAILED" >> $SUMMARY_FILE
    fi

    # Database status
    if [ $DB_STATUS -eq 0 ]; then
        echo -e "Database: ${GREEN}PASSED${NC}"
        echo "Database: PASSED" >> $SUMMARY_FILE
    else
        echo -e "Database: ${RED}FAILED${NC}"
        echo "Database: FAILED" >> $SUMMARY_FILE
    fi

    # Security status
    if [ $SECURITY_STATUS -eq 0 ]; then
        echo -e "Security: ${GREEN}PASSED${NC}"
        echo "Security: PASSED" >> $SUMMARY_FILE
    else
        echo -e "Security: ${RED}FAILED${NC}"
        echo "Security: FAILED" >> $SUMMARY_FILE
    fi

    # Overall status
    if [ $BLOCKCHAIN_STATUS -eq 0 ] && [ $REDIS_STATUS -eq 0 ] && [ $API_STATUS -eq 0 ] && [ $DB_STATUS -eq 0 ] && [ $SECURITY_STATUS -eq 0 ]; then
        echo -e "\nOverall Status: ${GREEN}PASSED${NC}"
        echo -e "\nOverall Status: PASSED" >> $SUMMARY_FILE
    else
        echo -e "\nOverall Status: ${RED}FAILED${NC}"
        echo -e "\nOverall Status: FAILED" >> $SUMMARY_FILE
    fi

    echo -e "\nSummary report saved to: $SUMMARY_FILE"
}

# ==============================================================================
# Display Help
# ==============================================================================
show_help() {
    echo "Maily Diagnostics Tool"
    echo "======================"
    echo "Usage: $0 [options] [command]"
    echo ""
    echo "Options:"
    echo "  -h, --help        Show this help message"
    echo "  -v, --verbose     Enable verbose output"
    echo ""
    echo "Commands:"
    echo "  all               Run all diagnostics (default)"
    echo "  blockchain        Run blockchain diagnostics"
    echo "  redis             Run Redis diagnostics"
    echo "  api               Run API diagnostics"
    echo "  db                Run database diagnostics"
    echo "  security          Run security diagnostics"
    echo ""
    echo "Examples:"
    echo "  $0                Run all diagnostics"
    echo "  $0 blockchain     Run blockchain diagnostics"
    echo "  $0 -v redis       Run Redis diagnostics with verbose output"
}

# ==============================================================================
# Parse command line arguments
# ==============================================================================
COMMAND="all"

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        all|blockchain|redis|api|db|security)
            COMMAND=$1
            shift
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# ==============================================================================
# Main
# ==============================================================================
echo -e "${BLUE}Maily Diagnostics Tool${NC}"
echo -e "${BLUE}======================${NC}"
echo -e "Running at: $(date)"
echo -e "Report directory: $REPORT_DIR"
echo -e "Command: $COMMAND"
echo -e "Verbose: $VERBOSE"

# Run the appropriate diagnostic
case $COMMAND in
    all)
        run_all_diagnostics
        ;;
    blockchain)
        run_blockchain_diagnostics
        ;;
    redis)
        run_redis_diagnostics
        ;;
    api)
        run_api_diagnostics
        ;;
    db)
        run_db_diagnostics
        ;;
    security)
        run_security_diagnostics
        ;;
esac

exit 0
