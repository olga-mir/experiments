# 1. Set or export
# export LB_NAME="n8n-secure-lb"
# export OAUTH_CLIENT_ID=<YOUR_ID>
# export OAUTH_CLIENT_SECRET=<YOUR_CLIENT>

# 3. Run the update command
echo "🔗 Linking manual OAuth client to the load balancer..."
gcloud compute backend-services update ${LB_NAME}-backend \
  --global \
  --iap=enabled,oauth2-client-id=${OAUTH_CLIENT_ID},oauth2-client-secret=${OAUTH_CLIENT_SECRET} \
  --project=$PROJECT_ID

echo "🎉 All Done! Wait 2-3 minutes, then test in an Incognito browser."
echo "Go to: https://n8n-gdg.YOUR-DOMAIN/"

# gcloud services enable iap.googleapis.com --project=$PROJECT_ID

# This is the special, Google-managed service account for IAP
export IAP_SERVICE_AGENT="serviceAccount:service-${PROJECT_NUMBER}@gcp-sa-iap.iam.gserviceaccount.com"

echo "🔐 Granting IAP permission to invoke your Cloud Run service..."

gcloud run services add-iam-policy-binding $N8N_SERVICE_NAME \
  --member=$IAP_SERVICE_AGENT \
  --role="roles/run.invoker" \
  --region=$REGION \
  --project=$PROJECT_ID

echo "✅ All permissions are set!"
