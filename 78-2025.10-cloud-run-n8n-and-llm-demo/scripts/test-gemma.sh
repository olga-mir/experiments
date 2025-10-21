#!/bin/bash
set -euo pipefail

# Check if GEMMA_URL is set
if [ -z "${GEMMA_URL:-}" ]; then
    echo "Error: GEMMA_URL environment variable is not set"
    echo "Usage: export GEMMA_URL=<service-url>"
    echo "Example: export GEMMA_URL=https://gemma-model-xxx.a.run.app"
    exit 1
fi

# Get authentication token
echo "Getting authentication token..."
TOKEN=$(gcloud auth print-identity-token)

# Prompt to use (can be customized)
PROMPT="${1:-"Hello, how are you?"}"

echo ""
echo "Testing Gemma service..."
echo "URL: $GEMMA_URL"
echo "Prompt: $PROMPT"
echo ""

# Create JSON payload
cat > /tmp/gemma-request.json <<EOF
{
  "model": "gemma3-4b",
  "prompt": "$PROMPT",
  "stream": false
}
EOF

echo "Request payload:"
cat /tmp/gemma-request.json | jq '.'
echo ""

# Send POST request to Gemma service
echo "Sending request..."
echo ""

curl -X POST "$GEMMA_URL/api/generate" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d @/tmp/gemma-request.json \
    --max-time 120 \
    -w "\n\nHTTP Status: %{http_code}\n" \
    | jq '.'

# Cleanup
rm -f /tmp/gemma-request.json

echo ""
echo "Test complete!"
