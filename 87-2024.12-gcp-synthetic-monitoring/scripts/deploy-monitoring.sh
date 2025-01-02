#!/bin/bash

set -eoux pipefail

export SYNTH_APP_ENDPOINT="fortio-5c4xj36nda-ts.a.run.app"

gcloud beta monitoring uptime create test-connectivity \
    --resource-type=uptime-url \
    --resource-labels=host=$SYNTH_APP_ENDPOINT,project_id=$PROJECT_ID \
    --path="/fortio/fetch?url=https://www.google.com"

gcloud beta monitoring uptime create test-dns \
    --resource-type=uptime-url \
    --resource-labels=host=google.com,project_id=$PROJECT_ID

# --http-check-path="/fortio/rest/dns?host=google.com" \
# --http-check-path="/fortio/fetch?url=https://www.google.com" \
