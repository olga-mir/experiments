#!/bin/bash

# Project configuration
export PROJECT_ID="cloud-run-demo-474608"
export PROJECT_NUMBER="763924620189"
export REGION="australia-southeast1"

# Network configuration
export VPC_NAME="main-vpc"
export SUBNET_DEV="apps-dev"
export SUBNET_DEV_RANGE="10.10.0.0/20"
export SUBNET_PROD="apps-prod"
export SUBNET_PROD_RANGE="10.10.16.0/20"

# Cloud Run configuration
export CLOUD_RUN_SERVICE="fortio-dev"
export CLOUD_RUN_IMAGE="fortio/fortio:latest"

# Set the project
gcloud config set project $PROJECT_ID

# Create VPC if it doesn't exist
if ! gcloud compute networks describe $VPC_NAME --quiet 2>/dev/null; then
    echo "Creating VPC: $VPC_NAME"
    gcloud compute networks create $VPC_NAME --subnet-mode=custom
else
    echo "VPC $VPC_NAME already exists"
fi

# Create dev subnet if it doesn't exist
if ! gcloud compute networks subnets describe $SUBNET_DEV --region=$REGION --quiet 2>/dev/null; then
    echo "Creating subnet: $SUBNET_DEV"
    gcloud compute networks subnets create $SUBNET_DEV \
        --network=$VPC_NAME \
        --range=$SUBNET_DEV_RANGE \
        --region=$REGION
else
    echo "Subnet $SUBNET_DEV already exists"
fi

# Create prod subnet if it doesn't exist
if ! gcloud compute networks subnets describe $SUBNET_PROD --region=$REGION --quiet 2>/dev/null; then
    echo "Creating subnet: $SUBNET_PROD"
    gcloud compute networks subnets create $SUBNET_PROD \
        --network=$VPC_NAME \
        --range=$SUBNET_PROD_RANGE \
        --region=$REGION
else
    echo "Subnet $SUBNET_PROD already exists"
fi

# Deploy Cloud Run service with Direct VPC Egress
echo "Deploying Cloud Run service: $CLOUD_RUN_SERVICE"
gcloud run deploy $CLOUD_RUN_SERVICE \
    --image=$CLOUD_RUN_IMAGE \
    --region=$REGION \
    --network=$VPC_NAME \
    --subnet=$SUBNET_DEV \
    --vpc-egress=all-traffic \
    --no-allow-unauthenticated \
    --platform=managed

echo "Deployment complete!"
echo "Service URL: $(gcloud run services describe $CLOUD_RUN_SERVICE --region=$REGION --format='value(status.url)')"
