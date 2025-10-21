# Cloud Run N8N and LLM Demo

This project demonstrates deploying n8n workflow automation and LLM services on Google Cloud Run with private networking and secure access patterns.

## Architecture

- **VPC Network**: VPC in the same project as Cloud Run services
- **Cloud Run Services**: Internal-only services
- **Bastion Host**: Compute Engine VM (with no public IP) for accessing Cloud Run services
- **Security**: Identity-Aware Proxy (IAP) for secure access without external IPs

## Prerequisites

- Google Cloud Project with billing enabled
- `gcloud` CLI installed and authenticated
- `task` (Taskfile) installed - [Installation guide](https://taskfile.dev/installation/)
- Required APIs enabled:
  - Compute Engine API
  - Cloud Run API
  - IAP API

## Environment Setup

Create a file (e.g., `.env` or `env.sh`) with the following variables and source it:

```bash
# Project where Cloud Run services and VPC are deployed
export PROJECT_ID="your-project-id"
export PROJECT_NAME="your-project-name"
export PROJECT_NUMBER="your-project-number"

# Network configuration
export NETWORK="cloud-run-vpc"
export SUBNETWORK="cloud-run-subnet"

# Region and zone
export REGION="us-central1"
export ZONE="us-central1-b"

# Your GCP user email
export USER_EMAIL="your-email@example.com"

# DNS record lives in this project (if using separate project)
export NETWORK_PROJECT_ID=""
export NETWORK_PROJECT_NUMBER=""
```

## Tasks

List all tools
```
$ task --list
$ task help
```

###  📁 tasks/bastion.yaml (Frequently used - Every session)

  - task bastion:setup - Create bastion host
  - task bastion:connect - SSH to bastion
  - task bastion:delete - Remove bastion
  - task bastion:tunnel - Create SSH tunnel (localhost:8080)
  - task bastion:copy-tools-script - Copy tools install script
  - task bastion:copy-n8n-test - Copy n8n test script
  - task bastion:copy-gemma-test - Copy gemma test script
  - task bastion:copy-all-scripts - Copy all scripts at once

###  📁 tasks/services.yaml (Cloud Run services - Both n8n & gemma)

  Service Accounts:
  - task services:setup-service-accounts - Create all service accounts

  n8n:
  - task services:deploy-n8n - Deploy n8n
  - task services:get-n8n-url - Get n8n URL
  - task services:delete-n8n - Delete n8n
  - task services:proxy-n8n - Proxy n8n locally

  Gemma:
  - task services:deploy-gemma - Deploy gemma
  - task services:get-gemma-url - Get gemma URL
  - task services:delete-gemma - Delete gemma
  - task services:proxy-gemma - Proxy gemma locally

  Combined:
  - task services:deploy-all - Deploy both services
  - task services:delete-all - Delete both services

###  📁 Taskfile.yaml (Main - Utility tasks only)

  - `task get-token` - Get auth token
  - `task extract-tools` - Create temp VM for tools

###  📁 tasks/vpc.yaml (Rarely used - VPC only)

  - task vpc:setup - Create VPC network, subnets, firewall rules
  - task vpc:delete - Delete entire VPC (destructive)

##  Typical Workflow

```bash
$ # On new project setup:
$   task vpc:setup
$
$ # Every session:
$   task bastion:setup
$   task bastion:connect
$
$   task bastion:delete
$
$ # Deploy services:
$   task services:deploy-all
```

### Access n8n Locally

need to run both:
```
gcloud beta run services proxy n8n --region asia-southeast1 --project $PROJECT_ID
gcloud compute ssh [BASTION_NAME] --zone=[ZONE] -- -L 8080:localhost:8080
```
Both have dedicated `tasks`

# Network Configuration

### Subnet
- **VPC**: Defined by `$NETWORK` environment variable
- **Subnet**: Defined by `$SUBNETWORK` environment variable
- **CIDR Range**: 10.0.0.0/24
- **Private Google Access**: Enabled

### Firewall Rules
- **allow-iap-tunnel**: Allows SSH (TCP:22) from IAP range (35.235.240.0/20)
- **allow-internal-all**: Allows TCP/UDP/ICMP within 10.0.0.0/8

# Troubleshooting

## IAP Tunnel Connection Issues

If you can't connect to the bastion:

1. Verify IAP API is enabled:
   ```bash
   gcloud services enable iap.googleapis.com --project=$PROJECT_ID
   ```

2. Check your IAM permissions - you need `roles/iap.tunnelResourceAccessor`

3. Verify firewall rules allow IAP range:
   ```bash
   gcloud compute firewall-rules describe allow-iap-tunnel --project=$PROJECT_ID
   ```

# References

- [Cloud Run VPC Access](https://cloud.google.com/run/docs/configuring/vpc-direct-vpc)
- [Identity-Aware Proxy](https://cloud.google.com/iap/docs)
- [Cloud Run Security Best Practices](https://cloud.google.com/run/docs/securing/overview)
