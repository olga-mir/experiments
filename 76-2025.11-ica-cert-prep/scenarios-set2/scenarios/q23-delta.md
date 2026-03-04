# Q23 - Delta: AuthzPolicy Deny-All + Granular Allow

## Namespace
`q23-delta`

## Workloads
- `client` (SA: client, curlimages/curl)
- `sender` (SA: sender, curlimages/curl)
- `payments` (SA: payments, kong/httpbin:latest)
- `store` (SA: store, kong/httpbin:latest)

## Task

1. A deny-all AuthorizationPolicy already exists (empty spec: {}). Do not modify it.

2. Create two ALLOW AuthorizationPolicies:
   - Allow SA `client` to access `payments:8000` with GET method only
   - Allow SA `sender` to access `store:8000` with GET and POST methods

3. These policies must coexist with the deny-all policy (scoped per target).

## Verification

```bash
# From client: GET to payments (should succeed)
kubectl exec -it deploy/client -n q23-delta -- curl http://payments:8000/get

# From client: POST to payments (should fail - 403)
kubectl exec -it deploy/client -n q23-delta -- curl -X POST http://payments:8000/post

# From sender: GET to store (should succeed)
kubectl exec -it deploy/sender -n q23-delta -- curl http://store:8000/get

# From sender: POST to store (should succeed)
kubectl exec -it deploy/sender -n q23-delta -- curl -X POST http://store:8000/post

# From client to store (should fail - 403, not allowed)
kubectl exec -it deploy/client -n q23-delta -- curl http://store:8000/get
```

Note that you likely need to provide host header in curl: `-H "Host: payments"` 
Potentially need to specify explicit hosts in AP:
```
hosts: ["payments", "payments:*", "payments.q23-delta.svc.cluster.local"]
```
And also the port must be the port of the receiving pod, not the k8s svc. If you have access logs enabled then you can find hints in receiving pod logs `inbound:80`


## Resources to Create

- AuthorizationPolicy (ALLOW client → payments GET)
- AuthorizationPolicy (ALLOW sender → store GET,POST)
