#!/bin/bash
set -euo pipefail

# Validate required environment variables
required_vars=("PROJECT_ID" "REGION" "NETWORK" "SUBNETWORK")
for var in "${required_vars[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "Error: $var environment variable is not set"
        exit 1
    fi
done

SERVICE_NAME="n8n"
SERVICE_ACCOUNT="n8n-service@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud run deploy "$SERVICE_NAME" \
    --project="$PROJECT_ID" \
    --image=n8nio/n8n \
    --region="$REGION" \
    --no-allow-unauthenticated \
    --port=5678 \
    --no-cpu-throttling \
    --memory=2Gi \
    --network="$NETWORK" \
    --subnet="$SUBNETWORK" \
    --ingress=internal \
    --vpc-egress=all-traffic \
    --execution-environment=gen2 \
    --service-account="$SERVICE_ACCOUNT"

echo ""
echo "n8n deployment completed!"
echo ""
echo "Get service URL with: task get-n8n-url"
echo "Connect to bastion: task vpc:connect-bastion"
