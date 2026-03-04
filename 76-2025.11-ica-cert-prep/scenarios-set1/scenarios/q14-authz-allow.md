# Q14 – AuthorizationPolicy ALLOW Rules

**Domain:** Securing Workloads
**Namespace:** q14
**Workloads:** httpbin, sleep

## Task

Create fine-grained ALLOW authorization policies.

1. Create an `AuthorizationPolicy` for `httpbin` that **only allows** requests from the `sleep` service account in namespace `q14`
2. Verify that sleep in q14 can access httpbin
3. Verify that requests from other namespaces are denied

## Verification

```bash
# From q14 sleep — should succeed
kubectl exec -n q14 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin.q14:8000/get
# Expected: 200

# From another namespace — should be denied (403)
kubectl exec -n q01 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin.q14:8000/get
# Expected: 403

# Check the policy
kubectl get authorizationpolicy -n q14 -o yaml
```

## Resources to create

- `security.istio.io/AuthorizationPolicy` (action: ALLOW, source principals)
