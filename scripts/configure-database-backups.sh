#!/bin/bash
# configure-database-backups.sh
# Script to configure database backups for Maily

set -e

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
  echo "Error: AWS CLI is not installed. Please install it first."
  exit 1
fi

# Check if AWS credentials are configured
if ! aws sts get-caller-identity &>/dev/null; then
  echo "Error: AWS credentials not configured or invalid."
  echo "Please configure your AWS credentials using 'aws configure' or environment variables."
  exit 1
fi

# Default values
AWS_REGION="us-east-1"
DB_INSTANCE_IDENTIFIER="maily-production"
BACKUP_RETENTION_PERIOD=7
BACKUP_WINDOW="03:00-04:00"
ENABLE_AUTOMATED_BACKUPS=true
ENABLE_SNAPSHOT_COPY=true
SNAPSHOT_COPY_REGION="us-west-2"
ENABLE_POINT_IN_TIME_RECOVERY=true
ENABLE_EXPORT_TO_S3=true
S3_BUCKET_NAME="maily-db-backups"
ENABLE_DAILY_SNAPSHOT=true
ENABLE_WEEKLY_SNAPSHOT=true
ENABLE_MONTHLY_SNAPSHOT=true
DAILY_SNAPSHOT_RETENTION=7
WEEKLY_SNAPSHOT_RETENTION=4
MONTHLY_SNAPSHOT_RETENTION=12

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --region)
      AWS_REGION="$2"
      shift 2
      ;;
    --db-instance-identifier)
      DB_INSTANCE_IDENTIFIER="$2"
      shift 2
      ;;
    --backup-retention-period)
      BACKUP_RETENTION_PERIOD="$2"
      shift 2
      ;;
    --backup-window)
      BACKUP_WINDOW="$2"
      shift 2
      ;;
    --enable-automated-backups)
      ENABLE_AUTOMATED_BACKUPS="$2"
      shift 2
      ;;
    --enable-snapshot-copy)
      ENABLE_SNAPSHOT_COPY="$2"
      shift 2
      ;;
    --snapshot-copy-region)
      SNAPSHOT_COPY_REGION="$2"
      shift 2
      ;;
    --enable-point-in-time-recovery)
      ENABLE_POINT_IN_TIME_RECOVERY="$2"
      shift 2
      ;;
    --enable-export-to-s3)
      ENABLE_EXPORT_TO_S3="$2"
      shift 2
      ;;
    --s3-bucket-name)
      S3_BUCKET_NAME="$2"
      shift 2
      ;;
    --enable-daily-snapshot)
      ENABLE_DAILY_SNAPSHOT="$2"
      shift 2
      ;;
    --enable-weekly-snapshot)
      ENABLE_WEEKLY_SNAPSHOT="$2"
      shift 2
      ;;
    --enable-monthly-snapshot)
      ENABLE_MONTHLY_SNAPSHOT="$2"
      shift 2
      ;;
    --daily-snapshot-retention)
      DAILY_SNAPSHOT_RETENTION="$2"
      shift 2
      ;;
    --weekly-snapshot-retention)
      WEEKLY_SNAPSHOT_RETENTION="$2"
      shift 2
      ;;
    --monthly-snapshot-retention)
      MONTHLY_SNAPSHOT_RETENTION="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Set AWS region
export AWS_DEFAULT_REGION=$AWS_REGION

# Check if the RDS instance exists
echo "Checking if RDS instance $DB_INSTANCE_IDENTIFIER exists..."
if ! aws rds describe-db-instances --db-instance-identifier $DB_INSTANCE_IDENTIFIER &>/dev/null; then
  echo "Error: RDS instance $DB_INSTANCE_IDENTIFIER not found."
  exit 1
fi

# Configure automated backups
if [ "$ENABLE_AUTOMATED_BACKUPS" = true ]; then
  echo "Configuring automated backups for RDS instance $DB_INSTANCE_IDENTIFIER..."
  aws rds modify-db-instance \
    --db-instance-identifier $DB_INSTANCE_IDENTIFIER \
    --backup-retention-period $BACKUP_RETENTION_PERIOD \
    --preferred-backup-window $BACKUP_WINDOW \
    --apply-immediately
  
  echo "Automated backups configured with retention period of $BACKUP_RETENTION_PERIOD days and backup window of $BACKUP_WINDOW."
