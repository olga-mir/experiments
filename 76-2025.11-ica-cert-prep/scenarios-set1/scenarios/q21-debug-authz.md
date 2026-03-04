# Q21 – Troubleshoot: Overly Restrictive AuthorizationPolicy

**Domain:** Troubleshooting
**Namespace:** q21
**Workloads:** httpbin, sleep
**Pre-deployed bug:** An AuthorizationPolicy that blocks all traffic

## Situation

After deploying an AuthorizationPolicy in namespace q21, **all** requests to httpbin are being denied with 403. The sleep pod cannot reach httpbin at all, even though it should be allowed.

## Task

1. Identify the problematic AuthorizationPolicy
2. Understand why an empty-spec AuthorizationPolicy denies everything
3. Fix it to allow traffic from the sleep service account while denying other sources

## Hints

```bash
# Check what policies exist
kubectl get authorizationpolicy -n q21 -o yaml

# Test the current state
kubectl exec -n q21 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin:8000/get
# Expected before fix: 403

# Key insight: an AuthorizationPolicy with spec: {} and no rules = deny all
```

## Verification

```bash
# After fix — sleep in q21 should be able to reach httpbin
kubectl exec -n q21 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin:8000/get
# Expected: 200
```
