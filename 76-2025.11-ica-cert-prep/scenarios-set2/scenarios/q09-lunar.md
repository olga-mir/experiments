# q09-lunar: VirtualService URI Rewrite

## Namespace
`q09-lunar`

## Workloads
- **client**: curlimages/curl (test pod)
- **api-svc**: kong/httpbin (port 8000 → 80)

## Task

1. Create a **VirtualService** for `api-svc` that:
   - Matches URIs with prefix `/api/v1/`
   - Rewrites the URI from `/api/v1/*` to `/` (strips the prefix)
   - Routes to `api-svc:8000`
2. Verify that requests to `/api/v1/get` are rewritten and reach the correct endpoint

## Verification

**Request with /api/v1 prefix:**
```bash
kubectl exec deploy/client -n q09-lunar -- curl -s api-svc:8000/api/v1/get | jq '.url'
```

**Direct request to /get (for comparison):**
```bash
kubectl exec deploy/client -n q09-lunar -- curl -s api-svc:8000/get | jq '.url'
```

Expected: Both requests should return equivalent responses. The first is rewritten to match the second.

## Resources to Create
- Namespace: `q09-lunar`
- Deployments: `client`, `api-svc` with httpbin image
- VirtualService: api-svc (URI prefix match with rewrite)
