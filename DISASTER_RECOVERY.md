# Disaster Recovery Plan

## Overview
This document outlines the disaster recovery procedures for the Maily application, covering both frontend and backend components, databases, and infrastructure.

## Critical Systems
- PostgreSQL Database
- Redis Cache
- File Storage (S3/equivalent)
- Frontend Application (Next.js)
- Backend API (FastAPI)
- Authentication Services
- Email Service Providers

## Backup Procedures

### Database Backups
1. **Automated Daily Backups**
   ```bash
   # AWS RDS Automated Backup Configuration
   aws rds modify-db-instance \
     --db-instance-identifier maily-prod \
     --backup-retention-period 35 \
     --preferred-backup-window "00:00-01:00" \
     --copy-tags-to-snapshot \
     --deletion-protection \
     --apply-immediately

   # Cross-Region Replication
   aws rds create-db-instance-read-replica \
     --db-instance-identifier maily-prod-replica \
     --source-db-instance-identifier maily-prod \
     --source-region us-east-1 \
     --destination-region us-west-2
   ```

2. **Backup Retention**
   - Daily backups: 35 days retention (automated)
   - Weekly backups: 52 weeks retention (manual)
   - Monthly backups: 12 months retention (manual)
   - Cross-region replicas: Real-time replication

3. **Backup Verification**
   ```bash
   # Automated daily backup verification
   #!/bin/bash
   # /usr/local/bin/verify_backups.sh
   
   # Verify RDS snapshot
   aws rds describe-db-snapshots \
     --db-instance-identifier maily-prod \
     --snapshot-type automated \
     --query 'DBSnapshots[?Status==`available`].DBSnapshotIdentifier' \
     --output text | while read -r snapshot; do
     aws rds describe-db-snapshots \
       --db-snapshot-identifier "$snapshot" \
       --query 'DBSnapshots[].Status' \
       --output text
   done

   # Verify replica lag
   aws rds describe-db-instances \
     --db-instance-identifier maily-prod-replica \
     --query 'DBInstances[].ReplicaLag' \
     --output text
   ```

### Redis Cache
- Persistence Configuration:
  ```bash
  # /etc/redis/redis.conf
  save 900 1           # Save if at least 1 key changed in 15 minutes
  save 300 10          # Save if at least 10 keys changed in 5 minutes
  save 60 10000        # Save if at least 10000 keys changed in 1 minute
  
  appendonly yes
  appendfsync everysec
  
  # Replication configuration
  replicaof master.maily-redis.xxx.ng.0001.use1.cache.amazonaws.com 6379
  ```

### File Storage
- S3 Cross-Region Replication:
  ```bash
  # Enable versioning
  aws s3api put-bucket-versioning \
    --bucket maily-prod \
    --versioning-configuration Status=Enabled

  # Configure replication
  aws s3api put-bucket-replication \
    --bucket maily-prod \
    --replication-configuration file://replication.json
  ```

## Automated Failover Configuration

### Database Failover
1. **Multi-AZ Configuration**
   ```bash
   aws rds modify-db-instance \
     --db-instance-identifier maily-prod \
     --multi-az \
     --apply-immediately
   ```

2. **Cross-Region Failover**
   ```bash
   # Monitor primary health
   aws cloudwatch put-metric-alarm \
     --alarm-name maily-db-health \
     --metric-name StatusCheckFailed \
     --namespace AWS/RDS \
     --period 60 \
     --evaluation-periods 2 \
     --threshold 1 \
     --comparison-operator GreaterThanThreshold \
     --alarm-actions arn:aws:sns:us-east-1:123456789012:db-failover

   # Automated failover Lambda function
   aws lambda create-function \
     --function-name maily-db-failover \
     --runtime python3.9 \
     --handler index.handler \
     --role arn:aws:iam::123456789012:role/db-failover-role \
     --code S3Bucket=maily-lambda,S3Key=db-failover.zip
   ```

### Application Failover
1. **Route 53 Health Checks**
   ```bash
   aws route53 create-health-check \
     --caller-reference $(date +%s) \
     --health-check-config file://health-check.json

   # Configure DNS failover
   aws route53 change-resource-record-sets \
     --hosted-zone-id ZXXXXXXXXXXXXX \
     --change-batch file://dns-failover.json
   ```

## Quarterly Disaster Recovery Drills

### Schedule
1. **Q1 Drill (January)**
   - Database failover testing
   - Cross-region replication verification
   - Recovery time measurement

2. **Q2 Drill (April)**
   - Application deployment rollback
   - Cache recovery procedures
   - Communication plan testing

3. **Q3 Drill (July)**
   - Full system recovery
   - Data integrity verification
   - Performance testing post-recovery

4. **Q4 Drill (October)**
   - Multi-region failover
   - Backup restoration testing
   - Documentation review and updates

### Drill Results Documentation
```markdown
# Disaster Recovery Drill Report Template

## Drill Information
- Date: YYYY-MM-DD
- Type: [Database/Application/Full System]
- Participants: [Team Members]

## Objectives
1. [Specific test objectives]
2. [Success criteria]

## Results
- Recovery Time: XX minutes
- Data Loss: None/XXX records
- Issues Encountered: [List issues]

## Action Items
1. [Improvements needed]
2. [Process updates]

## Sign-off
- DevOps Lead: [Name]
- Database Admin: [Name]
- System Owner: [Name]
```

