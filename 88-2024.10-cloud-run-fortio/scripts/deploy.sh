#!/bin/bash
set -eoux pipefail

SERVICE_NAME="fortio-test"

gcloud run deploy $SERVICE_NAME \
--image="fortio/fortio" \
--network=$NETWORK \
--subnet=$SUBNETWORK \
--vpc-egress=all-traffic \
--region=$REGION \
--project=$PROJECT_ID

#--network-tags=NETWORK_TAG_NAMES \
#--no-allow-unauthenticated \

export SERVICE_URL=$(gcloud run services describe fortio-test --region=$REGION --format='value(status.url)')
