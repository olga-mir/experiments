# q17-wave: AuthorizationPolicy ALLOW by ServiceAccount

**Namespace**: q17-wave

## Workloads
- `client` (curlimages/curl) with ServiceAccount `client` - initiates requests
- `payments` (kong/httpbin) - service on port 8000
- `store` (kong/httpbin) - service on port 8000, ServiceAccount `store`

## Task
1. Create an AuthorizationPolicy on the `payments` service that:
   - Action: ALLOW
   - Only allows requests from ServiceAccount `client` in namespace q17-wave
   - Implicitly denies all other requests
2. Apply the policy
3. Verify access control is enforced

## Verification
```bash
# Allowed: client pod can access payments
kubectl exec -it <client-pod> -n q17-wave -- curl payments:8000/get

# Denied: other service accounts (store) cannot access payments
# This requires testing from another pod with different SA
kubectl exec -it <store-pod> -n q17-wave -- curl payments:8000/get
# Should fail with 403 or connection error

# Check the AuthorizationPolicy
kubectl get authorizationpolicy -n q17-wave -o yaml
```

## Resources to Create
- **AuthorizationPolicy** named `payments-allow-client` with:
  - `spec.action: ALLOW`
  - `spec.rules[].from[].source.principals: ["cluster.local/ns/q17-wave/sa/client"]`
  - `spec.selector.matchLabels.app: payments` (or appropriate label)
