#!/bin/bash
set -e # Exit immediately if a command fails

echo "--- 🚀 Starting OAuth setup for IAP ---"

# --- 3. Create OAuth Consent Screen (Brand) ---
# This is a one-time operation per project.

echo "🔍 Checking for existing OAuth consent screen (brand)..."
# We list brands and get the name of the first one.
BRAND_NAME=$(gcloud iap oauth-brands list \
  --project=$PROJECT_ID \
  --format="value(name)" \
  --limit=1)

if [ -z "$BRAND_NAME" ]; then
  echo "🎨 No consent screen found. Creating a new one..."
  BRAND_NAME=$(gcloud iap oauth-brands create \
    --application_title="n8n Secure Access" \
    --support_email=$USER_EMAIL \
    --project=$PROJECT_ID \
    --format="value(name)")
  echo "✅ Created new consent screen: $BRAND_NAME"
else
  echo "✅ Found existing consent screen: $BRAND_NAME"
fi

# --- 4. Create OAuth Client ID & Secret ---
echo "💳 Creating new OAuth client ID for IAP..."
# We create the client and capture its JSON output
CLIENT_JSON=$(gcloud iap oauth-clients create $BRAND_NAME \
  --display_name="n8n-lb-iap-client" \
  --project=$PROJECT_ID \
  --format=json)

# Parse the client ID and secret from the JSON
# The 'name' is a long path, so we split it by '/' and get the last part
OAUTH_CLIENT_ID=$(echo $CLIENT_JSON | jq -r '.name | split("/") | last')
OAUTH_CLIENT_SECRET=$(echo $CLIENT_JSON | jq -r '.secret')

if [ -z "$OAUTH_CLIENT_ID" ] || [ "$OAUTH_CLIENT_ID" == "null" ]; then
    echo "❌ Error: Failed to create or parse OAuth Client ID."
    exit 1
fi

echo "✅ Created new OAuth client."
echo "   Client ID: $OAUTH_CLIENT_ID"

# --- 5. Link OAuth Client to IAP Backend Service ---
echo "🔗 Linking new OAuth client to the load balancer backend service..."
gcloud compute backend-services update ${LB_NAME}-backend \
  --global \
  --iap=enabled,oauth2-client-id=${OAUTH_CLIENT_ID},oauth2-client-secret=${OAUTH_CLIENT_SECRET} \
  --project=$PROJECT_ID

echo "---"
echo "🎉 All Done! ---"
echo "---"
echo "Wait about 2-3 minutes for the settings to apply."
echo "Then, open a new Incognito window and go to your URL: https://n8n-gdg...."
echo ""
echo "You should now see the Google login page. After you log in, you will be taken to n8n."
