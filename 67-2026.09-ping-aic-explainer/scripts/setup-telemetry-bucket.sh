#!/usr/bin/env bash
# Create the completions bucket and grant the Agent Runtime SA write access.
# Does not print project numbers.
set -euo pipefail

if [[ -z "${GOOGLE_CLOUD_PROJECT:-}" ]]; then
  echo "ERROR: GOOGLE_CLOUD_PROJECT is required" >&2
  exit 1
fi

REGION="${GOOGLE_CLOUD_REGION:-us-central1}"
BUCKET="${LOGS_BUCKET_NAME:-${GOOGLE_CLOUD_PROJECT}-ping-aic-explainer-logs}"

if ! gcloud storage buckets describe "gs://${BUCKET}" --project="${GOOGLE_CLOUD_PROJECT}" >/dev/null 2>&1; then
  gcloud storage buckets create "gs://${BUCKET}" \
    --project="${GOOGLE_CLOUD_PROJECT}" \
    --location="${REGION}" \
    --uniform-bucket-level-access
  echo "created bucket gs://${BUCKET}"
else
  echo "bucket gs://${BUCKET} already exists"
fi

PROJECT_NUMBER="$(gcloud projects describe "${GOOGLE_CLOUD_PROJECT}" --format='value(projectNumber)')"
RUNTIME_SA="service-${PROJECT_NUMBER}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"

gcloud storage buckets add-iam-policy-binding "gs://${BUCKET}" \
  --member="serviceAccount:${RUNTIME_SA}" \
  --role="roles/storage.objectUser" \
  --project="${GOOGLE_CLOUD_PROJECT}" \
  >/dev/null

for ROLE in roles/logging.logWriter roles/cloudtrace.agent roles/telemetry.tracesWriter; do
  gcloud projects add-iam-policy-binding "${GOOGLE_CLOUD_PROJECT}" \
    --member="serviceAccount:${RUNTIME_SA}" \
    --role="${ROLE}" \
    --condition=None \
    >/dev/null
done

echo "granted runtime service account write access to gs://${BUCKET}"
echo "LOGS_BUCKET_NAME=${BUCKET}"