## Recovery Procedures

### Database Recovery
1. **Full Database Restore**
   ```bash
   pg_restore -d maily_new backup.dump
   ```

2. **Point-in-Time Recovery**
   ```bash
   # Using AWS RDS or equivalent
   aws rds restore-db-instance-to-point-in-time \
     --source-db-instance-identifier maily-prod \
     --target-db-instance-identifier maily-recovery \
     --restore-time "2024-03-21T23:45:00Z"
   ```

### Redis Recovery
1. **From RDB**
   ```bash
   redis-cli config set dir /var/lib/redis
   redis-cli config set dbfilename dump.rdb
   ```

2. **From AOF**
   ```bash
   redis-cli config set appendonly yes
   redis-cli config set appendfilename "appendonly.aof"
   ```

### Application Recovery

1. **Frontend**
   ```bash
   # Restore from latest deployment
   git checkout main
   npm ci
   npm run build
   ```

2. **Backend**
   ```bash
   # Restore from latest deployment
   git checkout main
   pip install -r requirements.txt
   uvicorn main:app
   ```

## Disaster Scenarios and Response

### Database Failure
1. **Immediate Actions**
   - Switch to read replica if available
   - Notify engineering team
   - Begin recovery assessment

2. **Recovery Steps**
   - Identify failure cause
   - Restore from latest backup
   - Verify data integrity
   - Switch application to restored database

### Application Failure
1. **Frontend**
   - Deploy previous known-good version
   - Clear CDN cache if necessary
   - Verify static assets

2. **Backend**
   - Scale down to minimum instances
   - Deploy last stable version
   - Gradually scale up with monitoring

### Infrastructure Failure
1. **Region Failure**
   - Switch DNS to backup region
   - Activate backup infrastructure
   - Scale up backup resources

2. **Provider Failure**
   - Switch to backup provider if configured
   - Update DNS records
   - Scale up backup infrastructure

## Recovery Time Objectives (RTO)

| Component | RTO |
|-----------|-----|
| Database | 1 hour |
| Redis Cache | 15 minutes |
| Frontend | 15 minutes |
| Backend API | 30 minutes |
| Full System | 2 hours |

## Recovery Point Objectives (RPO)

| Component | RPO |
|-----------|-----|
| Database | 5 minutes |
| Redis Cache | 1 hour |
| File Storage | Real-time |

## Communication Plan

### Internal Communication
1. **First Response**
   - Use PagerDuty for initial alerts
   - Slack channel #incident-response for updates
   - Video call bridge for critical incidents

2. **Status Updates**
   - Regular updates every 30 minutes
   - Incident commander designated for coordination
   - Documentation in real-time

### External Communication
1. **Customer Communication**
   - Status page updates
   - Email notifications for major incidents
   - Social media updates if necessary

2. **Stakeholder Updates**
   - Regular briefings to management
   - Impact assessment reports
   - Post-incident analysis

## Testing and Maintenance

### Regular Testing
1. **Quarterly Tests**
   - Database restore procedures
   - Application deployment rollbacks
   - Cross-region failover
   - Communication procedures

2. **Documentation Updates**
   - Review and update after each test
   - Update contact information
   - Revise procedures based on lessons learned

### Maintenance Schedule
1. **Monthly**
   - Verify backup integrity
   - Test monitoring systems
   - Update emergency contact list

2. **Quarterly**
   - Full disaster recovery drill
   - Update recovery procedures
   - Review and update RTO/RPO targets

## Incident Response Runbook

### Initial Response
1. **Incident Detection**
   - Automated monitoring alerts
   - User-reported issues
   - System performance degradation

2. **Assessment**
   - Identify affected systems
   - Determine incident severity
   - Establish incident command

### Recovery Execution
1. **Containment**
   - Isolate affected systems
   - Prevent cascade failures
   - Implement temporary workarounds

2. **Recovery**
   - Execute relevant recovery procedures
   - Verify system restoration
   - Monitor for secondary issues

### Post-Incident
1. **Analysis**
   - Root cause analysis
   - Document lessons learned
   - Update procedures if necessary

2. **Reporting**
   - Generate incident report
   - Update stakeholders
   - Plan preventive measures

## Contacts and Escalation

### Primary Contacts
- **DevOps Lead**: [Contact Information]
- **Database Admin**: [Contact Information]
- **Security Team**: [Contact Information]
- **Infrastructure Team**: [Contact Information]

### Escalation Path
1. On-call Engineer
2. Team Lead
3. Engineering Manager
4. CTO
5. CEO

## Appendix

### Useful Commands
```bash
# Quick database backup
pg_dump -Fc maily > backup.dump

# Quick database restore
pg_restore -d maily backup.dump

# Redis backup
redis-cli save

# Check system status
systemctl status nginx postgresql redis
```

### Monitoring Dashboard URLs
- Grafana: https://grafana.maily.com
- Prometheus: https://prometheus.maily.com
- Application Metrics: https://metrics.maily.com

### Reference Architecture
[Include architecture diagram]

### Compliance Requirements
- Data retention policies
- Security protocols
- Audit requirements 