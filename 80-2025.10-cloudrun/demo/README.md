# Cloud Run VPC Demo

This demo provisions a GCP VPC with subnets and deploys a Cloud Run service with Direct VPC Egress.

## Prerequisites

- gcloud CLI installed and configured
- Appropriate GCP permissions for:
  - VPC network and subnet creation
  - Cloud Run service deployment

## Configuration

Configured via env vars

All configuration variables are defined at the top of `network.sh` and can be modified as needed.

## Resources Provisioned

### Network Infrastructure
- **VPC**: `main-vpc` (custom mode)
- **Dev Subnet**: `apps-dev` (10.10.0.0/20)
- **Prod Subnet**: `apps-prod` (10.10.16.0/20)

### Cloud Run Service
- **Service Name**: `fortio-dev`
- **Image**: `gcr.io/fortio/fortio:latest`
- **VPC Configuration**: Direct VPC Egress (all traffic)
- **Subnet**: Connected to `apps-dev`
- **Authentication**: Invoker check enabled (no unauthenticated access)

## Usage

### Using Different GCP Accounts

To use different gcloud configurations for different accounts:

```bash
# List available configurations
gcloud config configurations list

# Activate the desired configuration
gcloud config configurations activate <your-config-name>

# Run the script
./network.sh
```

### Running the Script

```bash
chmod +x network.sh
./network.sh
```

### Idempotency

The script is fully idempotent. It checks for existing resources before creating them:
- If VPC exists, it will skip creation
- If subnets exist, they will be skipped
- Cloud Run service will be updated if it already exists

You can safely run the script multiple times without errors.

## Accessing the Cloud Run Service

After deployment, the script will output the service URL. Since invoker authentication is enabled, you'll need to authenticate requests:

```bash
# Get an identity token
TOKEN=$(gcloud auth print-identity-token)

# Make authenticated request
curl -H "Authorization: Bearer $TOKEN" <SERVICE_URL>
```

Alternatively, grant yourself the Cloud Run Invoker role:

```bash
gcloud run services add-iam-policy-binding fortio-dev \
    --region=australia-southeast1 \
    --member="user:<your-email>" \
    --role="roles/run.invoker"
```

## Customization

To modify the configuration, edit the variables at the top of `network.sh`:

- `PROJECT_ID` - Your GCP project ID
- `PROJECT_NUMBER` - Your GCP project number
- `REGION` - Deployment region
- `VPC_NAME` - VPC network name
- `SUBNET_DEV` / `SUBNET_PROD` - Subnet names
- `SUBNET_DEV_RANGE` / `SUBNET_PROD_RANGE` - IP ranges
- `CLOUD_RUN_SERVICE` - Cloud Run service name
- `CLOUD_RUN_IMAGE` - Container image to deploy

## Cleanup

To remove all resources:

```bash
# Delete Cloud Run service
gcloud run services delete fortio-dev --region=australia-southeast1 --quiet

# Delete subnets
gcloud compute networks subnets delete apps-dev --region=australia-southeast1 --quiet
gcloud compute networks subnets delete apps-prod --region=australia-southeast1 --quiet

# Delete VPC
gcloud compute networks delete main-vpc --quiet
```
