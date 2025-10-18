#!/bin/bash

# Deploy Cloud Run service using V2 REST API

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

TEMPLATE_FILE="${SCRIPT_DIR}/service-v2.json.tpl" # need to exist
SERVICE_JSON="${SCRIPT_DIR}/service-v2.json" # will be created
SERVICE_JSON_UPDATE="${SCRIPT_DIR}/service-v2-update.json" # create/update response

SERVICE_NAME="src-fortio"

VPC_URI="projects/${PROJECT_ID}/global/networks/${NETWORK}"
SUBNET_URI="projects/${PROJECT_ID}/regions/${REGION}/subnetworks/${SUBNETWORK}"

export PROJECT_ID SA_NAME VPC_URI SUBNET_URI
envsubst < "${TEMPLATE_FILE}" > "${SERVICE_JSON}"

TOKEN=$(gcloud auth print-access-token)

SERVICE_EXISTS=$(gcloud run services describe ${SERVICE_NAME} \
  --region=${REGION} \
  --project=${PROJECT_NUMBER} \
  --format="value(name)" 2>/dev/null)

if [ -z "$SERVICE_EXISTS" ]; then
  # Service doesn't exist, create it
  echo "Creating new service..."
  # Note: service-v2.json should NOT have a 'name' field for creation
  curl -X POST \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d @"${SERVICE_JSON}" \
    "https://run.googleapis.com/v2/projects/${PROJECT_NUMBER}/locations/${REGION}/services?serviceId=${SERVICE_NAME}"
else
  # Service exists, update it
 echo "Updating existing service..."
  # For PATCH, we need to add the name field to the JSON
  jq --arg name "projects/${PROJECT_NUMBER}/locations/${REGION}/services/${SERVICE_NAME}" \
    '. + {name: $name}' "${SERVICE_JSON}" > "${SERVICE_JSON_UPDATE}"

 curl -X PATCH \
    -H "Authorization: Bearer ${TOKEN}" \
    -H "Content-Type: application/json" \
    -d @"${SERVICE_JSON_UPDATE}" \
    "https://run.googleapis.com/v2/projects/${PROJECT_NUMBER}/locations/${REGION}/services/${SERVICE_NAME}"

  #rm "${SERVICE_JSON_UPDATE}"
fi

# To check the operation status:
# OPERATION_NAME="operations/..."  # From the response above
echo curl -H \"Authorization: Bearer \${TOKEN}\" \"https://run.googleapis.com/v2/\${OPERATION_NAME}\"
