# Maily Operational Runbooks

This directory contains operational runbooks for common issues and procedures encountered in the Maily platform. These runbooks provide step-by-step instructions for resolving issues and performing routine operations.

## Table of Contents

### Incident Response
- [General Incident Response Process](incident-response/general-process.md)
- [High Severity Incident Handling](incident-response/high-severity.md)
- [Postmortem Template](incident-response/postmortem-template.md)

### Service Outages
- [API Service Outage](service-outages/api-outage.md)
- [Database Service Outage](service-outages/database-outage.md)
- [Email Service Outage](service-outages/email-service-outage.md)
- [AI Service Outage](service-outages/ai-service-outage.md)
- [Frontend Service Outage](service-outages/frontend-outage.md)

### Performance Issues
- [API Latency Troubleshooting](performance/api-latency.md)
- [Database Performance Issues](performance/database-performance.md)
- [Memory Leaks Investigation](performance/memory-leaks.md)
- [Slow Queries Remediation](performance/slow-queries.md)

### Security Incidents
- [Data Breach Response](security/data-breach-response.md)
- [Account Compromise](security/account-compromise.md)
- [Unusual Traffic Patterns](security/unusual-traffic.md)
- [Vulnerability Management](security/vulnerability-management.md)

### Routine Operations
- [Backup and Restore](routine-operations/backup-restore.md)
- [Deployment Procedures](routine-operations/deployment.md)
- [Secret Rotation](routine-operations/secret-rotation.md)
- [Database Maintenance](routine-operations/database-maintenance.md)
- [Certificate Renewal](routine-operations/certificate-renewal.md)

### Monitoring and Alerting
- [Alert Response Guidelines](monitoring/alert-response.md)
- [SLA Monitoring](monitoring/sla-monitoring.md)
- [Setting Up New Alerts](monitoring/setting-up-alerts.md)
- [False Positive Management](monitoring/false-positives.md)

### Disaster Recovery
- [Disaster Recovery Plan](disaster-recovery/dr-plan.md)
- [Failover Procedures](disaster-recovery/failover.md)
- [Data Recovery](disaster-recovery/data-recovery.md)
- [Service Restoration Priority](disaster-recovery/restoration-priority.md)

### Scaling and Capacity Planning
- [Horizontal Scaling](scaling/horizontal-scaling.md)
- [Vertical Scaling](scaling/vertical-scaling.md)
- [Capacity Planning](scaling/capacity-planning.md)
- [Load Testing Interpretation](scaling/load-testing.md)

## How to Use These Runbooks

1. **During an incident**: Use the appropriate runbook to guide your response, following the steps provided.
2. **For routine operations**: Use the relevant runbook to ensure consistent execution of operational tasks.
3. **For training**: Use these runbooks to train new team members on operational procedures.

## Contributing to Runbooks

To contribute to these runbooks:

1. Follow the template provided in [runbook-template.md](runbook-template.md)
2. Submit your changes via a pull request
3. Ensure your runbook includes:
   - Clear problem definition
   - Step-by-step resolution steps
   - Verification steps
   - Related alerts and metrics
   - Relevant commands or scripts

## Runbook Maintenance

All runbooks should be reviewed and updated at least quarterly. The person on runbook duty each month is responsible for reviewing a designated section of the runbooks.

## Automation Status

Some runbooks have associated automation. The status is indicated in each runbook:
- 🤖 **Fully Automated**: The entire process is automated
- 🧑‍💻 **Partially Automated**: Some steps are automated, but manual intervention is required
- 📝 **Manual Process**: The process is entirely manual
