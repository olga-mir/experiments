#!/bin/bash

set -eou pipefail

export N8N_SERVICE_NAME="n8n"

# The fully qualified domain name you own and will point to this service
# This variables should be set in the terminal
# export DNS_ZONE_NAME="<YOUR_DNS_ZONE_NAME>"
# export DOMAIN_NAME="n8n-gdg...."

# A base name for all the new Load Balancer resources
export LB_NAME="n8n-secure-lb"


# --- 3. Verification ---
if [[ -z "$N8N_SERVICE_NAME" || -z "$DOMAIN_NAME" || -z "$LB_NAME" || -z "$REGION" || -z "$PROJECT_ID" || -z "$PROJECT_NUMBER" || -z "$USER_EMAIL" ]]; then
  echo "❌ Error: One or more required environment variables are not set."
  echo "Please edit the script or set the following environment variables:"
  echo "N8N_SERVICE_NAME: (Set in script)"
  echo "DOMAIN_NAME:    (Set in script - MUST be changed from the default)"
  echo "LB_NAME:        (Set in script)"
  echo "REGION:         (e.g., us-central1)"
  echo "PROJECT_ID:     (Your Google Cloud Project ID)"
  echo "PROJECT_NUMBER: (Your Google Cloud Project Number)"
  echo "USER_EMAIL:     (Your login email)"
  exit 1
fi

echo "--- 🚀 Starting setup with the following configuration ---"
echo "Service:     $N8N_SERVICE_NAME"
echo "Domain:      $DOMAIN_NAME"
echo "LB Name:     $LB_NAME"
echo "Region:      $REGION"
echo "Project ID:  $PROJECT_ID"
echo "Project Num: $PROJECT_NUMBER"
echo "User Email:  $USER_EMAIL"
echo "-----------------------------------------------------"

set -x

# === Step 2: Create the Global Application Load Balancer ===

# 2.1: Create a Serverless NEG (Network Endpoint Group) for the Cloud Run service
echo "🔗 Step 2.1: Creating Serverless NEG '${LB_NAME}-neg'..."
gcloud compute network-endpoint-groups create ${LB_NAME}-neg \
  --region=$REGION \
  --network-endpoint-type=serverless \
  --cloud-run-service=$N8N_SERVICE_NAME \
  --project=$PROJECT_ID

# 2.2: Create the Backend Service
echo "⚙️ Step 2.2: Creating Backend Service '${LB_NAME}-backend'..."
gcloud compute backend-services create ${LB_NAME}-backend \
  --global \
  --load-balancing-scheme=EXTERNAL_MANAGED \
  --project=$PROJECT_ID

# 2.3: Add the Serverless NEG as a backend to the Backend Service
echo "🔗 Step 2.3: Adding NEG to Backend Service..."
gcloud compute backend-services add-backend ${LB_NAME}-backend \
  --global \
  --network-endpoint-group=${LB_NAME}-neg \
  --network-endpoint-group-region=$REGION \
  --project=$PROJECT_ID

# 2.4: Create a Google-managed SSL Certificate for your domain (if it doesn't exist)
if gcloud compute ssl-certificates describe ${LB_NAME}-ssl --global --project=$PROJECT_ID &>/dev/null; then
  echo "🔒 Step 2.4: SSL Certificate '${LB_NAME}-ssl' already exists, skipping creation..."
  echo "   (Certificate provisioning can take 10-15 minutes, so reusing existing certificate)"
else
  echo "🔒 Step 2.4: Creating Google-managed SSL Certificate '${LB_NAME}-ssl' for $DOMAIN_NAME..."
  gcloud compute ssl-certificates create ${LB_NAME}-ssl \
    --domains=$DOMAIN_NAME \
    --global \
    --project=$PROJECT_ID
  echo "   Note: Certificate provisioning will take 10-15 minutes after DNS is configured"
fi

# 2.5: Create the URL Map to route all traffic to the backend
echo "🗺️ Step 2.5: Creating URL Map '${LB_NAME}-url-map'..."
gcloud compute url-maps create ${LB_NAME}-url-map \
  --default-service ${LB_NAME}-backend \
  --project=$PROJECT_ID

# 2.6: Create the Target HTTPS Proxy to terminate SSL
echo "🛡️ Step 2.6: Creating HTTPS Proxy '${LB_NAME}-https-proxy'..."
gcloud compute target-https-proxies create ${LB_NAME}-https-proxy \
  --ssl-certificates=${LB_NAME}-ssl \
  --url-map=${LB_NAME}-url-map \
  --global \
  --project=$PROJECT_ID

# 2.7: Reserve a Global Static IP for the Load Balancer
echo "🌍 Step 2.7: Reserving global static IP '${LB_NAME}-ip'..."
gcloud compute addresses create ${LB_NAME}-ip \
  --ip-version=IPV4 \
  --global \
  --project=$PROJECT_ID

# Get the IP address to print for the user
export LB_IP=$(gcloud compute addresses describe ${LB_NAME}-ip --global --project=$PROJECT_ID --format "value(address)")

# 2.8: Create the Global Forwarding Rule (the LB Frontend)
echo "➡️ Step 2.8: Creating Global Forwarding Rule '${LB_NAME}-forwarding-rule'..."
gcloud compute forwarding-rules create ${LB_NAME}-forwarding-rule \
  --address=${LB_NAME}-ip \
  --target-https-proxy=${LB_NAME}-https-proxy \
  --global \
  --ports=443 \
  --load-balancing-scheme=EXTERNAL_MANAGED \
  --project=$PROJECT_ID

