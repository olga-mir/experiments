# q19-zinc: AuthorizationPolicy Combining SA, Methods, and Paths

**Namespace**: q19-zinc

## Workloads
- `client` (curlimages/curl) with ServiceAccount `client` - initiates requests
- `tester` (curlimages/curl) with ServiceAccount `tester` - initiates requests
- `web` (kong/httpbin) - service on port 8000
- `backend` (kong/httpbin) - service on port 8000

## Task
1. Create an AuthorizationPolicy on `backend` with action ALLOW that:
   - Rule 1: Allow ServiceAccount `client` with GET method on paths `/get` and `/headers`
   - Rule 2: Allow ServiceAccount `tester` with POST method on path `/post`
   - All other access is implicitly denied
2. Apply the policy
3. Verify the fine-grained access control

## Verification
```bash
# From client: GET /get is allowed
kubectl exec -it <client-pod> -n q19-zinc -- curl backend:8000/get

# From client: GET /headers is allowed
kubectl exec -it <client-pod> -n q19-zinc -- curl backend:8000/headers

# From client: POST /post is DENIED
kubectl exec -it <client-pod> -n q19-zinc -- curl -X POST backend:8000/post
# Should return 403

# From tester: POST /post is allowed
kubectl exec -it <tester-pod> -n q19-zinc -- curl -X POST backend:8000/post

# From tester: GET /get is DENIED
kubectl exec -it <tester-pod> -n q19-zinc -- curl backend:8000/get
# Should return 403

# Check the AuthorizationPolicy
kubectl get authorizationpolicy -n q19-zinc -o yaml
```

## Resources to Create
- **AuthorizationPolicy** on `backend` with:
  - `spec.action: ALLOW`
  - `spec.rules[0].from[].source.principals: ["cluster.local/ns/q19-zinc/sa/client"]`
    - `to[].operation.methods: ["GET"]`
    - `to[].operation.paths: ["/get", "/headers"]`
  - `spec.rules[1].from[].source.principals: ["cluster.local/ns/q19-zinc/sa/tester"]`
    - `to[].operation.methods: ["POST"]`
    - `to[].operation.paths: ["/post"]`
