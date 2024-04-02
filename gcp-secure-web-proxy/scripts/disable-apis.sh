#!/bin/bash

set -x

gcloud certificate-manager certificates delete basic-cert --location=$GCP_REGION -q

gcloud services disable networksecurity.googleapis.com
gcloud services disable certificatemanager.googleapis.com
gcloud services disable networkservices.googleapis.com
