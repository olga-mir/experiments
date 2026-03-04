# Q29 - Jewel: ServiceEntry with Multiple Endpoints

## Namespace
`q29-jewel`

## Workloads
- `client` (SA: default, curlimages/curl)

## Task

1. Create a ServiceEntry for `external-api`:
   - Hosts: `external-api.example.com`
   - Port: 443 (HTTPS/TLS)
   - Resolution: STATIC
   - Location: MESH_EXTERNAL

2. Add two endpoints with locality labels:
   - Endpoint 1: 1.1.1.1, locality: `us-west1`
   - Endpoint 2: 8.8.8.8, locality: `us-east1`

3. Locality labels enable geographic distribution policies.

## Verification

```bash
# Verify ServiceEntry structure with endpoints and localities
kubectl get serviceentry -n q29-jewel -o yaml

# Check endpoint configuration
kubectl get serviceentry external-api -n q29-jewel -o json | jq '.spec.endpoints'
```

## Resources to Create

- ServiceEntry (hosts: external-api.example.com, port 443 TLS, resolution STATIC, location MESH_EXTERNAL, endpoints with locality labels)
