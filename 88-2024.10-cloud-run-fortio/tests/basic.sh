#!/bin/bash

set -eoux pipefail

export TOKEN=$(gcloud auth print-identity-token)

curl -H "Authorization: Bearer $TOKEN" $SERVICE_URL/fortio/debug
exit 0
curl "$SERVICE_URL/fortio/"
curl "$SERVICE_URL/fortio/"
curl "$SERVICE_URL/fortio/"
curl "$SERVICE_URL/fortio/load?qps=100&t=30s&c=20&url=$SERVICE_URL/echo"