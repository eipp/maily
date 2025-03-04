#!/bin/bash
# configure-dns.sh
# Script to configure DNS for Maily

set -e

# Default values
DOMAIN="justmaily.com"
ENVIRONMENT="production"
DNS_PROVIDER="cloudflare"
CLOUDFLARE_API_TOKEN=""
ROUTE53_ACCESS_KEY=""
ROUTE53_SECRET_KEY=""
ROUTE53_HOSTED_ZONE_ID=""
LOAD_BALANCER_HOSTNAME=""
LOAD_BALANCER_IP=""
ENABLE_EXTERNAL_DNS=true
ENABLE_WILDCARD=true
ENABLE_APEX_DOMAIN=true
ENABLE_WWW=true
ENABLE_API=true
ENABLE_APP=true
ENABLE_MAIL=true
ENABLE_DMARC=true
ENABLE_SPF=true
ENABLE_DKIM=true
ENABLE_MX=true
ENABLE_TXT=true
ENABLE_CAA=true
ENABLE_DNSSEC=true
DKIM_SELECTOR="mail"
DKIM_PUBLIC_KEY=""
MX_RECORDS="10 mx1.justmaily.com,20 mx2.justmaily.com"
SPF_RECORD="v=spf1 mx a include:_spf.justmaily.com ~all"
DMARC_RECORD="v=DMARC1; p=reject; sp=reject; adkim=s; aspf=s; rua=mailto:dmarc@justmaily.com; ruf=mailto:dmarc@justmaily.com; fo=1; pct=100"
CAA_RECORDS="0 issue \"letsencrypt.org\",0 issuewild \"letsencrypt.org\",0 iodef \"mailto:security@justmaily.com\""
TTL=3600
PROXIED=true

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --domain)
      DOMAIN="$2"
      shift 2
      ;;
    --environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --dns-provider)
      DNS_PROVIDER="$2"
      shift 2
      ;;
    --cloudflare-api-token)
      CLOUDFLARE_API_TOKEN="$2"
      shift 2
      ;;
    --route53-access-key)
      ROUTE53_ACCESS_KEY="$2"
      shift 2
      ;;
    --route53-secret-key)
      ROUTE53_SECRET_KEY="$2"
      shift 2
      ;;
    --route53-hosted-zone-id)
      ROUTE53_HOSTED_ZONE_ID="$2"
      shift 2
      ;;
    --load-balancer-hostname)
      LOAD_BALANCER_HOSTNAME="$2"
      shift 2
      ;;
    --load-balancer-ip)
      LOAD_BALANCER_IP="$2"
      shift 2
      ;;
    --enable-external-dns)
      ENABLE_EXTERNAL_DNS="$2"
      shift 2
      ;;
    --enable-wildcard)
      ENABLE_WILDCARD="$2"
      shift 2
      ;;
    --enable-apex-domain)
      ENABLE_APEX_DOMAIN="$2"
      shift 2
      ;;
    --enable-www)
      ENABLE_WWW="$2"
      shift 2
      ;;
    --enable-api)
      ENABLE_API="$2"
      shift 2
      ;;
    --enable-app)
      ENABLE_APP="$2"
      shift 2
      ;;
    --enable-mail)
      ENABLE_MAIL="$2"
      shift 2
      ;;
    --enable-dmarc)
      ENABLE_DMARC="$2"
      shift 2
      ;;
    --enable-spf)
      ENABLE_SPF="$2"
      shift 2
      ;;
    --enable-dkim)
      ENABLE_DKIM="$2"
      shift 2
      ;;
    --enable-mx)
      ENABLE_MX="$2"
      shift 2
      ;;
    --enable-txt)
      ENABLE_TXT="$2"
      shift 2
      ;;
    --enable-caa)
      ENABLE_CAA="$2"
      shift 2
      ;;
    --enable-dnssec)
      ENABLE_DNSSEC="$2"
      shift 2
      ;;
    --dkim-selector)
      DKIM_SELECTOR="$2"
      shift 2
      ;;
    --dkim-public-key)
      DKIM_PUBLIC_KEY="$2"
      shift 2
      ;;
    --mx-records)
      MX_RECORDS="$2"
      shift 2
      ;;
    --spf-record)
      SPF_RECORD="$2"
      shift 2
      ;;
    --dmarc-record)
      DMARC_RECORD="$2"
      shift 2
      ;;
    --caa-records)
      CAA_RECORDS="$2"
      shift 2
      ;;
    --ttl)
      TTL="$2"
      shift 2
      ;;
    --proxied)
      PROXIED="$2"
      shift 2
      ;;
    *)
      echo "Unknown option: $1"
      exit 1
      ;;
  esac
