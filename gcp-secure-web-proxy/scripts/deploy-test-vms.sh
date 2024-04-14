#!/bin/bash

set -eoux pipefail

GSA_NAME="demo-app-admin-sa-ksa2gsa"
VM_NAME=$GSA_NAME

vpc_name=$CLUSTER_VPC # sourced in env vars
subnet_name=$CLUSTER_SUBNET
subnet_primary_range="10.0.0.0/22"

# SA - create only once
gcloud iam service-accounts create $GSA_NAME \
    --description="Test SWP from VM" \
    --display-name="test-vm-swp"

gcloud compute instances create ${VM_NAME}-with-sa \
    --provisioning-model=SPOT \
    --service-account="${GSA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --machine-type=e2-small \
    --zone=$ZONE \
    --subnet=$subnet_name \
    --network=$vpc_name

gcloud compute instances create ${VM_NAME}-no-sa \
     --provisioning-model=SPOT \
     --scopes=https://www.googleapis.com/auth/cloud-platform \
     --machine-type=e2-small \
     --zone=$ZONE \
     --subnet=$subnet_name \
     --network=$vpc_name

gcloud compute instances create envoy-proxy \
    --provisioning-model=SPOT \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --machine-type=e2-small \
    --zone=$ZONE \
    --tag=proxy-vm-tag \
    --subnet=$subnet_name \
    --network=$vpc_name

gcloud compute firewall-rules create allow-proxy-communication \
    --direction=INGRESS \
    --priority=1000 \
    --network=$vpc_name \
    --action=ALLOW \
    --rules=tcp:8888 \
    --source-ranges=$subnet_primary_range \
    --target-tags=proxy-vm-tag

# on VM
# export HTTP_PROXY=http://10.0.0.9:443
# export HTTPS_PROXY=http://10.0.0.9:443
