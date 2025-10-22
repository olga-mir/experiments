#!/bin/bash
set -euo pipefail

#export N8N_URL=
#export GEMMA_URL=

curl -s -w "\nHTTP Status: %{http_code}\n" \
    -H "Authorization: Bearer $TOKEN" \
    "$N8N_URL/" \
    | head -n 20

PROMPT="${1:-"What is Google Developer Group?"}"

# Create JSON payload
cat > /tmp/gemma-request.json <<EOF
{
  "model": "gemma3:4b",
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

curl -s -X POST "$GEMMA_URL/api/generate" \
    -H "Authorization: Bearer $TOKEN" \
    -d @/tmp/gemma-request.json \
    --max-time 120 \
    -w "\n\nHTTP Status: %{http_code}\n"

#rm -f /tmp/gemma-request.json
    #-H "Content-Type: application/json" \

# echo command to terminal
# echo "curl -vvv -s -H \"Authorization: Bearer \$TOKEN\" $N8N_URL -o /dev/null 2>&1 | grep -v Bearer"

# curl -vvv -s "$N8N_URL" -o /dev/null 2>&1 | grep -v Bearer
# curl -vvv -s -H "Authorization: Bearer $TOKEN" "$N8N_URL" -o /dev/null 2>&1 | grep -v Bearer

# curl -s -X POST ${GEMMA_URL}/api/generate -H "Authorization: Bearer ${TOKEN}" -H 'Content-Type: application/json' -d @/tmp/gemma-request.json --max-time 120 2>&1 | grep -v Bearer
# curl -s -vvv -X POST ${GEMMA_URL}/api/generate -H "Authorization: Bearer ${TOKEN}" -H 'Content-Type: application/json' -d @/tmp/gemma-request.json -o /dev/null 2>&1 | grep -v Bearer

