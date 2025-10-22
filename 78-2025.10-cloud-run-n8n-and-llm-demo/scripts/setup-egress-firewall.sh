#!/bin/bash
set -euo pipefail

# Validate required environment variables
required_vars=("PROJECT_ID" "NETWORK")
for var in "${required_vars[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "Error: $var environment variable is not set"
        exit 1
    fi
done

NETWORK_NAME="${NETWORK##*/}"  # Extract network name from full path if needed

echo "Setting up egress firewall rules..."
echo "Project: $PROJECT_ID"
echo "Network: $NETWORK_NAME"
echo ""

# Rule 1: Allow egress for instances with "allow-model-access" tag (higher priority)
echo "Creating ALLOW egress rule for instances with 'allow-model-access' tag..."
gcloud compute firewall-rules create allow-tagged-egress \
    --project="$PROJECT_ID" \
    --network="$NETWORK_NAME" \
    --direction=EGRESS \
    --priority=900 \
    --action=ALLOW \
    --rules=all \
    --destination-ranges=0.0.0.0/0 \
    --target-tags=allow-model-access \
    || echo "Rule 'allow-tagged-egress' already exists, skipping..."

# Rule 2: Deny all other egress (lower priority)
echo "Creating DENY egress rule for all other traffic..."
gcloud compute firewall-rules create deny-all-egress \
    --project="$PROJECT_ID" \
    --network="$NETWORK_NAME" \
    --direction=EGRESS \
    --priority=1000 \
    --action=DENY \
    --rules=all \
    --destination-ranges=0.0.0.0/0 \
    || echo "Rule 'deny-all-egress' already exists, skipping..."

echo ""
echo "✅ Egress firewall rules created successfully!"
echo ""
echo "Rules:"
echo "  1. allow-tagged-egress (priority 900): Allows egress from instances with 'allow-model-access' tag"
echo "  2. deny-all-egress (priority 1000): Denies all other egress traffic"
echo ""
echo "To view the rules:"
echo "  gcloud compute firewall-rules list --project=$PROJECT_ID --filter='network:$NETWORK_NAME direction:EGRESS'"