done

# Function to check if a tool is installed
check_tool() {
  if ! command -v "$1" &> /dev/null; then
    echo "Error: $1 is not installed. Please install it first."
    return 1
  fi
  return 0
}

# Function to configure DNS using Cloudflare
configure_cloudflare_dns() {
  echo "Configuring DNS using Cloudflare..."
  
  if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo "Error: Cloudflare API token not provided."
    exit 1
  fi
  
  # Get Cloudflare Zone ID
  ZONE_ID=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones?name=$DOMAIN" \
    -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
    -H "Content-Type: application/json" | jq -r '.result[0].id')
  
  if [ -z "$ZONE_ID" ] || [ "$ZONE_ID" = "null" ]; then
    echo "Error: Could not find Cloudflare zone for domain $DOMAIN"
    exit 1
  fi
  
  # Function to create or update DNS record
  create_or_update_cloudflare_record() {
    local name="$1"
    local type="$2"
    local content="$3"
    local proxied="$4"
    local ttl="$5"
    
    # Check if record already exists
    local record_id=$(curl -s -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?type=$type&name=$name" \
      -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
      -H "Content-Type: application/json" | jq -r '.result[0].id')
    
    if [ -z "$record_id" ] || [ "$record_id" = "null" ]; then
      # Create new record
      echo "Creating $type record for $name..."
      curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
        -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
        -H "Content-Type: application/json" \
        --data "{\"type\":\"$type\",\"name\":\"$name\",\"content\":\"$content\",\"ttl\":$ttl,\"proxied\":$proxied}"
    else
      # Update existing record
      echo "Updating $type record for $name..."
      curl -s -X PUT "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$record_id" \
        -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
        -H "Content-Type: application/json" \
        --data "{\"type\":\"$type\",\"name\":\"$name\",\"content\":\"$content\",\"ttl\":$ttl,\"proxied\":$proxied}"
    fi
  }
  
  # Configure A/CNAME records for web services
  if [ "$ENABLE_APEX_DOMAIN" = true ]; then
    if [ -n "$LOAD_BALANCER_IP" ]; then
      create_or_update_cloudflare_record "$DOMAIN" "A" "$LOAD_BALANCER_IP" "$PROXIED" "$TTL"
    elif [ -n "$LOAD_BALANCER_HOSTNAME" ]; then
      create_or_update_cloudflare_record "$DOMAIN" "CNAME" "$LOAD_BALANCER_HOSTNAME" "$PROXIED" "$TTL"
    fi
  fi
  
  if [ "$ENABLE_WWW" = true ]; then
    create_or_update_cloudflare_record "www.$DOMAIN" "CNAME" "$DOMAIN" "$PROXIED" "$TTL"
  fi
  
  if [ "$ENABLE_API" = true ]; then
    create_or_update_cloudflare_record "api.$DOMAIN" "CNAME" "$DOMAIN" "$PROXIED" "$TTL"
  fi
  
  if [ "$ENABLE_APP" = true ]; then
    create_or_update_cloudflare_record "app.$DOMAIN" "CNAME" "$DOMAIN" "$PROXIED" "$TTL"
  fi
  
  if [ "$ENABLE_WILDCARD" = true ]; then
    create_or_update_cloudflare_record "*.$DOMAIN" "CNAME" "$DOMAIN" "$PROXIED" "$TTL"
  fi
  
  # Configure email-related records
  if [ "$ENABLE_MAIL" = true ]; then
    create_or_update_cloudflare_record "mail.$DOMAIN" "CNAME" "$DOMAIN" false "$TTL"
  fi
  
  if [ "$ENABLE_MX" = true ]; then
    IFS=',' read -ra MX_ARRAY <<< "$MX_RECORDS"
    for mx_record in "${MX_ARRAY[@]}"; do
      IFS=' ' read -ra MX_PARTS <<< "$mx_record"
      local priority="${MX_PARTS[0]}"
      local server="${MX_PARTS[1]}"
      
      # Cloudflare API requires priority to be part of the content
      create_or_update_cloudflare_record "$DOMAIN" "MX" "$priority $server" false "$TTL"
    done
  fi
  
  if [ "$ENABLE_SPF" = true ]; then
    create_or_update_cloudflare_record "$DOMAIN" "TXT" "$SPF_RECORD" false "$TTL"
  fi
  
  if [ "$ENABLE_DMARC" = true ]; then
    create_or_update_cloudflare_record "_dmarc.$DOMAIN" "TXT" "$DMARC_RECORD" false "$TTL"
  fi
  
  if [ "$ENABLE_DKIM" = true ] && [ -n "$DKIM_PUBLIC_KEY" ]; then
    create_or_update_cloudflare_record "$DKIM_SELECTOR._domainkey.$DOMAIN" "TXT" "v=DKIM1; k=rsa; p=$DKIM_PUBLIC_KEY" false "$TTL"
  fi
  
  if [ "$ENABLE_CAA" = true ]; then
    IFS=',' read -ra CAA_ARRAY <<< "$CAA_RECORDS"
    for caa_record in "${CAA_ARRAY[@]}"; do
      create_or_update_cloudflare_record "$DOMAIN" "CAA" "$caa_record" false "$TTL"
    done
  fi
  
  # Enable DNSSEC if requested
  if [ "$ENABLE_DNSSEC" = true ]; then
    echo "Enabling DNSSEC..."
    curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dnssec" \
      -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
      -H "Content-Type: application/json" \
      --data '{"status":"active"}'
  fi
  
  echo "Cloudflare DNS configuration completed successfully."
}