fi

# Create S3 bucket for database exports if it doesn't exist
if [ "$ENABLE_EXPORT_TO_S3" = true ]; then
  echo "Checking if S3 bucket $S3_BUCKET_NAME exists..."
  if ! aws s3api head-bucket --bucket $S3_BUCKET_NAME 2>/dev/null; then
    echo "Creating S3 bucket $S3_BUCKET_NAME..."
    aws s3api create-bucket \
      --bucket $S3_BUCKET_NAME \
      --create-bucket-configuration LocationConstraint=$AWS_REGION
    
    # Enable versioning on the bucket
    aws s3api put-bucket-versioning \
      --bucket $S3_BUCKET_NAME \
      --versioning-configuration Status=Enabled
    
    # Enable encryption on the bucket
    aws s3api put-bucket-encryption \
      --bucket $S3_BUCKET_NAME \
      --server-side-encryption-configuration '{
        "Rules": [
          {
            "ApplyServerSideEncryptionByDefault": {
              "SSEAlgorithm": "AES256"
            }
          }
        ]
      }'
    
    # Set lifecycle policy for the bucket
    aws s3api put-bucket-lifecycle-configuration \
      --bucket $S3_BUCKET_NAME \
      --lifecycle-configuration '{
        "Rules": [
          {
            "ID": "Move to Glacier after 30 days",
            "Status": "Enabled",
            "Prefix": "",
            "Transitions": [
              {
                "Days": 30,
                "StorageClass": "GLACIER"
              }
            ],
            "Expiration": {
              "Days": 365
            }
          }
        ]
      }'
    
    echo "S3 bucket $S3_BUCKET_NAME created and configured."
  else
    echo "S3 bucket $S3_BUCKET_NAME already exists."
  fi
fi

# Create IAM role for RDS to export snapshots to S3
if [ "$ENABLE_EXPORT_TO_S3" = true ]; then
  echo "Creating IAM role for RDS to export snapshots to S3..."
  
  # Create IAM policy document
  cat > /tmp/rds-s3-export-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject*",
        "s3:ListBucket",
        "s3:GetObject*",
        "s3:DeleteObject*",
        "s3:GetBucketLocation"
      ],
      "Resource": [
        "arn:aws:s3:::$S3_BUCKET_NAME",
        "arn:aws:s3:::$S3_BUCKET_NAME/*"
      ]
    }
  ]
}
EOF
  
  # Create IAM policy
  POLICY_ARN=$(aws iam create-policy \
    --policy-name RDSExportToS3Policy \
    --policy-document file:///tmp/rds-s3-export-policy.json \
    --query 'Policy.Arn' \
    --output text 2>/dev/null || \
    aws iam list-policies \
      --scope Local \
      --query 'Policies[?PolicyName==`RDSExportToS3Policy`].Arn' \
      --output text)
  
  # Create IAM role trust policy document
  cat > /tmp/rds-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "export.rds.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
  
  # Create IAM role
  ROLE_ARN=$(aws iam create-role \
    --role-name RDSExportToS3Role \
    --assume-role-policy-document file:///tmp/rds-trust-policy.json \
    --query 'Role.Arn' \
    --output text 2>/dev/null || \
    aws iam get-role \
      --role-name RDSExportToS3Role \
      --query 'Role.Arn' \
      --output text)
  
  # Attach policy to role
  aws iam attach-role-policy \
    --role-name RDSExportToS3Role \
    --policy-arn $POLICY_ARN
  
  echo "IAM role for RDS to export snapshots to S3 created and configured."
  
  # Clean up temporary files
  rm -f /tmp/rds-s3-export-policy.json /tmp/rds-trust-policy.json
fi

