#!/bin/bash
set -euo pipefail

PROJECT_ID="${1:-}"
BUCKET_NAME="${2:-}"

if [ -z "$PROJECT_ID" ]; then
  echo "❌ Usage: setup-infra.sh <PROJECT_ID> <BUCKET_NAME>"
  exit 1
fi

if [ -z "$BUCKET_NAME" ]; then
  echo "❌ Usage: setup-infra.sh <PROJECT_ID> <BUCKET_NAME>"
  exit 1
fi

echo "🚀 Setting up infrastructure for project: $PROJECT_ID"
echo "   Bucket: $BUCKET_NAME"

# Set the project
gcloud config set project "$PROJECT_ID" --quiet

# Enable required APIs
echo "📦 Enabling required APIs..."
REQUIRED_APIS=(
  "aiplatform.googleapis.com"
  "storage-api.googleapis.com"
  "cloudresourcemanager.googleapis.com"
  "iam.googleapis.com"
)

for api in "${REQUIRED_APIS[@]}"; do
  if gcloud services list --enabled --filter="name:$api" --format="value(name)" | grep -q "$api"; then
    echo "   ✓ $api already enabled"
  else
    echo "   Enabling $api..."
    gcloud services enable "$api" --quiet
  fi
done

# Create GCS bucket if it doesn't exist
echo "📂 Setting up GCS bucket..."
if gsutil ls -b "gs://$BUCKET_NAME" &>/dev/null; then
  echo "   ✓ Bucket gs://$BUCKET_NAME already exists"
else
  echo "   Creating bucket gs://$BUCKET_NAME..."
  gsutil mb -p "$PROJECT_ID" "gs://$BUCKET_NAME"
fi

# Set bucket lifecycle policy to clean up old artifacts (optional but recommended)
echo "🔄 Configuring bucket lifecycle..."
cat > /tmp/bucket-lifecycle.json <<EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 30}
      }
    ]
  }
}
EOF

gsutil lifecycle set /tmp/bucket-lifecycle.json "gs://$BUCKET_NAME" 2>/dev/null || true
rm -f /tmp/bucket-lifecycle.json

echo "✅ Infrastructure setup complete!"
echo ""
echo "Summary:"
echo "  Project ID: $PROJECT_ID"
echo "  Bucket: gs://$BUCKET_NAME"
echo ""
echo "Next steps:"
echo "  - Set SCREENSHOTS_BUCKET_NAME=$BUCKET_NAME in your environment (optional)"
echo "  - Run: task install"
echo "  - Run: task deploy"
