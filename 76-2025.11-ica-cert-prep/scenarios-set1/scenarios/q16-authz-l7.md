# Q16 – L7 AuthorizationPolicy (Path, Method, Headers)

**Domain:** Securing Workloads
**Namespace:** q16
**Workloads:** httpbin, sleep

## Task

Create a fine-grained L7 authorization policy using multiple conditions.

1. Create an `AuthorizationPolicy` for `httpbin` that **allows** requests only when ALL of:
   - Method is `GET`
   - Path matches `/get` or `/headers`
   - Request has header `x-team: platform`
2. All other requests should be denied

## Verification

```bash
# GET /get with correct header — should succeed
kubectl exec -n q16 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" -H "x-team: platform" httpbin:8000/get
# Expected: 200

# GET /get without header — should fail
kubectl exec -n q16 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin:8000/get
# Expected: 403

# POST /post with header — should fail (wrong method)
kubectl exec -n q16 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" -X POST -H "x-team: platform" httpbin:8000/post
# Expected: 403

# GET /ip with header — should fail (wrong path)
kubectl exec -n q16 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" -H "x-team: platform" httpbin:8000/ip
# Expected: 403
```

## Resources to create

- `security.istio.io/AuthorizationPolicy` (action: ALLOW, operation + when conditions)

## Note

L7 policies in ambient mode require a **waypoint proxy**. Make sure the namespace has one deployed or is using sidecar mode.
