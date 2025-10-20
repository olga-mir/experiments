# Cloud Run N8N and LLM Demo - AI Assistant Context

## Project Overview

This is a demonstration project for deploying n8n workflow automation and LLM services on Google Cloud Run with secure, private networking configuration.

## Key Architecture Decisions

### Networking
- **Private-only setup**: No external IPs on any resources
- **IAP-based access**: All access to bastion and Cloud Run services goes through Identity-Aware Proxy
- **Single VPC**: All resources in the same project and VPC (no Shared VPC or multi-project setup)
- **Subnet design**: Single subnet (10.0.0.0/24) for Cloud Run services and bastion host

### Security Model
- **Internal Cloud Run**: All Cloud Run services use `--ingress internal`
- **Service Account per service**: Each Cloud Run service should have its own dedicated service account
- **No public endpoints**: Services are only accessible from within the VPC or via IAP tunnel
- **OS Login**: Bastion uses OS Login for SSH key management

## Environment Variables

The project relies on environment variables sourced from a user's local environment file:

- `PROJECT_ID` - GCP project ID where resources are deployed
- `PROJECT_NUMBER` - GCP project number
- `PROJECT_NAME` - Human-readable project name
- `REGION` - GCP region (e.g., us-central1)
- `ZONE` - GCP zone (e.g., us-central1-b)
- `NETWORK` - VPC network name
- `SUBNETWORK` - Subnet name
- `USER_EMAIL` - User's GCP email for IAM bindings
- `NETWORK_PROJECT_ID` - (Optional) Separate project for DNS if needed
- `NETWORK_PROJECT_NUMBER` - (Optional) Project number for DNS project

## Code Patterns and Preferences

### Task Automation
- Use **Taskfile (Task)** for orchestration
- Keep Taskfile clean - avoid large bash chunks
- Extract complex logic into separate bash scripts in `scripts/` directory
- Reference pattern: `/Users/olga/repos/experiments/88-2024.10-cloud-run-fortio/Taskfile.yaml`

### Bash Scripts
- Always use `set -euo pipefail` for proper error handling
- Validate required environment variables at script start
- Make scripts idempotent (check if resources exist before creating)
- Provide clear output messages for user feedback
- Include retry logic for flaky operations (like SSH to new VMs)

### Script Organization
```
scripts/
├── setup-network.sh      # VPC, subnets, firewall rules
├── setup-bastion.sh      # Bastion host deployment
└── [future scripts]      # Cloud Run deployment, service accounts, etc.
```

## Current Implementation Status

### Completed
- ✅ VPC network setup with custom subnet
- ✅ Firewall rules for IAP tunnel and internal communication
- ✅ Bastion host deployment with IAP access
- ✅ Task-based automation framework
- ✅ Environment variable validation

### Not Yet Implemented
- ⏳ Cloud Run service deployment
- ⏳ Service account creation and IAM bindings
- ⏳ Cloud NAT setup (for outbound internet if needed)
- ⏳ N8N workflow service deployment
- ⏳ LLM inference service deployment
- ⏳ DNS configuration

## Important Notes for AI Assistants

1. **User has GCP expertise**: Assume knowledge of Kubernetes and GCP - no need to over-explain basics

2. **No organization**: This is a standalone project, not using GCP Organization or Shared VPC

3. **Script patterns**: Follow the patterns from the reference project at `/Users/olga/repos/experiments/88-2024.10-cloud-run-fortio/`

4. **Idempotency**: All scripts should be safe to run multiple times without errors

5. **Cloud Run deployment pattern**: When deploying Cloud Run:
   - Use `--no-allow-unauthenticated`
   - Use `--ingress internal`
   - Use `--network` and `--subnet` flags
   - Use `--vpc-egress all-traffic`
   - Use `--execution-environment gen2`
   - Bind IAM policies for `roles/run.invoker` to user and service accounts

6. **Service accounts**: Each Cloud Run service should have its own service account with minimal permissions

## Testing and Validation

### Testing Cloud Run Access from Bastion

From the bastion host, Cloud Run services can be accessed using:
```bash
TOKEN=$(gcloud auth print-identity-token)
curl -H "Authorization: Bearer $TOKEN" https://SERVICE_URL
```

### Verifying Network Configuration
- Check VPC: `gcloud compute networks describe $NETWORK`
- Check subnet: `gcloud compute networks subnets describe $SUBNETWORK --region=$REGION`
- Check firewall: `gcloud compute firewall-rules list --filter="network:$NETWORK"`

## Common Tasks for Future Development

1. **Adding new Cloud Run service**: Create script in `scripts/deploy-[service-name].sh`
2. **Service account setup**: Create script in `scripts/setup-service-accounts.sh`
3. **Cloud NAT**: Create script in `scripts/setup-cloud-nat.sh` if outbound internet needed
4. **Load testing**: Can use Fortio pattern from reference project

## References and Related Projects

- Reference implementation: `/Users/olga/repos/experiments/88-2024.10-cloud-run-fortio/`
- Related patterns available in other experiment folders in `/Users/olga/repos/experiments/`
