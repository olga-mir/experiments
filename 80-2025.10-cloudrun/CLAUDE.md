# Claude Instructions for GCP VPC and Cloud Run Project with Crossplane

## Project Context

This project implements shared VPC infrastructure and Cloud Run services on GCP using spec-kit methodology with Crossplane. The user has expertise in Kubernetes and GCP.

## Technology Stack

- **Infrastructure Platform**: GKE cluster with Crossplane. This cluster exists and it managed in a separate repository.
- **Infrastructure as Code**: Crossplane Compositions and Custom Resource Definitions (XRDs)
- **Cloud Platform**: Google Cloud Platform (GCP)
- **Methodology**: Specification-Driven Development using spec-kit
- **Target Services**: Shared VPC, Cloud Run, Cloud NAT, Load Balancers

## Key Implementation Guidelines

### Crossplane-First Approach
- Always prefer Crossplane Compositions over Terraform modules
- Use Kubernetes Custom Resources for infrastructure provisioning
- Design for GitOps workflows with FluxCD
- Create self-service APIs through XRDs and Compositions

### Spec-Kit Workflow Commands
When the user asks for spec-kit implementation, use these exact commands:

1. **Specification Phase**: `/specify [detailed infrastructure requirements]`
2. **Planning Phase**: `/plan [technical approach with Crossplane]`
3. **Task Generation**: `/tasks [break down into Crossplane-specific tasks]`
4. **Implementation**: `/implement [execute tasks one by one]`

### Infrastructure Patterns
- Multi-environment support (dev, staging, production)
- Shared VPC architecture with isolated subnets
- VPC-native Cloud Run services
- Direct VPC Egress
- Load balancer integration with SSL management
- Kubernetes-native monitoring and logging

### File Structure Expectations
```
crossplane/
├── xrds/              # Custom Resource Definitions
├── compositions/      # Reusable infrastructure patterns
├── environments/      # Environment-specific configs
└── examples/          # Sample usage patterns

specs/                 # Spec-kit generated specifications
kubernetes/            # Additional K8s resources
tests/                # Infrastructure validation tests
```

## Development Workflow

1. **Always start with specification**: Use `/specify` to capture business requirements
2. **Create technical plans**: Use `/plan` with Crossplane-specific architecture
3. **Break down work**: Use `/tasks` for actionable Crossplane implementations
4. **Implement systematically**: Use `/implement` following the generated tasks

## Testing and Validation

- Test Crossplane Compositions before deployment
- Validate Custom Resource schemas
- Ensure RBAC policies are properly configured
- Verify GitOps integration works correctly

## Security Considerations

- Follow least privilege principle for IAM roles
- Implement proper Kubernetes RBAC
- Use private networking for Cloud Run services
- Ensure SSL/TLS termination at load balancer level

## When Working on This Project

1. **Read the implementation guide**: Refer to `spec-kit-crossplane-guide.md` for detailed steps
2. **Follow spec-kit methodology**: Always use the four-phase approach
3. **Prioritize Crossplane**: Choose Crossplane solutions over other IaC tools
4. **Think Kubernetes-native**: Design for Kubernetes APIs and workflows
5. **Enable self-service**: Create abstractions that teams can use independently

## Common Tasks

- Creating XRDs for infrastructure APIs
- Writing Compositions for reusable patterns
- Setting up environment-specific configurations
- Implementing GitOps workflows
- Creating developer documentation and examples

## Important Notes

- User has expertise in Kubernetes and GCP - avoid basic explanations
- Focus on Crossplane-specific implementations
- Prioritize practical, actionable guidance
- Always reference the spec-kit methodology when implementing features
