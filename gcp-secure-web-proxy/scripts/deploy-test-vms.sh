#!/bin/bash

GSA="test-vm-swp"
VM_NAME=$GSA

vpc_name=$CLUSTER_VPC # sourced in env vars
subnet_name=$CLUSTER_SUBNET
zone="australia-southeast1-a"

# SA - create only once
gcloud iam service-accounts create $GSA \
    --description="Test SWP from VM" \
    --display-name="test-vm-swp"

gcloud compute instances create ${VM_NAME}-with-sa \
    --provisioning-model=SPOT \
    --service-account="${GSA}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --machine-type=e2-small \
    --zone=$zone \
    --subnet=$subnet_name \
    --network=$vpc_name

gcloud compute instances create ${VM_NAME}-no-sa \
    --provisioning-model=SPOT \
    --scopes=https://www.googleapis.com/auth/cloud-platform \
    --machine-type=e2-small \
    --zone=$zone \
    --subnet=$subnet_name \
    --network=$vpc_name

# on VM
# export HTTP_PROXY=http://10.0.0.9:443
# export HTTPS_PROXY=http://10.0.0.9:443
