#!/bin/bash
set -euo pipefail

# Check if N8N_URL is set
if [ -z "${N8N_URL:-}" ]; then
    echo "Error: N8N_URL environment variable is not set"
    exit 1
fi

echo "Getting authentication token: gcloud auth print-identity-token"
TOKEN=$(gcloud auth print-identity-token)


# Test 1: Check if service is accessible (GET request to root)
echo "=== Test 1: Service Health Check ==="
echo "GET $N8N_URL/"
echo ""

curl -s -w "\nHTTP Status: %{http_code}\n" \
    -H "Authorization: Bearer $TOKEN" \
    "$N8N_URL/" \
    | head -n 20

echo ""
echo "---"
echo ""

# curl -vvv -s -H "Authorization: Bearer $TOKEN" "$N8N_URL" -o /dev/null 2>&1 | grep -v Bearer
echo "curl -vvv -s -H \"Authorization: Bearer \$TOKEN\" $N8N_URL -o /dev/null 2>&1 | grep -v Bearer"