# Create EventBridge rules for scheduled snapshots
if [ "$ENABLE_DAILY_SNAPSHOT" = true ] || [ "$ENABLE_WEEKLY_SNAPSHOT" = true ] || [ "$ENABLE_MONTHLY_SNAPSHOT" = true ]; then
  echo "Creating EventBridge rules for scheduled snapshots..."
  
  # Create IAM policy document for EventBridge to create RDS snapshots
  cat > /tmp/eventbridge-rds-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "rds:CreateDBSnapshot",
        "rds:AddTagsToResource",
        "rds:DeleteDBSnapshot"
      ],
      "Resource": [
        "arn:aws:rds:$AWS_REGION:*:db:$DB_INSTANCE_IDENTIFIER",
        "arn:aws:rds:$AWS_REGION:*:snapshot:*"
      ]
    }
  ]
}
EOF
  
  # Create IAM policy
  POLICY_ARN=$(aws iam create-policy \
    --policy-name EventBridgeRDSSnapshotPolicy \
    --policy-document file:///tmp/eventbridge-rds-policy.json \
    --query 'Policy.Arn' \
    --output text 2>/dev/null || \
    aws iam list-policies \
      --scope Local \
      --query 'Policies[?PolicyName==`EventBridgeRDSSnapshotPolicy`].Arn' \
      --output text)
  
  # Create IAM role trust policy document
  cat > /tmp/eventbridge-trust-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "events.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
EOF
  
  # Create IAM role
  ROLE_ARN=$(aws iam create-role \
    --role-name EventBridgeRDSSnapshotRole \
    --assume-role-policy-document file:///tmp/eventbridge-trust-policy.json \
    --query 'Role.Arn' \
    --output text 2>/dev/null || \
    aws iam get-role \
      --role-name EventBridgeRDSSnapshotRole \
      --query 'Role.Arn' \
      --output text)
  
  # Attach policy to role
  aws iam attach-role-policy \
    --role-name EventBridgeRDSSnapshotRole \
    --policy-arn $POLICY_ARN
  
  # Create Lambda function for snapshot management
  echo "Creating Lambda function for snapshot management..."
  
  # Create Lambda function code
  mkdir -p /tmp/lambda
  cat > /tmp/lambda/snapshot_manager.py << 'EOF'
import boto3
import os
import datetime
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    db_instance_id = event.get('db_instance_id')
    snapshot_type = event.get('snapshot_type', 'daily')
    retention_days = int(event.get('retention_days', 7))
    
    if not db_instance_id:
        logger.error("No DB instance ID provided")
        return {
            'statusCode': 400,
            'body': 'No DB instance ID provided'
        }
    
    rds = boto3.client('rds')
    
    # Create snapshot
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M')
    snapshot_id = f"{db_instance_id}-{snapshot_type}-{timestamp}"
    
    logger.info(f"Creating snapshot {snapshot_id} for DB instance {db_instance_id}")
    
    try:
        response = rds.create_db_snapshot(
            DBSnapshotIdentifier=snapshot_id,
            DBInstanceIdentifier=db_instance_id,
            Tags=[
                {
                    'Key': 'SnapshotType',
                    'Value': snapshot_type
                },
                {
                    'Key': 'CreatedBy',
                    'Value': 'AutomatedBackup'
                }
            ]
        )
        logger.info(f"Snapshot creation initiated: {response}")
    except Exception as e:
        logger.error(f"Error creating snapshot: {e}")
        return {
            'statusCode': 500,
            'body': f'Error creating snapshot: {str(e)}'
        }
    
    # Delete old snapshots
    try:
        # Get all snapshots for this DB instance
        snapshots = rds.describe_db_snapshots(
            DBInstanceIdentifier=db_instance_id,
            SnapshotType='manual'
        )
        
        # Filter snapshots by type
        filtered_snapshots = []
        for snapshot in snapshots['DBSnapshots']:
            # Check if snapshot has tags
            snapshot_tags = rds.list_tags_for_resource(
                ResourceName=snapshot['DBSnapshotArn']
            )['TagList']
            
            # Check if snapshot has the correct type tag
            for tag in snapshot_tags:
                if tag['Key'] == 'SnapshotType' and tag['Value'] == snapshot_type:
                    filtered_snapshots.append(snapshot)
                    break
        
        # Sort snapshots by creation time
        filtered_snapshots.sort(key=lambda x: x['SnapshotCreateTime'])
        
        # Keep only the most recent 'retention_days' snapshots
        snapshots_to_delete = filtered_snapshots[:-retention_days] if len(filtered_snapshots) > retention_days else []
        
        for snapshot in snapshots_to_delete:
            snapshot_id = snapshot['DBSnapshotIdentifier']
            logger.info(f"Deleting old snapshot: {snapshot_id}")
            rds.delete_db_snapshot(
                DBSnapshotIdentifier=snapshot_id
            )
    except Exception as e:
        logger.error(f"Error managing old snapshots: {e}")
        # Continue execution even if there's an error deleting old snapshots
    
    return {
        'statusCode': 200,
        'body': f'Snapshot {snapshot_id} created successfully'
    }
