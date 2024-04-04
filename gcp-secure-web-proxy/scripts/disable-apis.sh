#!/bin/bash

set -x

gcloud certificate-manager certificates delete basic-cert --location=$GCP_REGION -q

gcloud services disable --force networksecurity.googleapis.com
gcloud services disable --force networkservices.googleapis.com

sleep 200
gcloud services disable --force certificatemanager.googleapis.com
