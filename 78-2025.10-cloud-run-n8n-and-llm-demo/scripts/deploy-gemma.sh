#!/bin/bash
set -euo pipefail

# Validate required environment variables
required_vars=("PROJECT_ID" "NETWORK" "SUBNETWORK")
for var in "${required_vars[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "Error: $var environment variable is not set"
        exit 1
    fi
done

SERVICE_NAME="gemma-model"
SERVICE_ACCOUNT="gemma-service@${PROJECT_ID}.iam.gserviceaccount.com"

# GPU configuration for nvidia-l4 is only supported in specific regions
# ERROR: (gcloud.beta.run.deploy) spec.template.spec.node_selector:
# GPU configuration for nvidia-l4 is only supported in regions:
# asia-southeast1, europe-west4, europe-west1, us-central1, us-east4
LOCATION="asia-southeast1"

echo "Deploying Gemma LLM model to Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Region: $LOCATION"
echo "Service Account: $SERVICE_ACCOUNT"
echo "Network: $NETWORK"
echo "Subnet: $SUBNETWORK"
echo ""

gcloud run deploy "$SERVICE_NAME" \
    --project="$PROJECT_ID" \
    --image=us-docker.pkg.dev/cloudrun/container/gemma/gemma3-4b \
    --region="$LOCATION" \
    --no-allow-unauthenticated \
    --concurrency=4 \
    --cpu=4 \
    --set-env-vars=OLLAMA_NUM_PARALLEL=4 \
    --gpu=1 \
    --gpu-type=nvidia-l4 \
    --min-instances=1 \
    --max-instances=1 \
    --memory=16Gi \
    --service-account="$SERVICE_ACCOUNT" \
    --no-cpu-throttling \
    --timeout=600 \
    --network="$NETWORK" \
    --subnet="$SUBNETWORK" \
    --ingress=internal \
    --vpc-egress=all-traffic \
    --execution-environment=gen2
