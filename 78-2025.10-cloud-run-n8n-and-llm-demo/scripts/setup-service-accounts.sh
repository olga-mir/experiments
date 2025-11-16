#!/bin/bash
set -euo pipefail

# Validate required environment variables
required_vars=("PROJECT_ID")
for var in "${required_vars[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "Error: $var environment variable is not set"
        exit 1
    fi
done

echo "Setting up service accounts for Cloud Run services..."
echo "Project: $PROJECT_ID"
echo ""

# Service account names (must be 6-30 characters)
SERVICE_ACCOUNTS=("n8n-service" "gemma-service")

for SA_NAME in "${SERVICE_ACCOUNTS[@]}"; do
    SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

    # Check if service account exists
    if gcloud iam service-accounts describe "$SA_EMAIL" \
        --project="$PROJECT_ID" &>/dev/null; then
        echo "Service account $SA_EMAIL already exists"
    else
        echo "Creating service account $SA_NAME..."
        gcloud iam service-accounts create "$SA_NAME" \
            --project="$PROJECT_ID" \
            --display-name="Cloud Run service account for $SA_NAME" \
            --description="Service account for $SA_NAME Cloud Run service"
    fi
done

echo ""
echo "Service accounts setup completed!"
echo "Created service accounts:"
for SA_NAME in "${SERVICE_ACCOUNTS[@]}"; do
    echo "  - ${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
done
