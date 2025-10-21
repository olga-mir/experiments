#!/bin/bash
set -euo pipefail

# Validate required environment variables
required_vars=("PROJECT_ID" "REGION" "NETWORK")
for var in "${required_vars[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "Error: $var environment variable is not set"
        exit 1
    fi
done

ROUTER_NAME="cloud-nat-router"
NAT_NAME="cloud-nat-config"

echo "Setting up Cloud NAT for outbound internet access..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Network: $NETWORK"
echo ""

# Create Cloud Router if it doesn't exist
if ! gcloud compute routers describe "$ROUTER_NAME" \
    --project="$PROJECT_ID" \
    --region="$REGION" &>/dev/null; then

    echo "Creating Cloud Router $ROUTER_NAME..."
    gcloud compute routers create "$ROUTER_NAME" \
        --project="$PROJECT_ID" \
        --region="$REGION" \
        --network="$NETWORK"
else
    echo "Cloud Router $ROUTER_NAME already exists"
fi

# Create Cloud NAT configuration if it doesn't exist
if ! gcloud compute routers nats describe "$NAT_NAME" \
    --router="$ROUTER_NAME" \
    --project="$PROJECT_ID" \
    --region="$REGION" &>/dev/null; then

    echo "Creating Cloud NAT configuration $NAT_NAME..."
    gcloud compute routers nats create "$NAT_NAME" \
        --router="$ROUTER_NAME" \
        --project="$PROJECT_ID" \
        --region="$REGION" \
        --nat-all-subnet-ip-ranges \
        --auto-allocate-nat-external-ips
else
    echo "Cloud NAT configuration $NAT_NAME already exists"
fi

echo ""
echo "Cloud NAT setup completed!"
echo "Router: $ROUTER_NAME"
echo "NAT Config: $NAT_NAME"
echo ""
echo "Your bastion and Cloud Run services now have outbound internet access."
echo "Wait ~30 seconds for NAT to become active, then try installing packages again."
