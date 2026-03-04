# Q21 - Bolt: AuthzPolicy Multiple Rules and Precedence

## Namespace
`q21-bolt`

## Workloads
- `client` (SA: default, curlimages/curl)
- `api-svc` (SA: api-svc, kong/httpbin:latest)

## Task

1. Create two AuthorizationPolicies on `api-svc`:
   - **DENY policy**: Block all requests to path `/admin/*`
   - **ALLOW policy**: Allow all requests from ServiceAccount `client`

2. Understand precedence: DENY rules always take precedence over ALLOW rules, even if the same source is allowed elsewhere.

3. Verify the policies are applied correctly.

## Verification

```bash
# Should succeed (allowed by ALLOW policy)
kubectl exec -it deploy/client -n q21-bolt -- curl http://api-svc:8000/get

# Should be denied (DENY policy blocks /admin/*)
kubectl exec -it deploy/client -n q21-bolt -- curl http://api-svc:8000/admin/config
# Expected: 403 Forbidden
```

## Resources to Create

- AuthorizationPolicy (DENY, action: DENY, rules matching path /admin/*)
- AuthorizationPolicy (ALLOW, action: ALLOW, rules matching sourceRef SA:client)
