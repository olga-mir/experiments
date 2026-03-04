# q14-ridge: Request Headers Manipulation

**Namespace**: q14-ridge

## Workloads
- `tester` (curlimages/curl) - initiates requests
- `my-app` (kong/httpbin) - backend service on port 8000

## Task
1. Create a VirtualService for `my-app` that:
   - Adds a request header `x-custom: injected-by-mesh` before forwarding
   - Removes the request header `user-agent` before forwarding
2. Apply the configuration
3. Verify the headers are correctly manipulated

## Verification
```bash
# Send request from tester pod to my-app
kubectl exec -it <tester-pod> -n q14-ridge -- curl my-app:8000/headers | jq '.headers'

# Should see:
# - "x-custom": "injected-by-mesh"
# - NO "user-agent" header

# Check VirtualService configuration
kubectl get vs -n q14-ridge -o yaml
```

## Resources to Create
- **VirtualService** for `my-app` with:
  - `spec.http[].headers.request.add: {"x-custom": "injected-by-mesh"}`
  - `spec.http[].headers.request.remove: ["user-agent"]`
