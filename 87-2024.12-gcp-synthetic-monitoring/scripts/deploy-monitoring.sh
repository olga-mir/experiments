#!/bin/bash

set -eoux pipefail

export SYNTH_APP_ENDPOINT="TODO"

gcloud beta monitoring uptime create gke-test-connectivity \
    --resource-type=uptime-url \
    --resource-labels=host=$SYNTH_APP_ENDPOINT,project_id=$PROJECT_ID \
    --path="/fortio/fetch?url=https://www.google.com"

gcloud beta monitoring uptime create gke-test-dns \
    --resource-type=uptime-url \
    --resource-labels=host=google.com,project_id=$PROJECT_ID

# --http-check-path="/fortio/rest/dns?host=google.com" \
# --http-check-path="/fortio/fetch?url=https://www.google.com" \