echo "✅ Step 2 Complete."

# --- 3. Run the Atomic DNS Transaction ---
# This process creates a local 'transaction.yaml' file, adds/removes
# from it, and then executes it on the server.


# The static IP reserved for your Load Balancer (this should be exported from your previous step)
# This is just an example, make sure $LB_IP is set in your environment
# export LB_IP="12.34.56.78"

export NEW_TTL=300

# --- 2. Verification ---
if [[ -z "$NETWORK_PROJECT_ID" || -z "$DNS_ZONE_NAME" || -z "$LB_IP" ]]; then
  echo "❌ Error: One or more required environment variables are not set."
  echo "Please set: NETWORK_PROJECT_ID, DNS_ZONE_NAME, DOMAIN_NAME, and LB_IP"
  exit 1
fi

# Add a trailing dot to the domain name, which is required by Cloud DNS
export FQDN_DOMAIN_NAME="${DOMAIN_NAME}."

# --- 3. Cleanup Trap ---
function cleanup() {
  if [ -f transaction.yaml ]; then
    echo "--- 🧹 Stale 'transaction.yaml' found. Aborting transaction. ---"
    gcloud dns record-sets transaction abort \
      --zone=$DNS_ZONE_NAME \
      --project=$NETWORK_PROJECT_ID \
      --quiet
    echo "--- ✅ Cleanup complete. ---"
  fi
}
trap cleanup EXIT

# --- 4. Look up existing record (NEW) ---
echo "🔍 Checking for existing DNS record for $FQDN_DOMAIN_NAME..."
# Get the current record's data and TTL. Format is: [IP_ADDRESS] [TTL]
EXISTING_RECORD=$(gcloud dns record-sets list \
  --name=$FQDN_DOMAIN_NAME \
  --type=A \
  --zone=$DNS_ZONE_NAME \
  --project=$NETWORK_PROJECT_ID \
  --format="value(rrdatas[0], ttl)" \
  2>/dev/null || true) # '|| true' prevents script from exiting if no record is found

# Parse the output into variables
read -r OLD_IP OLD_TTL <<< "$EXISTING_RECORD"

echo "--- 🔄 Starting DNS Update Transaction ---"
echo "Project: $NETWORK_PROJECT_ID"
echo "Zone:    $DNS_ZONE_NAME"
echo "Domain:  $FQDN_DOMAIN_NAME"
echo "New IP:  $LB_IP"
echo "-----------------------------------------"

# --- 5. Run the Atomic DNS Transaction ---

# Step 5.1: Start a new transaction
echo "1. Starting transaction..."
gcloud dns record-sets transaction start \
  --zone=$DNS_ZONE_NAME \
  --project=$NETWORK_PROJECT_ID

# Step 5.2: Remove the old 'A' record if it exists
if [ -n "$OLD_IP" ] && [ -n "$OLD_TTL" ]; then
  echo "2. Removing old 'A' record ($OLD_IP with TTL $OLD_TTL)..."
  gcloud dns record-sets transaction remove \
    --name=$FQDN_DOMAIN_NAME \
    --type=A \
    --ttl=$OLD_TTL \
    --zone=$DNS_ZONE_NAME \
    --project=$NETWORK_PROJECT_ID \
    $OLD_IP
else
  echo "2. No existing 'A' record found. Skipping remove."
fi

# Step 5.3: Add the new 'A' record to the transaction
echo "3. Adding new 'A' record..."
gcloud dns record-sets transaction add \
  --name=$FQDN_DOMAIN_NAME \
  --type=A \
  --ttl=$NEW_TTL \
  --zone=$DNS_ZONE_NAME \
  --project=$NETWORK_PROJECT_ID \
  $LB_IP

# Step 5.4: Execute the transaction
echo "4. Executing transaction..."
gcloud dns record-sets transaction execute \
  --zone=$DNS_ZONE_NAME \
  --project=$NETWORK_PROJECT_ID


echo "✅ DNS update complete for $DOMAIN_NAME."

# === Step 4: Enable and Configure IAP (Identity-Aware Proxy) ===

# 4.1: Enable IAP on the Backend Service
# This command will prompt you to create an OAuth client if one doesn't exist.
echo "👮 Step 4.1: Enabling IAP on the Backend Service..."
gcloud compute backend-services update ${LB_NAME}-backend \
  --global \
  --iap=enabled \
  --project=$PROJECT_ID

# 4.2: Grant your user account access to the IAP-secured service
echo "👤 Step 4.2: Granting '$USER_EMAIL' the 'IAP-secured Web App User' role..."
gcloud iap web add-iam-policy-binding \
  --resource-type=backend-services \
  --service=${LB_NAME}-backend \
  --member="user:$USER_EMAIL" \
  --role="roles/iap.httpsResourceAccessor" \
  --project=$PROJECT_ID

echo "✅ Step 4 Complete."

echo "---"
echo "🎉 All Done! --- Next Steps:"
echo "---"
echo "    Once the DNS has updated, complete Step 4: Deploy a new revision of your '$N8N_SERVICE_NAME' service and add these environment variables:"
echo "    N8N_EDITOR_BASE_URL=https://$DOMAIN_NAME/"
echo "    WEBHOOK_URL=https://$DOMAIN_NAME/"
echo "    N8N_HOST=$DOMAIN_NAME"
echo "    N8N_PROTOCOL=https"

