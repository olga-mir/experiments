# Q24 - Edge: AuthzPolicy with Source Namespaces and Principals

## Namespace
`q24-edge`

## Workloads
- `tester` (SA: tester, curlimages/curl)
- `backend` (SA: backend, kong/httpbin:latest)

## Task

1. Create an AuthorizationPolicy on `backend` that ALLOWs requests.

2. The policy must match:
   - Source namespace: `q24-edge`
   - Principal: `cluster.local/ns/q24-edge/sa/tester`

3. This combines both namespace and principal-level matching for fine-grained access control.

## Verification

```bash
# From tester to backend (should succeed - matches NS and principal)
kubectl exec -it tester -n q24-edge -- curl http://backend:8000/get

# Verify policy structure
kubectl get authorizationpolicy -n q24-edge -o yaml
```

## Resources to Create

- AuthorizationPolicy (ALLOW, sourceNamespaces: q24-edge, principals: cluster.local/ns/q24-edge/sa/tester)
