#!/bin/bash
set -euo pipefail

# Validate required environment variables
required_vars=("PROJECT_ID" "PROJECT_NUMBER" "REGION")
for var in "${required_vars[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "Error: $var environment variable is not set"
        exit 1
    fi
done

#   Cleanup Order (reverse of dependencies):
#
#   1. IAP IAM binding - Remove user access
#   2. Forwarding rule - n8n-secure-lb-forwarding-rule
#   3. Static IP - n8n-secure-lb-ip
#   4. HTTPS proxy - n8n-secure-lb-https-proxy
#   5. URL map - n8n-secure-lb-url-map
#   6. Backend service - n8n-secure-lb-backend (with IAP disabled first)
#   7. NEG - n8n-secure-lb-neg
#
#   ✅ PRESERVED: SSL certificate n8n-secure-lb-ssl

# Must match the setup script
LB_NAME="n8n-secure-lb"

echo "🧹 Cleaning up Application Load Balancer resources..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "LB Name: $LB_NAME"
echo ""
echo "NOTE: SSL certificate '${LB_NAME}-ssl' will be preserved for reuse"
echo ""
sleep 2

# Delete resources in reverse order of dependencies

# 1. Delete IAP IAM binding
echo "👤 Step 1: Removing IAP IAM bindings..."
gcloud iap web services remove-iam-policy-binding \
    "projects/$PROJECT_NUMBER/iap_web/compute/services/${LB_NAME}-backend" \
    --member="user:${USER_EMAIL}" \
    --role="roles/iap.httpsIapUser" \
    --project="$PROJECT_ID" \
    --quiet 2>/dev/null || echo "  IAP IAM binding not found or already removed"

# 2. Delete forwarding rule
echo "➡️ Step 2: Deleting forwarding rule '${LB_NAME}-forwarding-rule'..."
gcloud compute forwarding-rules delete "${LB_NAME}-forwarding-rule" \
    --global \
    --project="$PROJECT_ID" \
    --quiet 2>/dev/null || echo "  Forwarding rule not found or already deleted"

# 3. Delete static IP
echo "🌍 Step 3: Deleting static IP '${LB_NAME}-ip'..."
gcloud compute addresses delete "${LB_NAME}-ip" \
    --global \
    --project="$PROJECT_ID" \
    --quiet 2>/dev/null || echo "  Static IP not found or already deleted"

# 4. Delete target HTTPS proxy
echo "🛡️ Step 4: Deleting HTTPS proxy '${LB_NAME}-https-proxy'..."
gcloud compute target-https-proxies delete "${LB_NAME}-https-proxy" \
    --project="$PROJECT_ID" \
    --quiet 2>/dev/null || echo "  HTTPS proxy not found or already deleted"

# 5. Delete URL map
echo "🗺️ Step 5: Deleting URL map '${LB_NAME}-url-map'..."
gcloud compute url-maps delete "${LB_NAME}-url-map" \
    --project="$PROJECT_ID" \
    --quiet 2>/dev/null || echo "  URL map not found or already deleted"

# 6. Delete backend service (first disable IAP)
echo "⚙️ Step 6: Disabling IAP and deleting backend service '${LB_NAME}-backend'..."
gcloud compute backend-services update "${LB_NAME}-backend" \
    --global \
    --iap=disabled \
    --project="$PROJECT_ID" \
    --quiet 2>/dev/null || echo "  IAP already disabled or backend not found"

gcloud compute backend-services delete "${LB_NAME}-backend" \
    --global \
    --project="$PROJECT_ID" \
    --quiet 2>/dev/null || echo "  Backend service not found or already deleted"

# 7. Delete NEG (Network Endpoint Group)
echo "🔗 Step 7: Deleting NEG '${LB_NAME}-neg'..."
gcloud compute network-endpoint-groups delete "${LB_NAME}-neg" \
    --region="$REGION" \
    --project="$PROJECT_ID" \
    --quiet 2>/dev/null || echo "  NEG not found or already deleted"

echo ""
echo "✅ === Cleanup Complete ==="
echo ""
echo "🔒 SSL certificate '${LB_NAME}-ssl' was preserved and can be reused."
echo ""
echo "To view the certificate:"
echo "  gcloud compute ssl-certificates describe ${LB_NAME}-ssl --project=$PROJECT_ID"
echo ""
echo "To delete the certificate manually (if needed):"
echo "  gcloud compute ssl-certificates delete ${LB_NAME}-ssl --global --project=$PROJECT_ID"
echo ""
echo "To recreate the load balancer:"
echo "  ./scripts/setup-alb.sh"
