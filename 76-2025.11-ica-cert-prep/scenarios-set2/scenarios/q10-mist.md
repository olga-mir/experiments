# q10-mist: VirtualService Delegate (Multi-VS for Same Host)

## Namespace
`q10-mist`

## Workloads
- **tester**: curlimages/curl (test pod)
- **portal**: kong/httpbin (port 8000 → 80)
- **store**: kong/httpbin (port 8000 → 80)

## Task

1. Create a **root VirtualService** for host `portal` that:
   - Delegates traffic matching `/store/*` to another VirtualService
   - Routes all other traffic to `portal:8000`
2. Create a **delegate VirtualService** that:
   - Handles `/store/*` paths
   - Rewrites `/store/*` to `/`
   - Routes to `store:8000`
3. Verify that traffic is correctly delegated based on path

## Verification

**Request to portal root (routes to portal):**
```bash
kubectl exec deploy/tester -n q10-mist -- curl -s portal:8000/get | jq '.url'
```

**Request to store path (delegates to store):**
```bash
kubectl exec deploy/tester -n q10-mist -- curl -s portal:8000/store/get | jq '.url'
```

Expected: First request hits portal, second hits store (URI rewritten from /store/get to /get).

## Resources to Create
- Namespace: `q10-mist`
- Deployments: `tester`, `portal`, `store` with httpbin image
- VirtualService (root): portal (delegates /store/*)
- VirtualService (delegate): portal-store (handles /store/* with rewrite)
