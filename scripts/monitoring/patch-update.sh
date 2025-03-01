#!/bin/bash

# Monthly Security Patch Update Script
# Usage: ./patch-update.sh [environment]

set -e

ENV=${1:-staging}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/patch_update_${TIMESTAMP}.log"

mkdir -p logs

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

check_environment() {
    log "Checking environment: $ENV"

    case $ENV in
        "staging"|"production")
            ;;
        *)
            log "ERROR: Invalid environment. Use: staging|production"
            exit 1
            ;;
    esac
}

backup_databases() {
    log "Creating database backups..."

    # RDS snapshot
    aws rds create-db-snapshot \
        --db-instance-identifier justmaily-${ENV} \
        --db-snapshot-identifier justmaily-${ENV}-pre-patch-${TIMESTAMP}

    # Wait for snapshot completion
    aws rds wait db-snapshot-available \
        --db-snapshot-identifier justmaily-${ENV}-pre-patch-${TIMESTAMP}

    log "Database backup completed"
}

update_dependencies() {
    log "Updating dependencies..."

    # Frontend dependencies
    cd frontend
    npm audit fix
    npm update
    npm audit
    cd ..

    # Backend dependencies
    cd backend
    pip install --upgrade pip
    pip install --upgrade -r requirements.txt
    safety check
    cd ..

    log "Dependencies updated"
}

update_containers() {
    log "Updating container images..."

    # Update base images
    docker pull node:18-alpine
    docker pull python:3.9-alpine

    # Rebuild application containers
    docker-compose -f docker-compose.${ENV}.yml build --no-cache

    log "Container images updated"
}

update_infrastructure() {
    log "Updating infrastructure components..."

    # Update ECS container instances
    aws ecs update-container-instances-state \
        --cluster justmaily-${ENV} \
        --container-instances $(aws ecs list-container-instances --cluster justmaily-${ENV} --query 'containerInstanceArns[]' --output text) \
        --status DRAINING

    # Wait for new instances
    sleep 300

    # Update ECS service
    aws ecs update-service \
        --cluster justmaily-${ENV} \
        --service justmaily-backend \
        --force-new-deployment

    aws ecs update-service \
        --cluster justmaily-${ENV} \
        --service justmaily-frontend \
        --force-new-deployment

    log "Infrastructure updated"
}

run_security_scan() {
    log "Running security scan..."

    # Run OWASP ZAP scan
    ./scripts/security/zap-scan.sh $ENV

    # Run npm audit
    cd frontend
    npm audit
    cd ..

    # Run pip safety check
    cd backend
    safety check
    cd ..

    log "Security scan completed"
}

verify_updates() {
    log "Verifying updates..."

    # Check application health
    HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" https://${ENV}.justmaily.com/health)
    if [ "$HEALTH_CHECK" != "200" ]; then
        log "ERROR: Health check failed"
        return 1
    fi

    # Check container versions
    docker images | grep justmaily

    # Check dependency versions
    cd frontend
    npm list --depth=0
    cd ../backend
    pip freeze

    log "Update verification completed"
}

notify_team() {
    log "Sending notifications..."

    # Create update report
    REPORT="Security patches applied for ${ENV} environment\n"
    REPORT+="Timestamp: ${TIMESTAMP}\n"
    REPORT+="Log file: ${LOG_FILE}\n"
    REPORT+="Please review the changes and monitor for any issues."

    # Send SNS notification
    aws sns publish \
        --topic-arn arn:aws:sns:us-east-1:123456789012:security-updates \
        --message "$REPORT"
}

rollback() {
    log "ERROR: Update failed, initiating rollback..."

    # Restore database if needed
    aws rds restore-db-instance-from-db-snapshot \
        --db-instance-identifier justmaily-${ENV}-rollback \
        --db-snapshot-identifier justmaily-${ENV}-pre-patch-${TIMESTAMP}

    # Rollback ECS services
    aws ecs update-service \
        --cluster justmaily-${ENV} \
        --service justmaily-backend \
        --task-definition justmaily-backend:previous

    aws ecs update-service \
        --cluster justmaily-${ENV} \
        --service justmaily-frontend \
        --task-definition justmaily-frontend:previous

    log "Rollback completed"
}

cleanup() {
    log "Performing cleanup..."

    # Remove old snapshots
    aws rds delete-db-snapshot \
        --db-snapshot-identifier justmaily-${ENV}-pre-patch-${TIMESTAMP}

    # Clean up Docker images
    docker system prune -f

    log "Cleanup completed"
}

main() {
    log "Starting security patch update for ${ENV} environment"

    check_environment
    backup_databases

    if update_dependencies && \
       update_containers && \
       update_infrastructure && \
       run_security_scan && \
       verify_updates; then
        cleanup
        notify_team
        log "Security patch update completed successfully"
    else
        rollback
        notify_team
        log "Security patch update failed, rollback completed"
        exit 1
    fi
}

main
