# q02-titan: VirtualService Header-Based Routing

## Namespace
`q02-titan`

## Workloads
- **tester**: curlimages/curl (test pod)
- **backend-v1**: kong/httpbin with label `version: v1`
- **backend-v2**: kong/httpbin with label `version: v2`

## Task

1. Create a **DestinationRule** for `backend` with two subsets: `v1` (label `version: v1`) and `v2` (label `version: v2`)
2. Create a **VirtualService** that:
   - Routes to `v2` when header `x-version: v2` is present
   - Otherwise routes to `v1` (default)

## Verification

**Request without header (goes to v1):**
```bash
kubectl exec deploy/tester -n q02-titan -- curl -s backend:8000/headers | jq '.headers["X-Version"]'
```

**Request with header (goes to v2):**
```bash
kubectl exec deploy/tester -n q02-titan -- curl -s -H "x-version: v2" backend:8000/headers | jq '.headers["X-Version"]'
```

Expected: Responses should reflect routing to correct backend version (check response headers or httpbin server ID).

## Resources to Create
- Namespace: `q02-titan`
- Deployments: `backend-v1`, `backend-v2` with httpbin image
- Deployment: `tester`
- DestinationRule: backend (subsets v1, v2)
- VirtualService: backend (header-based routing)
