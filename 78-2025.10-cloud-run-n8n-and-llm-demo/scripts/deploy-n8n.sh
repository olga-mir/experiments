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

# Use custom domain if provided, otherwise use Cloud Run URL
# For ALB setup, set DOMAIN_NAME="n8n-gdg....."
if [ -z "${DOMAIN_NAME:-}" ]; then
    # Default: Construct predictable Cloud Run URL using PROJECT_NUMBER format
    # Format: https://SERVICE_NAME-PROJECT_NUMBER.REGION.run.app
    N8N_HOST="${SERVICE_NAME}-${PROJECT_NUMBER}.${REGION}.run.app"
else
    # Use custom domain from ALB
    N8N_HOST="$DOMAIN_NAME"
fi

N8N_URL="https://${N8N_HOST}"

echo "Deploying n8n to Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Project Number: $PROJECT_NUMBER"
echo "Region: $REGION"
echo "Service Account: $SERVICE_ACCOUNT"
echo "Network: $NETWORK"
echo "Subnet: $SUBNETWORK"
echo "N8N Host: $N8N_HOST"
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
    --network-tags=allow-model-access \
    --no-default-url \
    --set-env-vars="N8N_PORT=5678,N8N_PROTOCOL=https,N8N_HOST=${N8N_HOST},GENERIC_TIMEZONE=UTC,N8N_BASIC_AUTH_ACTIVE=false,N8N_EDITOR_BASE_URL=${N8N_URL},WEBHOOK_URL=${N8N_URL}"
