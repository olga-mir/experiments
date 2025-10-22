#!/bin/bash
set -euo pipefail

# Validate required environment variables
required_vars=("PROJECT_ID" "PROJECT_NUMBER" "REGION" "NETWORK" "SUBNETWORK")
for var in "${required_vars[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "Error: $var environment variable is not set"
        exit 1
    fi
done

SERVICE_NAME="n8n"
SERVICE_ACCOUNT="n8n-service@${PROJECT_ID}.iam.gserviceaccount.com"

# Construct predictable Cloud Run URL using PROJECT_NUMBER format
# Format: https://SERVICE_NAME-PROJECT_NUMBER.REGION.run.app
N8N_URL="https://${SERVICE_NAME}-${PROJECT_NUMBER}.${REGION}.run.app"

echo "Deploying n8n to Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Project Number: $PROJECT_NUMBER"
echo "Region: $REGION"
echo "Service Account: $SERVICE_ACCOUNT"
echo "Network: $NETWORK"
echo "Subnet: $SUBNETWORK"
echo "N8N URL: $N8N_URL"
echo ""

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
    --ingress=internal-and-cloud-load-balancing \
    --vpc-egress=all-traffic \
    --execution-environment=gen2 \
    --service-account="$SERVICE_ACCOUNT" \
    --set-env-vars="N8N_PORT=5678,N8N_PROTOCOL=https,N8N_HOST=${SERVICE_NAME}-${PROJECT_NUMBER}.${REGION}.run.app,GENERIC_TIMEZONE=UTC,N8N_BASIC_AUTH_ACTIVE=false,N8N_EDITOR_BASE_URL=${N8N_URL},WEBHOOK_URL=${N8N_URL}"

echo ""
echo "n8n deployment completed!"
echo ""
echo "Get service URL with: task get-n8n-url"
echo "Connect to bastion: task vpc:connect-bastion"
