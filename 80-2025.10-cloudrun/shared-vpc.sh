#!/bin/bash

# --- Configuration Variables ---
# IMPORTANT: Replace these with your actual values.
# Get your organization ID by running 'gcloud organizations list'
ORG_ID="YOUR-ORG-ID" # e.g., 123456789012

# Development Shared VPC Configuration
DEV_HOST_PROJECT_ID="dev-host-vpc-123456" # Must be globally unique
DEV_HOST_PROJECT_NAME="Dev Shared VPC Host"
DEV_VPC_NETWORK_NAME="dev-shared-vpc-network"
DEV_SUBNET_NAME_1="dev-us-central1-subnet"
DEV_SUBNET_REGION_1="us-central1"
DEV_SUBNET_IP_RANGE_1="10.10.0.0/20" # Example range, adjust as needed

# Production Shared VPC Configuration
PROD_HOST_PROJECT_ID="prod-host-vpc-123456" # Must be globally unique
PROD_HOST_PROJECT_NAME="Prod Shared VPC Host"
PROD_VPC_NETWORK_NAME="prod-shared-vpc-network"
PROD_SUBNET_NAME_1="prod-us-central1-subnet"
PROD_SUBNET_REGION_1="us-central1"
PROD_SUBNET_IP_RANGE_1="10.20.0.0/20" # Example range, ensure no overlap with dev or other networks

# --- Function to check command success ---
check_success() {
    if [ $? -ne 0 ]; then
        echo "ERROR: $1 failed. Exiting."
        exit 1
    fi
}

echo "--- Starting Shared VPC Setup Script ---"

# --- 1. Create Host Projects ---
echo "1. Creating Dev Host Project: ${DEV_HOST_PROJECT_ID}..."
gcloud projects create ${DEV_HOST_PROJECT_ID} \
    --name="${DEV_HOST_PROJECT_NAME}" \
    --organization="${ORG_ID}" \
    --labels=environment=development,shared-vpc=host
check_success "Dev Host Project creation"

echo "1. Creating Prod Host Project: ${PROD_HOST_PROJECT_ID}..."
gcloud projects create ${PROD_HOST_PROJECT_ID} \
    --name="${PROD_HOST_PROJECT_NAME}" \
    --organization="${ORG_ID}" \
    --labels=environment=production,shared-vpc=host
check_success "Prod Host Project creation"

echo "Waiting for projects to become fully active (this may take a few moments)..."
sleep 30 # Give some time for project creation to propagate

# --- 2. Enable Required APIs on Host Projects ---
echo "2. Enabling Compute Engine API on Dev Host Project..."
gcloud services enable compute.googleapis.com --project=${DEV_HOST_PROJECT_ID}
check_success "Compute Engine API enablement on Dev Host"

echo "2. Enabling Compute Engine API on Prod Host Project..."
gcloud services enable compute.googleapis.com --project=${PROD_HOST_PROJECT_ID}
check_success "Compute Engine API enablement on Prod Host"

echo "Waiting for APIs to enable..."
sleep 15 # Give some time for API enablement to propagate

# --- 3. Create VPC Networks and Subnets in Host Projects ---

# Dev Host Project Network
echo "3. Creating VPC network '${DEV_VPC_NETWORK_NAME}' in Dev Host Project '${DEV_HOST_PROJECT_ID}'..."
gcloud compute networks create ${DEV_VPC_NETWORK_NAME} \
    --project=${DEV_HOST_PROJECT_ID} \
    --subnet-mode=custom \
    --mtu=1460 \
    --description="Shared VPC network for development environments."
check_success "Dev VPC network creation"

echo "3. Creating subnet '${DEV_SUBNET_NAME_1}' in Dev VPC network..."
gcloud compute networks subnets create ${DEV_SUBNET_NAME_1} \
    --project=${DEV_HOST_PROJECT_ID} \
    --network=${DEV_VPC_NETWORK_NAME} \
    --range=${DEV_SUBNET_IP_RANGE_1} \
    --region=${DEV_SUBNET_REGION_1} \
    --description="Development subnet in ${DEV_SUBNET_REGION_1}."
check_success "Dev subnet creation"

# Prod Host Project Network
echo "3. Creating VPC network '${PROD_VPC_NETWORK_NAME}' in Prod Host Project '${PROD_HOST_PROJECT_ID}'..."
gcloud compute networks create ${PROD_VPC_NETWORK_NAME} \
    --project=${PROD_HOST_PROJECT_ID} \
    --subnet-mode=custom \
    --mtu=1460 \
    --description="Shared VPC network for production environments."
check_success "Prod VPC network creation"

echo "3. Creating subnet '${PROD_SUBNET_NAME_1}' in Prod VPC network..."
gcloud compute networks subnets create ${PROD_SUBNET_NAME_1} \
    --project=${PROD_HOST_PROJECT_ID} \
    --network=${PROD_VPC_NETWORK_NAME} \
    --range=${PROD_SUBNET_IP_RANGE_1} \
    --region=${PROD_SUBNET_REGION_1} \
    --description="Production subnet in ${PROD_SUBNET_REGION_1}."
check_success "Prod subnet creation"

# --- 4. Enable Shared VPC on Host Projects ---
echo "4. Enabling Shared VPC on Dev Host Project '${DEV_HOST_PROJECT_ID}'..."
gcloud compute shared-vpc enable ${DEV_HOST_PROJECT_ID}
check_success "Enabling Shared VPC on Dev Host"

echo "4. Enabling Shared VPC on Prod Host Project '${PROD_HOST_PROJECT_ID}'..."
gcloud compute shared-vpc enable ${PROD_HOST_PROJECT_ID}
check_success "Enabling Shared VPC on Prod Host"

echo "--- Shared VPC Host Projects and Networks Created Successfully! ---"
echo ""
echo "Next Steps:"
echo "1. Create your Service Projects (e.g., 'dev-app-a-project', 'prod-app-b-project')."
echo "2. Attach your Service Projects to their respective Host Projects using 'gcloud compute shared-vpc associated-projects add'."
echo "   Example for Dev:"
echo "   gcloud compute shared-vpc associated-projects add SERVICE_PROJECT_ID --host-project=${DEV_HOST_PROJECT_ID}"
echo "3. Grant 'compute.networkUser' role to service accounts or users in Service Projects on specific subnets of their Host Project."
echo "   Example for a service account in a Dev Service Project using the Dev Host Project's subnet:"
echo "   gcloud compute shared-vpc associated-projects add-iam-policy-binding SERVICE_PROJECT_ID \\"
echo "       --host-project=${DEV_HOST_PROJECT_ID} \\"
echo "       --member='serviceAccount:SERVICE_ACCOUNT_NAME@SERVICE_PROJECT_ID.iam.gserviceaccount.com' \\"
echo "       --role='roles/compute.networkUser' \\"
echo "       --subnet='${DEV_VPC_NETWORK_NAME}/regions/${DEV_SUBNET_REGION_1}/subnetworks/${DEV_SUBNET_NAME_1}'"
echo "   (Note: For the above, you might first need to add the service project, then grant the role on the host project)."
echo "4. Configure firewall rules in each host project as needed."

