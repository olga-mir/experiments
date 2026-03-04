# q20-apex: AuthorizationPolicy CUSTOM Action with External Authorizer

**Namespace**: q20-apex

## Workloads
- `tester` (curlimages/curl) - initiates requests
- `portal` (kong/httpbin) - service on port 8000

## Task
1. Create an AuthorizationPolicy on `portal` with:
   - Action: CUSTOM
   - Provider name: `my-ext-authz`
   - This delegates authorization decisions to an external authorizer service
   - **Note**: No actual external authorizer is running; this exercise focuses on the resource structure
2. Apply the policy
3. Verify the AuthorizationPolicy is correctly configured

## Verification
```bash
# Check the AuthorizationPolicy resource
kubectl get authorizationpolicy -n q20-apex -o yaml

# Verify the action field is CUSTOM
kubectl describe authorizationpolicy -n q20-apex | grep -A 10 "Action:"

# Expected output should show:
# Action: CUSTOM
# Provider: my-ext-authz

# Full YAML inspection
kubectl get ap -n q20-apex -o jsonpath='{.items[0].spec}'
```

## Resources to Create
- **AuthorizationPolicy** with:
  - `spec.action: CUSTOM`
  - `spec.provider.name: my-ext-authz`
  - `spec.selector.matchLabels.app: portal` (or appropriate label)
