# Cloud Run Fortio Exploration Project

This project explores Cloud Run behavior using custom info service and Fortio load testing tools.

## Project Structure

- **src/**: Custom Go application that provides system information via HTTP endpoints
- **idtoken/**: Go utility for generating authentication tokens for Cloud Run services
- **scripts/**: Deployment scripts for bastion hosts and infrastructure
- **tests/**: Basic testing scripts for Fortio endpoints
- **docs/**: Documentation and example outputs
- **test-results/**: Output directory for test results

## Key Components

### Services
- **cloudrun-info**: Custom Go service that exposes system information
- **src-fortio**: Source Fortio service for load testing
- **dest-fortio**: Destination Fortio service for load testing

### Infrastructure
- Uses Direct VPC Egress for Cloud Run services
- Internal-only traffic with IAM invoker permissions
- Cloud NAT setup for external connectivity
- Bastion host for accessing internal services

## Main Operations

- `task deploy-info`: Deploy the custom info service
- `task deploy-src-fortio` / `task deploy-dest-fortio`: Deploy Fortio services
- `task print-authed-load-test-request`: Generate authenticated load test requests
- `./scripts/deploy-bastion.sh`: Deploy bastion host for internal access
- `./setup-cloud-nat.sh`: Configure Cloud NAT

## Security Model

- All Cloud Run services are internal-only
- IAM invoker permissions required
- Authentication tokens required for service-to-service communication
- Bastion host uses IAP tunnel for access

## Load Testing Workflow

1. Deploy source and destination Fortio services
2. Generate authentication tokens using idtoken utility
3. Create load test configuration
4. Execute tests from bastion host
5. Collect results via REST API endpoints