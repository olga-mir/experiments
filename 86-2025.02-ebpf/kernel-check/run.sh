#!/bin/bash

set -eoux pipefail

if [[ -z "${PROJECT_ID:-}" ]] || [[ -z "${REGION:-}" ]]; then
    echo "Error: PROJECT_ID and REGION must be set"
    exit 1
fi

export IMAGE_NAME=kernel-check
export REPO_NAME=experiments
export REPO_URI="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}"
export PLATFORMS="linux/amd64,linux/arm64"
export TAG="${REPO_URI}/${IMAGE_NAME}:latest"

docker buildx create --use --name multiarch-builder

docker buildx build --platform=${PLATFORMS} --push --tag ${TAG} .

gcloud run deploy kernel-check \
    --image ${TAG} \
    --execution-environment gen2 \
    --region ${REGION} \
    --platform managed
