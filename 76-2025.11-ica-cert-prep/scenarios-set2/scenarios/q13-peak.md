# q13-peak: VirtualService Catch-all with Version Routing

**Namespace**: q13-peak

## Workloads
- `client` (curlimages/curl) - initiates requests
- `backend` with three versions (v1, v2, v3) - kong/httpbin on port 8000

## Task
1. Create a DestinationRule for `backend` with subsets: v1, v2, v3 (matched by `version` label)
2. Create a VirtualService for `backend` with routing rules:
   - Requests with header `x-version: v2` → route to v2 subset
   - Requests with header `x-version: v3` → route to v3 subset
   - All other requests (catch-all) → route to v1 subset
   - **Important**: Place specific rules BEFORE the catch-all rule

## Verification
```bash
# Default traffic (catch-all) goes to v1
kubectl exec -it <client-pod> -n q13-peak -- curl backend:8000/get | jq '.headers.user-agent'

# Route to v2 with header
kubectl exec -it <client-pod> -n q13-peak -- curl -H "x-version: v2" backend:8000/get

# Route to v3 with header
kubectl exec -it <client-pod> -n q13-peak -- curl -H "x-version: v3" backend:8000/get

# Verify VS configuration
kubectl get vs -n q13-peak -o yaml
```

## Resources to Create
- **DestinationRule** for `backend` with subsets: v1, v2, v3 (labeled by `version`)
- **VirtualService** for `backend` with match conditions and catch-all route
