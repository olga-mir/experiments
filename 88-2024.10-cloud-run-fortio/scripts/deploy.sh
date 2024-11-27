#!/bin/bash
set -eoux pipefail

SERVICE_NAME="fortio-test"

gcloud run deploy $SERVICE_NAME \
--no-allow-unauthenticated \
--image="fortio/fortio" \
--network=$NETWORK \
--subnet=$SUBNETWORK \
--vpc-egress=all-traffic \
--region=$REGION \
--project=$PROJECT_ID

#--network-tags=NETWORK_TAG_NAMES \

export SERVICE_URL=$(gcloud run services describe fortio-test --format='value(status.url)')
