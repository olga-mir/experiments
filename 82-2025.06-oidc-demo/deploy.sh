#!/bin/bash

# GCP OIDC Setup Script for GitHub Actions
# This script configures the necessary GCP resources for GitHub Actions to authenticate using OIDC

set -eoux pipefail

required_vars=("PROJECT_ID" "GITHUB_REPO")
for var in "${required_vars[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "Error: $var environment variable is not set"
        exit 1
    fi
done

# GITHUB_REPO: username/repo

export POOL_ID="${POOL_ID:-github-actions-pool}"
export PROVIDER_ID="${PROVIDER_ID:-github-actions-provider}"
export SERVICE_ACCOUNT_ID="${SERVICE_ACCOUNT_ID:-github-actions-sa}"

# Helper function for retries with exponential backoff
retry_with_backoff() {
    local max_attempts=5
    local delay=2
    local attempt=1

    while [ $attempt -le $max_attempts ]; do
        if "$@"; then
            return 0
        fi

        if [ $attempt -eq $max_attempts ]; then
            echo "Command failed after $max_attempts attempts"
            return 1
        fi

        echo "Attempt $attempt failed. Retrying in ${delay}s..."
        sleep $delay
        delay=$((delay * 2))
        attempt=$((attempt + 1))
    done
}

# Helper function to wait for resource to exist
wait_for_resource() {
    local check_command="$1"
    local resource_name="$2"
    local max_wait=60
    local wait_time=0

    echo "Waiting for $resource_name to be available..."
    while [ $wait_time -lt $max_wait ]; do
        if eval "$check_command" >/dev/null 2>&1; then
            echo "$resource_name is now available"
            return 0
        fi
        sleep 5
        wait_time=$((wait_time + 5))
        echo "Still waiting for $resource_name... (${wait_time}s/${max_wait}s)"
    done

    echo "Timeout waiting for $resource_name"
    return 1
}

# Set the project
gcloud config set project $PROJECT_ID

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable iamcredentials.googleapis.com
gcloud services enable sts.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com

echo "Waiting for APIs to be fully enabled..."
sleep 10

# Create Workload Identity Pool
echo "Creating Workload Identity Pool..."
gcloud iam workload-identity-pools create $POOL_ID \
    --location="global" \
    --description="Pool for GitHub Actions" \
    --display-name="GitHub Actions Pool" || echo "Pool already exists"

# Wait for pool to be available
wait_for_resource "gcloud iam workload-identity-pools describe $POOL_ID --location=global --quiet" "Workload Identity Pool"

POOL_NAME=$(gcloud iam workload-identity-pools describe $POOL_ID --location="global" --format="value(name)")
GITHUB_OWNER=$(echo $GITHUB_REPO | cut -d'/' -f1)

# Create Workload Identity Provider
echo "Creating Workload Identity Provider..."
gcloud iam workload-identity-pools providers create-oidc $PROVIDER_ID \
    --location="global" \
    --workload-identity-pool=$POOL_ID \
    --display-name="GitHub Actions Provider" \
    --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository" \
    --attribute-condition="assertion.repository_owner=='${GITHUB_OWNER}'" \
    --issuer-uri="https://token.actions.githubusercontent.com" || echo "Provider already exists"

# Wait for provider to be available
wait_for_resource "gcloud iam workload-identity-pools providers describe $PROVIDER_ID --location=global --workload-identity-pool=$POOL_ID --quiet" "Workload Identity Provider"

# Create Service Account
echo "Creating Service Account..."
gcloud iam service-accounts create $SERVICE_ACCOUNT_ID \
    --description="Service account for GitHub Actions" \
    --display-name="GitHub Actions SA" || echo "Service Account already exists"

SERVICE_ACCOUNT_EMAIL="${SERVICE_ACCOUNT_ID}@${PROJECT_ID}.iam.gserviceaccount.com"

# Wait for service account to be available
wait_for_resource "gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL --quiet" "Service Account"

# Grant Storage Admin role to service account (for bucket operations)
echo "Granting Storage Admin role to service account..."
retry_with_backoff gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/storage.admin"

# Grant Service Account Token Creator role (required for impersonation)
echo "Granting Service Account Token Creator role..."
retry_with_backoff gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT_EMAIL}" \
    --role="roles/iam.serviceAccountTokenCreator"

# Allow GitHub Actions to impersonate the service account
echo "Allowing GitHub Actions to impersonate service account..."
echo "Using pool: $POOL_NAME"
echo "For repository: $GITHUB_REPO"

retry_with_backoff gcloud iam service-accounts add-iam-policy-binding $SERVICE_ACCOUNT_EMAIL \
    --role="roles/iam.workloadIdentityUser" \
    --member="principalSet://iam.googleapis.com/${POOL_NAME}/attribute.repository/${GITHUB_REPO}"

# Get the provider name for GitHub Actions configuration
PROVIDER_NAME="projects/${PROJECT_ID}/locations/global/workloadIdentityPools/${POOL_ID}/providers/${PROVIDER_ID}"

# Final verification
echo "Verifying configuration..."
sleep 5

echo "Checking Workload Identity Pool..."
gcloud iam workload-identity-pools describe $POOL_ID --location="global" --format="value(name)"

echo "Checking Workload Identity Provider..."
gcloud iam workload-identity-pools providers describe $PROVIDER_ID \
    --location="global" \
    --workload-identity-pool=$POOL_ID \
    --format="value(name)"

echo "Checking Service Account..."
gcloud iam service-accounts describe $SERVICE_ACCOUNT_EMAIL --format="value(email)"

echo ""
echo "Setup completed successfully!"
echo ""
echo "Add these secrets to your GitHub repository:"
echo "WIF_PROVIDER: $PROVIDER_NAME"
echo "WIF_SERVICE_ACCOUNT: $SERVICE_ACCOUNT_EMAIL"
echo "GCP_PROJECT_ID: $PROJECT_ID"
echo ""
echo "To add secrets to GitHub:"
echo "1. Go to your repository on GitHub"
echo "2. Navigate to Settings > Secrets and variables > Actions"
echo "3. Add the above secrets"
