#!/bin/bash

# Deploy Cloud Run service using V2 REST API

LOCATION="australia-southeast1"
SERVICE_NAME="src-fortio"

TOKEN=$(gcloud auth print-access-token)

SERVICE_EXISTS=$(gcloud run services describe ${SERVICE_NAME} \
  --region=${LOCATION} \
  --project=${PROJECT_NUMBER} \
  --format="value(name)" 2>/dev/null)

if [ -z "$SERVICE_EXISTS" ]; then
  # Service doesn't exist, create it
  echo "Creating new service..."
  # Note: service-v2.json should NOT have a 'name' field for creation
  curl -X POST \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d @service-v2.json \
    "https://run.googleapis.com/v2/projects/${PROJECT_NUMBER}/locations/${LOCATION}/services?serviceId=${SERVICE_NAME}"
else
  # Service exists, update it
  echo "Updating existing service..."
  # For PATCH, we need to add the name field to the JSON
  jq --arg name "projects/${PROJECT_NUMBER}/locations/${LOCATION}/services/${SERVICE_NAME}" \
    '. + {name: $name}' service-v2.json > service-v2-update.json

  curl -X PATCH \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d @service-v2-update.json \
    "https://run.googleapis.com/v2/projects/${PROJECT_NUMBER}/locations/${LOCATION}/services/${SERVICE_NAME}"

  #rm service-v2-update.json
fi

# To check the operation status:
# OPERATION_NAME="operations/..."  # From the response above
echo curl -H \"Authorization: Bearer \${TOKEN}\" \"https://run.googleapis.com/v2/\${OPERATION_NAME}\"
