# q03-nova: VirtualService Path-Based Routing

## Namespace
`q03-nova`

## Workloads
- **client**: curlimages/curl (test pod)
- **api-svc**: kong/httpbin (port 8000 → 80)
- **portal**: kong/httpbin (port 8000 → 80)

## Task

1. Create a **VirtualService** for host `api-svc` with path-based routing:
   - Routes `/portal/*` (prefix match) to `portal:8000`
   - Routes all other paths to `api-svc:8000`
2. Verify traffic reaches the correct backend based on URL path

## Verification

**Request to api-svc root (goes to api-svc):**
```bash
kubectl exec deploy/client -n q03-nova -- curl -s api-svc:8000/get | jq '.url'
```

**Request to portal path (goes to portal):**
```bash
kubectl exec deploy/client -n q03-nova -- curl -s api-svc:8000/portal/get | jq '.url'
```

Expected: First request shows `api-svc` endpoint, second shows `portal` endpoint.

## Resources to Create
- Namespace: `q03-nova`
- Deployments: `client`, `api-svc`, `portal` with httpbin image
- VirtualService: api-svc (path-based routing with prefix /portal/*)