EOF
  
  # Create Lambda deployment package
  cd /tmp/lambda
  zip -r snapshot_manager.zip snapshot_manager.py
  
  # Create Lambda function
  LAMBDA_ARN=$(aws lambda create-function \
    --function-name RDSSnapshotManager \
    --runtime python3.9 \
    --role $ROLE_ARN \
    --handler snapshot_manager.lambda_handler \
    --zip-file fileb://snapshot_manager.zip \
    --timeout 60 \
    --query 'FunctionArn' \
    --output text 2>/dev/null || \
    aws lambda update-function-code \
      --function-name RDSSnapshotManager \
      --zip-file fileb://snapshot_manager.zip \
      --query 'FunctionArn' \
      --output text)
  
  # Create EventBridge rules
  if [ "$ENABLE_DAILY_SNAPSHOT" = true ]; then
    echo "Creating daily snapshot rule..."
    aws events put-rule \
      --name DailyRDSSnapshot \
      --schedule-expression "cron(0 1 * * ? *)" \
      --state ENABLED
    
    aws events put-targets \
      --rule DailyRDSSnapshot \
      --targets "[{\"Id\": \"1\", \"Arn\": \"$LAMBDA_ARN\", \"Input\": \"{\\\"db_instance_id\\\": \\\"$DB_INSTANCE_IDENTIFIER\\\", \\\"snapshot_type\\\": \\\"daily\\\", \\\"retention_days\\\": $DAILY_SNAPSHOT_RETENTION}\"}]"
  fi
  
  if [ "$ENABLE_WEEKLY_SNAPSHOT" = true ]; then
    echo "Creating weekly snapshot rule..."
    aws events put-rule \
      --name WeeklyRDSSnapshot \
      --schedule-expression "cron(0 2 ? * SUN *)" \
      --state ENABLED
    
    aws events put-targets \
      --rule WeeklyRDSSnapshot \
      --targets "[{\"Id\": \"1\", \"Arn\": \"$LAMBDA_ARN\", \"Input\": \"{\\\"db_instance_id\\\": \\\"$DB_INSTANCE_IDENTIFIER\\\", \\\"snapshot_type\\\": \\\"weekly\\\", \\\"retention_days\\\": $WEEKLY_SNAPSHOT_RETENTION}\"}]"
  fi
  
  if [ "$ENABLE_MONTHLY_SNAPSHOT" = true ]; then
    echo "Creating monthly snapshot rule..."
    aws events put-rule \
      --name MonthlyRDSSnapshot \
      --schedule-expression "cron(0 3 1 * ? *)" \
      --state ENABLED
    
    aws events put-targets \
      --rule MonthlyRDSSnapshot \
      --targets "[{\"Id\": \"1\", \"Arn\": \"$LAMBDA_ARN\", \"Input\": \"{\\\"db_instance_id\\\": \\\"$DB_INSTANCE_IDENTIFIER\\\", \\\"snapshot_type\\\": \\\"monthly\\\", \\\"retention_days\\\": $MONTHLY_SNAPSHOT_RETENTION}\"}]"
  fi
  
  # Add permission for EventBridge to invoke Lambda
  aws lambda add-permission \
    --function-name RDSSnapshotManager \
    --statement-id EventBridgeInvoke \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn $(aws events describe-rule --name DailyRDSSnapshot --query 'Arn' --output text)
  
  echo "EventBridge rules for scheduled snapshots created and configured."
  
  # Clean up temporary files
  rm -rf /tmp/lambda
  rm -f /tmp/eventbridge-rds-policy.json /tmp/eventbridge-trust-policy.json