# Function to configure DNS using Route 53
configure_route53_dns() {
  echo "Configuring DNS using Route 53..."
  
  if [ -z "$ROUTE53_ACCESS_KEY" ] || [ -z "$ROUTE53_SECRET_KEY" ] || [ -z "$ROUTE53_HOSTED_ZONE_ID" ]; then
    echo "Error: Route 53 credentials or hosted zone ID not provided."
    exit 1
  fi
  
  # Set AWS credentials
  export AWS_ACCESS_KEY_ID="$ROUTE53_ACCESS_KEY"
  export AWS_SECRET_ACCESS_KEY="$ROUTE53_SECRET_KEY"
  export AWS_DEFAULT_REGION="us-east-1"
  
  # Function to create or update Route 53 record
  create_or_update_route53_record() {
    local name="$1"
    local type="$2"
    local value="$3"
    local ttl="$4"
    
    # Ensure name ends with a dot
    if [[ "$name" != *. ]]; then
      name="$name."
    fi
    
    # Create change batch file
    cat > /tmp/route53-change-batch.json << EOF
{
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "$name",
        "Type": "$type",
        "TTL": $ttl,
        "ResourceRecords": [
          {
            "Value": "$value"
          }
        ]
      }
    }
  ]
}
EOF
    
    # Apply change batch
    echo "Creating/updating $type record for $name..."
    aws route53 change-resource-record-sets \
      --hosted-zone-id "$ROUTE53_HOSTED_ZONE_ID" \
      --change-batch file:///tmp/route53-change-batch.json
  }
  
  # Function to create or update Route 53 alias record
  create_or_update_route53_alias() {
    local name="$1"
    local alias_target="$2"
    
    # Ensure name ends with a dot
    if [[ "$name" != *. ]]; then
      name="$name."
    fi
    
    # Create change batch file for alias
    cat > /tmp/route53-alias-change-batch.json << EOF
{
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "$name",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z2FDTNDATAQYW2",
          "DNSName": "$alias_target",
          "EvaluateTargetHealth": true
        }
      }
    }
  ]
}
EOF
    
    # Apply change batch
    echo "Creating/updating alias record for $name..."
    aws route53 change-resource-record-sets \
      --hosted-zone-id "$ROUTE53_HOSTED_ZONE_ID" \
      --change-batch file:///tmp/route53-alias-change-batch.json
  }
  
  # Configure A/CNAME records for web services
  if [ "$ENABLE_APEX_DOMAIN" = true ]; then
    if [ -n "$LOAD_BALANCER_IP" ]; then
      create_or_update_route53_record "$DOMAIN" "A" "$LOAD_BALANCER_IP" "$TTL"
    elif [ -n "$LOAD_BALANCER_HOSTNAME" ]; then
      create_or_update_route53_alias "$DOMAIN" "$LOAD_BALANCER_HOSTNAME"
    fi
  fi
  
  if [ "$ENABLE_WWW" = true ]; then
    create_or_update_route53_record "www.$DOMAIN" "CNAME" "$DOMAIN" "$TTL"
  fi
  
  if [ "$ENABLE_API" = true ]; then
    create_or_update_route53_record "api.$DOMAIN" "CNAME" "$DOMAIN" "$TTL"
  fi
  
  if [ "$ENABLE_APP" = true ]; then
    create_or_update_route53_record "app.$DOMAIN" "CNAME" "$DOMAIN" "$TTL"
  fi
  
  if [ "$ENABLE_WILDCARD" = true ]; then
    create_or_update_route53_record "*.$DOMAIN" "CNAME" "$DOMAIN" "$TTL"
  fi
  
  # Configure email-related records
  if [ "$ENABLE_MAIL" = true ]; then
    create_or_update_route53_record "mail.$DOMAIN" "CNAME" "$DOMAIN" "$TTL"
  fi
  
  if [ "$ENABLE_MX" = true ]; then
    IFS=',' read -ra MX_ARRAY <<< "$MX_RECORDS"
    
    # Create a combined change batch for all MX records
    cat > /tmp/route53-mx-change-batch.json << EOF
{
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "$DOMAIN.",
        "Type": "MX",
        "TTL": $TTL,
        "ResourceRecords": [
EOF
    
    for i in "${!MX_ARRAY[@]}"; do
      mx_record="${MX_ARRAY[$i]}"
      
      # Add comma for all but the last record
      if [ $i -lt $((${#MX_ARRAY[@]} - 1)) ]; then
        cat >> /tmp/route53-mx-change-batch.json << EOF
          {
            "Value": "$mx_record"
          },
EOF
      else
        cat >> /tmp/route53-mx-change-batch.json << EOF
          {
            "Value": "$mx_record"
          }
EOF
      fi
    done
    
    # Close the JSON structure
    cat >> /tmp/route53-mx-change-batch.json << EOF
        ]
      }
    }
  ]
}
EOF
    
    # Apply MX records change batch
    echo "Creating/updating MX records for $DOMAIN..."
    aws route53 change-resource-record-sets \
      --hosted-zone-id "$ROUTE53_HOSTED_ZONE_ID" \
      --change-batch file:///tmp/route53-mx-change-batch.json
  fi
  
  if [ "$ENABLE_SPF" = true ]; then
    create_or_update_route53_record "$DOMAIN" "TXT" "\"$SPF_RECORD\"" "$TTL"
  fi
  
  if [ "$ENABLE_DMARC" = true ]; then
    create_or_update_route53_record "_dmarc.$DOMAIN" "TXT" "\"$DMARC_RECORD\"" "$TTL"
  fi
  
  if [ "$ENABLE_DKIM" = true ] && [ -n "$DKIM_PUBLIC_KEY" ]; then
    create_or_update_route53_record "$DKIM_SELECTOR._domainkey.$DOMAIN" "TXT" "\"v=DKIM1; k=rsa; p=$DKIM_PUBLIC_KEY\"" "$TTL"
  fi
  
  if [ "$ENABLE_CAA" = true ]; then
    IFS=',' read -ra CAA_ARRAY <<< "$CAA_RECORDS"
    
    # Create a combined change batch for all CAA records
    cat > /tmp/route53-caa-change-batch.json << EOF
{
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "$DOMAIN.",
        "Type": "CAA",
        "TTL": $TTL,
        "ResourceRecords": [
EOF
    
    for i in "${!CAA_ARRAY[@]}"; do
      caa_record="${CAA_ARRAY[$i]}"
      
      # Add comma for all but the last record
      if [ $i -lt $((${#CAA_ARRAY[@]} - 1)) ]; then
        cat >> /tmp/route53-caa-change-batch.json << EOF
          {
            "Value": "$caa_record"
          },
EOF
      else
        cat >> /tmp/route53-caa-change-batch.json << EOF
          {
            "Value": "$caa_record"
          }
EOF
      fi
    done
    
    # Close the JSON structure
    cat >> /tmp/route53-caa-change-batch.json << EOF
        ]
      }
    }
  ]
}
EOF
    
    # Apply CAA records change batch
    echo "Creating/updating CAA records for $DOMAIN..."
    aws route53 change-resource-record-sets \
      --hosted-zone-id "$ROUTE53_HOSTED_ZONE_ID" \
      --change-batch file:///tmp/route53-caa-change-batch.json
  fi
  
  # Enable DNSSEC if requested
  if [ "$ENABLE_DNSSEC" = true ]; then
    echo "Enabling DNSSEC..."
    aws route53 enable-hosted-zone-dnssec \
      --hosted-zone-id "$ROUTE53_HOSTED_ZONE_ID"
  fi
  
  echo "Route 53 DNS configuration completed successfully."
}

# Function to configure External DNS for Kubernetes
configure_external_dns() {
  echo "Configuring External DNS for Kubernetes..."
  
  # Check if kubectl is installed
  if ! check_tool "kubectl"; then
    echo "Error: kubectl is not installed. Please install it first."
    exit 1
  fi
  
  # Check if helm is installed
  if ! check_tool "helm"; then
    echo "Error: helm is not installed. Please install it first."
    exit 1
  fi
  
  # Create namespace for external-dns
  kubectl create namespace external-dns --dry-run=client -o yaml | kubectl apply -f -
  
  # Create secret for DNS provider credentials
  if [ "$DNS_PROVIDER" = "cloudflare" ] && [ -n "$CLOUDFLARE_API_TOKEN" ]; then
    kubectl create secret generic cloudflare-api-token \
      --namespace external-dns \
      --from-literal=cloudflare_api_token="$CLOUDFLARE_API_TOKEN" \
      --dry-run=client -o yaml | kubectl apply -f -
  elif [ "$DNS_PROVIDER" = "route53" ] && [ -n "$ROUTE53_ACCESS_KEY" ] && [ -n "$ROUTE53_SECRET_KEY" ]; then
    kubectl create secret generic aws-credentials \
      --namespace external-dns \
      --from-literal=access-key="$ROUTE53_ACCESS_KEY" \
      --from-literal=secret-key="$ROUTE53_SECRET_KEY" \
      --dry-run=client -o yaml | kubectl apply -f -
  fi
  
  # Add Bitnami Helm repository
  helm repo add bitnami https://charts.bitnami.com/bitnami
  helm repo update
  
  # Create values file for external-dns
  cat > /tmp/external-dns-values.yaml << EOF
provider: $DNS_PROVIDER
domainFilters:
  - $DOMAIN
policy: sync
registry: txt
txtOwnerId: maily-$ENVIRONMENT
interval: 1m
sources:
  - service
  - ingress
EOF
  
  # Add provider-specific configuration
  if [ "$DNS_PROVIDER" = "cloudflare" ]; then
    cat >> /tmp/external-dns-values.yaml << EOF
cloudflare:
  apiToken: $CLOUDFLARE_API_TOKEN
  proxied: $PROXIED
EOF
  elif [ "$DNS_PROVIDER" = "route53" ]; then
    cat >> /tmp/external-dns-values.yaml << EOF
aws:
  region: us-east-1
  credentials:
    secretKey: $ROUTE53_SECRET_KEY
    accessKey: $ROUTE53_ACCESS_KEY
EOF
  fi
  
  # Install external-dns
  helm upgrade --install external-dns bitnami/external-dns \
    --namespace external-dns \
    -f /tmp/external-dns-values.yaml
  
  # Wait for external-dns to be ready
  kubectl -n external-dns rollout status deployment/external-dns
  
  echo "External DNS configuration completed successfully."
}

# Main execution
echo "Configuring DNS for $DOMAIN in $ENVIRONMENT environment..."

# Configure DNS based on provider
if [ "$DNS_PROVIDER" = "cloudflare" ]; then
  configure_cloudflare_dns
elif [ "$DNS_PROVIDER" = "route53" ]; then
  configure_route53_dns
else
  echo "Error: Unsupported DNS provider: $DNS_PROVIDER"
  exit 1
fi

# Configure External DNS for Kubernetes if enabled
if [ "$ENABLE_EXTERNAL_DNS" = true ]; then
  configure_external_dns
fi

echo "DNS configuration completed successfully."
echo
echo "Next steps:"
echo "1. Verify DNS records using dig or nslookup:"
echo "   dig $DOMAIN"
echo "   dig www.$DOMAIN"
echo "   dig api.$DOMAIN"
echo "2. Test DNS resolution:"
echo "   ping $DOMAIN"
echo "   ping www.$DOMAIN"
echo "   ping api.$DOMAIN"
echo "3. Verify email-related DNS records:"
echo "   dig $DOMAIN MX"
echo "   dig $DOMAIN TXT"
echo "   dig _dmarc.$DOMAIN TXT"
echo "4. Test email deliverability using a tool like mail-tester.com"
echo "5. Monitor DNS propagation"
