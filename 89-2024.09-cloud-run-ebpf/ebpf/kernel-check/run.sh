#!/bin/bash

set -eoux pipefail

export IMAGE_NAME=kernel-check
export REPO_NAME=experiments
export REPO_URI="${REGION}-docker.pkg.dev/$PROJECT_ID/$REPO_NAME"

# env vars must be set:
# PROJECT_ID
# REGION

# Only once.
# gcloud artifacts repositories create experiments --repository-format=docker --location=$REGION --description="Repo for hosting experiments images"

TAG=$REPO_URI/$IMAGE_NAME:latest
docker build -t $TAG .

docker push $TAG

gcloud run deploy kernel-check --image $REPO_URI --execution-environment gen2 --region $REGION
