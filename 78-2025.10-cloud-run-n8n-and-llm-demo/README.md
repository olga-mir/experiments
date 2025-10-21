# Cloud Run N8N and LLM Demo

This project demonstrates deploying n8n workflow automation and LLM services on Google Cloud Run with private networking and secure access patterns.

## Architecture

- **VPC Network**: Custom VPC with private subnets
- **Cloud Run Services**: Internal-only services (no public internet exposure)
- **Bastion Host**: Compute Engine VM for accessing Cloud Run services via IAP
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

## Quick Start

**View available tasks:**
   ```bash
   task --list
   ```

**Setup complete infrastructure:**
   ```bash
   task setup-all
   ```
   This will:
   - Create VPC network and subnet
   - Configure firewall rules for IAP
   - Deploy bastion host

## Overview Tasks and Scripts

-  `task bastion-install-tools` - Copies the installation script (scripts/bastion-install-tools.sh) to bastion. This script installs network diagnostic tools and some common CLI utils. Run this on the bastion host

###  Gemma Testing

- `task bastion-copy-test-script`
  - Copies test-gemma.sh to bastion
  - Shows usage instructions

- `task bastion-test-gemma`
  - Runs the test directly from your laptop (executes on bastion)
  - Usage: task bastion-test-gemma PROMPT="What is Kubernetes?"
  - Default prompt: "Hello, how are you?"

  scripts/test-gemma.sh

  Tests the Gemma service with a POST request:
  - Automatically gets authentication token
  - Sends JSON payload to Gemma's Ollama API (/api/generate)
  - Pretty prints request and response with jq
  - Usage: ./test-gemma.sh "Your question here"

### Access n8n Locally

need to run both:
```
gcloud beta run services proxy n8n --region asia-southeast1 --project $PROJECT_ID
gcloud compute ssh [BASTION_NAME] --zone=[ZONE] -- -L 8080:localhost:8080
```
Both have dedeicated `tasks`


### Setup Tasks
- `task setup-network` - Create VPC network, subnet, and firewall rules
- `task setup-bastion` - Deploy bastion host with IAP access
- `task setup-all` - Run complete setup (network + bastion)

### Access Tasks
- `task connect-bastion` - SSH to bastion host via IAP tunnel

### Utility Tasks
- `task help` - Show all available tasks

## Network Configuration

### Subnet
- **VPC**: Defined by `$NETWORK` environment variable
- **Subnet**: Defined by `$SUBNETWORK` environment variable
- **CIDR Range**: 10.0.0.0/24
- **Private Google Access**: Enabled

### Firewall Rules
- **allow-iap-tunnel**: Allows SSH (TCP:22) from IAP range (35.235.240.0/20)
- **allow-internal-all**: Allows TCP/UDP/ICMP within 10.0.0.0/8

## Troubleshooting

### IAP Tunnel Connection Issues

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

## References

- [Cloud Run VPC Access](https://cloud.google.com/run/docs/configuring/vpc-direct-vpc)
- [Identity-Aware Proxy](https://cloud.google.com/iap/docs)
- [Cloud Run Security Best Practices](https://cloud.google.com/run/docs/securing/overview)
