# q18-xenon: AuthorizationPolicy DENY Specific Methods and Paths

**Namespace**: q18-xenon

## Workloads
- `caller` (curlimages/curl) - initiates requests
- `my-app` (kong/httpbin) - service on port 8000

## Task
1. Create an AuthorizationPolicy on `my-app` with action DENY that:
   - Denies DELETE method on ALL paths
   - Denies ANY method on paths matching `/admin/*`
   - Implicitly allows GET and POST to other paths
2. Apply the policy
3. Verify the access control works as expected

## Verification
```bash
# Allowed: GET requests to normal paths
kubectl exec -it <caller-pod> -n q18-xenon -- curl my-app:8000/get

# Allowed: POST requests to normal paths
kubectl exec -it <caller-pod> -n q18-xenon -- curl -X POST my-app:8000/post

# Denied: DELETE requests
kubectl exec -it <caller-pod> -n q18-xenon -- curl -X DELETE my-app:8000/get
# Should return 403 Forbidden

# Denied: Any request to /admin paths
kubectl exec -it <caller-pod> -n q18-xenon -- curl my-app:8000/admin/dashboard
# Should return 403 Forbidden

# Check the AuthorizationPolicy
kubectl get authorizationpolicy -n q18-xenon -o yaml
```

## Resources to Create
- **AuthorizationPolicy** with:
  - `spec.action: DENY`
  - `spec.rules[0].to[].operation.methods: ["DELETE"]` (all paths)
  - `spec.rules[1].to[].operation.paths: ["/admin/*"]` (any method)
