#!/bin/bash

# Disaster Recovery Failover Script
# Usage: ./failover.sh [component] [region]

set -e

COMPONENT=$1
REGION=${2:-us-east-1}
BACKUP_REGION="us-west-2"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="logs/failover_${TIMESTAMP}.log"

mkdir -p logs

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a $LOG_FILE
}

check_prerequisites() {
    log "Checking prerequisites..."

    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        log "ERROR: AWS CLI is not installed"
        exit 1
    }

    # Check required permissions
    aws sts get-caller-identity > /dev/null || {
        log "ERROR: AWS credentials not configured"
        exit 1
    }
}

database_failover() {
    log "Starting database failover procedure..."

    # Get current RDS status
    PRIMARY_DB=$(aws rds describe-db-instances \
        --region $REGION \
        --query 'DBInstances[?TagList[?Key==`Name` && Value==`justmaily-primary`]].[DBInstanceIdentifier]' \
        --output text)

    # Promote read replica to primary
    log "Promoting read replica to primary..."
    aws rds promote-read-replica \
        --region $BACKUP_REGION \
        --db-instance-identifier justmaily-replica

    # Wait for promotion to complete
    aws rds wait db-instance-available \
        --region $BACKUP_REGION \
        --db-instance-identifier justmaily-replica

    # Update application configuration
    log "Updating application configuration..."
    aws ecs update-service \
        --region $BACKUP_REGION \
        --cluster justmaily-cluster \
        --service justmaily-backend \
        --force-new-deployment

    log "Database failover completed"
}

redis_failover() {
    log "Starting Redis failover procedure..."

    # Promote Redis replica to primary
    aws elasticache modify-replication-group \
        --region $BACKUP_REGION \
        --replication-group-id justmaily-redis \
        --primary-cluster-id justmaily-redis-002

    log "Redis failover completed"
}

application_failover() {
    log "Starting application failover procedure..."

    # Update Route 53 DNS
    CHANGE_ID=$(aws route53 change-resource-record-sets \
        --hosted-zone-id ZXXXXXXXXXXXXX \
        --change-batch file://dns-failover.json \
        --query 'ChangeInfo.Id' \
        --output text)

    # Wait for DNS changes to propagate
    aws route53 wait resource-record-sets-changed \
        --id $CHANGE_ID

    # Scale up backup region resources
    aws autoscaling update-auto-scaling-group \
        --region $BACKUP_REGION \
        --auto-scaling-group-name justmaily-asg \
        --min-size 2 \
        --max-size 10 \
        --desired-capacity 4

    log "Application failover completed"
}

verify_failover() {
    log "Verifying failover..."

    # Check new database connectivity
    DB_CHECK=$(aws rds describe-db-instances \
        --region $BACKUP_REGION \
        --db-instance-identifier justmaily-replica \
        --query 'DBInstances[0].DBInstanceStatus' \
        --output text)

    if [ "$DB_CHECK" != "available" ]; then
        log "ERROR: Database verification failed"
        return 1
    fi

    # Check application health
    HEALTH_CHECK=$(curl -s -o /dev/null -w "%{http_code}" https://app.justmaily.com/health)
    if [ "$HEALTH_CHECK" != "200" ]; then
        log "ERROR: Application health check failed"
        return 1
    fi

    log "Failover verification successful"
    return 0
}

cleanup() {
    log "Performing cleanup..."

    # Remove old resources after successful failover
    if [ "$COMPONENT" = "database" ]; then
        aws rds delete-db-instance \
            --region $REGION \
            --db-instance-identifier $PRIMARY_DB \
            --skip-final-snapshot
    fi
}

notify_team() {
    log "Sending notifications..."

    # Send SNS notification
    aws sns publish \
        --topic-arn arn:aws:sns:us-east-1:123456789012:dr-notifications \
        --message "Failover completed for $COMPONENT. Check logs: $LOG_FILE"
}

main() {
    log "Starting failover process for $COMPONENT in $REGION"

    check_prerequisites

    case $COMPONENT in
        "database")
            database_failover
            ;;
        "redis")
            redis_failover
            ;;
        "application")
            application_failover
            ;;
        *)
            log "ERROR: Invalid component. Use: database|redis|application"
            exit 1
            ;;
    esac

    if verify_failover; then
        cleanup
        notify_team
        log "Failover completed successfully"
    else
        log "ERROR: Failover verification failed"
        notify_team
        exit 1
    fi
}

main
