# Q15 – AuthorizationPolicy DENY Rules

**Domain:** Securing Workloads
**Namespace:** q15
**Workloads:** httpbin, sleep

## Task

Use DENY policies to block specific traffic patterns.

1. Create an `AuthorizationPolicy` with action **DENY** that blocks:
   - All `DELETE` requests to httpbin
   - All requests to the `/status/` path prefix
2. Verify that GET to `/get` still works
3. Verify that DELETE and `/status/*` are blocked

## Verification

```bash
# GET /get — should succeed
kubectl exec -n q15 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin:8000/get
# Expected: 200

# DELETE — should be denied
kubectl exec -n q15 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" -X DELETE httpbin:8000/delete
# Expected: 403

# GET /status/200 — should be denied
kubectl exec -n q15 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin:8000/status/200
# Expected: 403
```

## Resources to create

- `security.istio.io/AuthorizationPolicy` (action: DENY, operation methods/paths)
