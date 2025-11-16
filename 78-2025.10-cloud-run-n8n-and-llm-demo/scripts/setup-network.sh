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

echo "Setting up VPC network infrastructure..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Network: $NETWORK"
echo "Subnetwork: $SUBNETWORK"
echo ""

# Create VPC network if it doesn't exist
if ! gcloud compute networks describe "$NETWORK" \
    --project="$PROJECT_ID" &>/dev/null; then

    echo "Creating VPC network $NETWORK..."
    gcloud compute networks create "$NETWORK" \
        --project="$PROJECT_ID" \
        --subnet-mode=custom \
        --bgp-routing-mode=regional
else
    echo "VPC network $NETWORK already exists"
fi

# Create subnet for Cloud Run if it doesn't exist
if ! gcloud compute networks subnets describe "$SUBNETWORK" \
    --project="$PROJECT_ID" \
    --region="$REGION" &>/dev/null; then

    echo "Creating subnet $SUBNETWORK..."
    gcloud compute networks subnets create "$SUBNETWORK" \
        --project="$PROJECT_ID" \
        --region="$REGION" \
        --network="$NETWORK" \
        --range="10.0.0.0/24"
else
    echo "Subnet $SUBNETWORK already exists"
fi

# Enable Private Google Access for the subnet
echo "Enabling Private Google Access on subnet $SUBNETWORK..."
gcloud compute networks subnets update "$SUBNETWORK" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --enable-private-ip-google-access

# Create firewall rule for IAP tunnel if it doesn't exist
IAP_RANGE="35.235.240.0/20"
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
        --source-ranges=$IAP_RANGE \
        --target-tags=allow-iap
else
    echo "IAP tunnel firewall rule already exists"
fi

# Create firewall rule for internal communication
FW_RULE_INTERNAL="allow-internal-all"
if ! gcloud compute firewall-rules describe "$FW_RULE_INTERNAL" \
    --project="$PROJECT_ID" &>/dev/null; then

    echo "Creating internal communication firewall rule..."
    gcloud compute firewall-rules create "$FW_RULE_INTERNAL" \
        --project="$PROJECT_ID" \
        --network="$NETWORK" \
        --direction=INGRESS \
        --action=ALLOW \
        --rules=tcp,udp,icmp \
        --source-ranges=10.0.0.0/8
else
    echo "Internal communication firewall rule already exists"
fi

echo ""
echo "Network setup completed successfully!"
echo "VPC Network: $NETWORK"
echo "Subnet: $SUBNETWORK (10.0.0.0/24)"
echo "Firewall rules: $FW_RULE_IAP, $FW_RULE_INTERNAL"