fi

# Configure snapshot copy to another region
if [ "$ENABLE_SNAPSHOT_COPY" = true ]; then
  echo "Configuring snapshot copy to region $SNAPSHOT_COPY_REGION..."
  
  # Create EventBridge rule for snapshot copy
  cat > /tmp/snapshot-copy-policy.json << EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "rds:CopyDBSnapshot",
        "rds:AddTagsToResource",
        "rds:DeleteDBSnapshot"
      ],
      "Resource": [
        "arn:aws:rds:$AWS_REGION:*:snapshot:*",
        "arn:aws:rds:$SNAPSHOT_COPY_REGION:*:snapshot:*"
      ]
    }
  ]
}
EOF
  
  # Create IAM policy
  POLICY_ARN=$(aws iam create-policy \
    --policy-name RDSSnapshotCopyPolicy \
    --policy-document file:///tmp/snapshot-copy-policy.json \
    --query 'Policy.Arn' \
    --output text 2>/dev/null || \
    aws iam list-policies \
      --scope Local \
      --query 'Policies[?PolicyName==`RDSSnapshotCopyPolicy`].Arn' \
      --output text)
  
  # Create IAM role
  ROLE_ARN=$(aws iam create-role \
    --role-name RDSSnapshotCopyRole \
    --assume-role-policy-document file:///tmp/eventbridge-trust-policy.json \
    --query 'Role.Arn' \
    --output text 2>/dev/null || \
    aws iam get-role \
      --role-name RDSSnapshotCopyRole \
      --query 'Role.Arn' \
      --output text)
  
  # Attach policy to role
  aws iam attach-role-policy \
    --role-name RDSSnapshotCopyRole \
    --policy-arn $POLICY_ARN
  
  # Create Lambda function for snapshot copy
  echo "Creating Lambda function for snapshot copy..."
  
  # Create Lambda function code
  mkdir -p /tmp/lambda
  cat > /tmp/lambda/snapshot_copy.py << 'EOF'
import boto3
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    source_region = os.environ['SOURCE_REGION']
    target_region = os.environ['TARGET_REGION']
    
    # Get the snapshot details from the event
    source_snapshot_arn = event['detail']['SourceArn']
    source_snapshot_id = source_snapshot_arn.split(':')[-1]
    db_instance_id = event['detail']['SourceIdentifier']
    
    # Create a new snapshot ID for the target region
    target_snapshot_id = f"copy-{source_snapshot_id}-{target_region}"
    
    logger.info(f"Copying snapshot {source_snapshot_id} from {source_region} to {target_region} as {target_snapshot_id}")
    
    # Create RDS client for target region
    rds_target = boto3.client('rds', region_name=target_region)
    
    try:
        # Copy the snapshot to the target region
        response = rds_target.copy_db_snapshot(
            SourceDBSnapshotIdentifier=source_snapshot_arn,
            TargetDBSnapshotIdentifier=target_snapshot_id,
            CopyTags=True
        )
        logger.info(f"Snapshot copy initiated: {response}")
    except Exception as e:
        logger.error(f"Error copying snapshot: {e}")
        return {
            'statusCode': 500,
            'body': f'Error copying snapshot: {str(e)}'
        }
    
    return {
        'statusCode': 200,
        'body': f'Snapshot {source_snapshot_id} copied to {target_region} as {target_snapshot_id}'
    }
