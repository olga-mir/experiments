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

## Available Tasks

### Setup Tasks
- `task setup-network` - Create VPC network, subnet, and firewall rules
- `task setup-bastion` - Deploy bastion host with IAP access
- `task setup-all` - Run complete setup (network + bastion)

### Access Tasks
- `task connect-bastion` - SSH to bastion host via IAP tunnel

### Utility Tasks
- `task show-config` - Display current configuration
- `task help` - Show all available tasks

### Cleanup Tasks
- `task delete-bastion` - Remove bastion host
- `task delete-network` - Remove all network infrastructure (destructive!)

## Network Configuration

### VPC Network
- **Name**: Defined by `$NETWORK` environment variable
- **Subnet Mode**: Custom
- **BGP Routing**: Regional

### Subnet
- **Name**: Defined by `$SUBNETWORK` environment variable
- **CIDR Range**: 10.0.0.0/24
- **Private Google Access**: Enabled

### Firewall Rules
- **allow-iap-tunnel**: Allows SSH (TCP:22) from IAP range (35.235.240.0/20)
- **allow-internal-all**: Allows TCP/UDP/ICMP within 10.0.0.0/8

## Security Features

1. **No External IPs**: All resources use private IPs only
2. **IAP Authentication**: Secure access via Identity-Aware Proxy
3. **Internal-only Cloud Run**: Services not exposed to public internet
4. **OS Login**: Cloud-based SSH key management
5. **Service Account Authentication**: Cloud Run services use dedicated service accounts

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

## Next Steps

- Deploy Cloud Run services with `--network` and `--subnet` flags
- Configure service accounts for Cloud Run
- Set up Cloud NAT for outbound internet access (if needed)
- Deploy n8n workflow automation service
- Deploy LLM inference services

## References

- [Cloud Run VPC Access](https://cloud.google.com/run/docs/configuring/vpc-direct-vpc)
- [Identity-Aware Proxy](https://cloud.google.com/iap/docs)
- [Cloud Run Security Best Practices](https://cloud.google.com/run/docs/securing/overview)
