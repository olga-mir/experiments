#!/bin/bash
set -euo pipefail

# Validate required environment variables
required_vars=("NETWORK" "SUBNETWORK" "PROJECT_ID" "REGION" "ZONE")
for var in "${required_vars[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "Error: $var environment variable is not set"
        exit 1
    fi
done

INSTANCE_NAME="bastion"

echo "Setting up bastion host..."
echo "Project: $PROJECT_ID"
echo "Zone: $ZONE"
echo "Network: $NETWORK"
echo "Subnet: $SUBNETWORK"
echo ""

# Check if bastion already exists
if gcloud compute instances describe "$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    --zone="$ZONE" &>/dev/null; then
    echo "Bastion VM $INSTANCE_NAME already exists. Skipping creation."
else
    echo "Creating bastion VM $INSTANCE_NAME..."
    gcloud compute instances create "$INSTANCE_NAME" \
        --project="$PROJECT_ID" \
        --zone="$ZONE" \
        --machine-type="e2-micro" \
        --subnet="$SUBNETWORK" \
        --no-address \
        --image-family="debian-12" \
        --image-project="debian-cloud" \
        --metadata="enable-oslogin=true" \
        --scopes="cloud-platform" \
        --tags="allow-iap"

    echo "Waiting for VM to be ready and IAP tunnel to be available..."
    sleep 30

    echo "Installing required packages on bastion..."
    # Retry SSH connection up to 3 times with delays
    max_attempts=3
    attempt=1
    while [ $attempt -le $max_attempts ]; do
        echo "SSH attempt $attempt/$max_attempts..."
        if gcloud compute ssh "$INSTANCE_NAME" \
            --project="$PROJECT_ID" \
            --zone="$ZONE" \
            --tunnel-through-iap \
            --command='sudo apt-get update && sudo apt-get install -y curl' 2>/dev/null; then
            echo "Successfully installed packages!"
            break
        else
            if [ $attempt -lt $max_attempts ]; then
                echo "SSH failed, waiting 15 seconds before retry..."
                sleep 15
            else
                echo "WARNING: Failed to install packages after $max_attempts attempts."
                echo "You can manually install curl later by running:"
                echo "  gcloud compute ssh $INSTANCE_NAME --project=$PROJECT_ID --zone=$ZONE --tunnel-through-iap --command='sudo apt-get update && sudo apt-get install -y curl'"
            fi
        fi
        attempt=$((attempt + 1))
    done
fi

echo ""
echo "Bastion VM ready: $INSTANCE_NAME"
echo "To connect: gcloud compute ssh $INSTANCE_NAME --project=$PROJECT_ID --zone=$ZONE --tunnel-through-iap"
