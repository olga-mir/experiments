#!/bin/bash
set -euo pipefail

# for now drop VM in the same subnet as the cloudruns
SUBNET_VM=$SUBNETWORK

# Validate required environment variables
required_vars=("NETWORK" "SUBNETWORK" "SUBNET_VM" "PROJECT_ID" "REGION")
for var in "${required_vars[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "Error: $var environment variable is not set"
        exit 1
    fi
done

IAP_RANGE="35.235.240.0/20"

# Create subnet for VM if it doesn't exist
if ! gcloud compute networks subnets describe "$SUBNET_VM" \
    --project="$PROJECT_ID" \
    --region="$REGION" &>/dev/null; then

    echo "Creating subnet $SUBNET_VM..."
    gcloud compute networks subnets create "$SUBNET_VM" \
        --project="$PROJECT_ID" \
        --region="$REGION" \
        --network="$NETWORK" \
        --range="10.0.1.0/28"
fi

# Create firewall rule for IAP tunnel if it doesn't exist
FW_RULE_IAP="allow-iap-tunnel"
if ! gcloud compute firewall-rules describe "$FW_RULE_IAP" \
    --project="$PROJECT_ID" &>/dev/null; then

    echo "Creating IAP tunnel firewall rule..."
    gcloud compute firewall-rules create "$FW_RULE_IAP" \
        --project="$PROJECT_ID" \
        --network="$NETWORK" \
        --direction=INGRESS \
        --action=ALLOW \
        --rules=tcp:22 \
        --source-ranges=$IAP_RANGE
fi

# Create firewall rule for internal access to Cloud Run if it doesn't exist
FW_RULE_INTERNAL="allow-internal-cloud-run"
if ! gcloud compute firewall-rules describe "$FW_RULE_INTERNAL" \
    --project="$PROJECT_ID" &>/dev/null; then

    echo "Creating internal Cloud Run access firewall rule..."
    gcloud compute firewall-rules create "$FW_RULE_INTERNAL" \
        --project="$PROJECT_ID" \
        --network="$NETWORK" \
        --direction=EGRESS \
        --action=ALLOW \
        --rules=tcp:80,tcp:443 \
        --destination-ranges="$(gcloud compute networks subnets describe "$SUBNET_VM" \
            --project="$PROJECT_ID" \
            --region="$REGION" \
            --format='get(ipCidrRange)')"
fi

# Create bastion VM
INSTANCE_NAME="bastion-$(date +%s)"
echo "Creating bastion VM $INSTANCE_NAME..."
gcloud compute instances create "$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    --zone="${REGION}-b" \
    --machine-type="e2-micro" \
    --subnet="$SUBNET_VM" \
    --no-address \
    --image-family="debian-12" \
    --image-project="debian-cloud" \
    --metadata="enable-oslogin=true" \
    --scopes="cloud-platform"

echo "Installing required packages on bastion..."
gcloud compute ssh "$INSTANCE_NAME" \
    --project="$PROJECT_ID" \
    --zone="${REGION}-b" \
    --tunnel-through-iap \
    --command='sudo apt-get update && sudo apt-get install -y curl'