EOF
  
  # Create Lambda deployment package
  cd /tmp/lambda
  zip -r snapshot_copy.zip snapshot_copy.py
  
  # Create Lambda function
  LAMBDA_ARN=$(aws lambda create-function \
    --function-name RDSSnapshotCopy \
    --runtime python3.9 \
    --role $ROLE_ARN \
    --handler snapshot_copy.lambda_handler \
    --zip-file fileb://snapshot_copy.zip \
    --timeout 300 \
    --environment "Variables={SOURCE_REGION=$AWS_REGION,TARGET_REGION=$SNAPSHOT_COPY_REGION}" \
    --query 'FunctionArn' \
    --output text 2>/dev/null || \
    aws lambda update-function-code \
      --function-name RDSSnapshotCopy \
      --zip-file fileb://snapshot_copy.zip \
      --query 'FunctionArn' \
      --output text)
  
  # Update Lambda environment variables
  aws lambda update-function-configuration \
    --function-name RDSSnapshotCopy \
    --environment "Variables={SOURCE_REGION=$AWS_REGION,TARGET_REGION=$SNAPSHOT_COPY_REGION}"
  
  # Create EventBridge rule for snapshot creation events
  aws events put-rule \
    --name RDSSnapshotCreated \
    --event-pattern "{\"source\":[\"aws.rds\"],\"detail-type\":[\"RDS DB Snapshot Event\"],\"detail\":{\"EventCategories\":[\"backup\"],\"EventID\":[\"RDS-EVENT-0042\"],\"SourceIdentifier\":[\"$DB_INSTANCE_IDENTIFIER\"]}}" \
    --state ENABLED
  
  aws events put-targets \
    --rule RDSSnapshotCreated \
    --targets "[{\"Id\": \"1\", \"Arn\": \"$LAMBDA_ARN\"}]"
  
  # Add permission for EventBridge to invoke Lambda
  aws lambda add-permission \
    --function-name RDSSnapshotCopy \
    --statement-id EventBridgeInvoke \
    --action lambda:InvokeFunction \
    --principal events.amazonaws.com \
    --source-arn $(aws events describe-rule --name RDSSnapshotCreated --query 'Arn' --output text)
  
  echo "Snapshot copy to region $SNAPSHOT_COPY_REGION configured."
  
  # Clean up temporary files
  rm -rf /tmp/lambda
  rm -f /tmp/snapshot-copy-policy.json
fi

echo
echo "Database backup configuration completed successfully!"
echo
echo "Backup configuration summary:"
echo "- RDS instance: $DB_INSTANCE_IDENTIFIER"
echo "- Automated backups: $ENABLE_AUTOMATED_BACKUPS (retention: $BACKUP_RETENTION_PERIOD days, window: $BACKUP_WINDOW)"
echo "- Daily snapshots: $ENABLE_DAILY_SNAPSHOT (retention: $DAILY_SNAPSHOT_RETENTION snapshots)"
echo "- Weekly snapshots: $ENABLE_WEEKLY_SNAPSHOT (retention: $WEEKLY_SNAPSHOT_RETENTION snapshots)"
echo "- Monthly snapshots: $ENABLE_MONTHLY_SNAPSHOT (retention: $MONTHLY_SNAPSHOT_RETENTION snapshots)"
echo "- Snapshot copy to region: $ENABLE_SNAPSHOT_COPY (target region: $SNAPSHOT_COPY_REGION)"
echo "- Export to S3: $ENABLE_EXPORT_TO_S3 (bucket: $S3_BUCKET_NAME)"
echo
echo "Next steps:"
echo "1. Verify that automated backups are enabled in the RDS console"
echo "2. Test the backup and restore process"
echo "3. Set up monitoring and alerting for backup failures"
echo "4. Document the backup and restore procedures"
echo "5. Schedule regular backup testing"

echo "Done!"

# Check for dry-run mode
DRY_RUN=false
for arg in "$@"; do
  if [[ "$arg" == "--dry-run" ]]; then
    DRY_RUN=true
    echo "Running in dry-run mode. No changes will be made."
  fi
done

