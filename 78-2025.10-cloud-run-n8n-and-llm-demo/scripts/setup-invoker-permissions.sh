#!/bin/bash
set -euo pipefail

# Validate required environment variables
required_vars=("PROJECT_ID" "REGION" "USER_EMAIL")
for var in "${required_vars[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "Error: $var environment variable is not set"
        exit 1
    fi
done

N8N_SERVICE="n8n"
N8N_SA="n8n-service@${PROJECT_ID}.iam.gserviceaccount.com"
GEMMA_SERVICE="gemma-model"
GEMMA_REGION="asia-southeast1"

echo "Setting up Cloud Run invoker permissions..."
echo "Project: $PROJECT_ID"
echo "User: $USER_EMAIL"
echo ""

# Grant USER invoker permission on n8n
echo "Granting user:${USER_EMAIL} invoker permission on ${N8N_SERVICE}..."
gcloud run services add-iam-policy-binding "$N8N_SERVICE" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --member="user:${USER_EMAIL}" \
    --role="roles/run.invoker"

# Grant USER invoker permission on gemma
echo "Granting user:${USER_EMAIL} invoker permission on ${GEMMA_SERVICE}..."
gcloud run services add-iam-policy-binding "$GEMMA_SERVICE" \
    --project="$PROJECT_ID" \
    --region="$GEMMA_REGION" \
    --member="user:${USER_EMAIL}" \
    --role="roles/run.invoker"

# Grant N8N service account invoker permission on gemma
echo "Granting ${N8N_SA} invoker permission on ${GEMMA_SERVICE}..."
gcloud run services add-iam-policy-binding "$GEMMA_SERVICE" \
    --project="$PROJECT_ID" \
    --region="$GEMMA_REGION" \
    --member="serviceAccount:${N8N_SA}" \
    --role="roles/run.invoker"

echo ""
echo "=== Invoker Permissions Configured ==="
echo ""
echo "✓ ${USER_EMAIL} can invoke:"
echo "  - ${N8N_SERVICE} (region: ${REGION})"
echo "  - ${GEMMA_SERVICE} (region: ${GEMMA_REGION})"
echo ""
echo "✓ ${N8N_SA} can invoke:"
echo "  - ${GEMMA_SERVICE} (region: ${GEMMA_REGION})"
echo ""
echo "Usage on bastion:"
echo "  # Get your identity token locally:"
echo "  task get-token"
echo ""
echo "  # Copy token to bastion and use it:"
echo "  export TOKEN=<your-token>"
echo "  curl -H \"Authorization: Bearer \$TOKEN\" <service-url>"
