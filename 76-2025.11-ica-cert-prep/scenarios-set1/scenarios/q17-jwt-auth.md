# Q17 – JWT Authentication (RequestAuthentication)

**Domain:** Securing Workloads
**Namespace:** q17
**Workloads:** httpbin, sleep

## Task

Configure JWT token validation for httpbin.

1. Create a `RequestAuthentication` for `httpbin` that:
   - Validates JWTs issued by `https://accounts.example.com`
   - Uses JWKS from `https://raw.githubusercontent.com/istio/istio/release-1.26/security/tools/jwt/samples/jwks.json`
2. Create an `AuthorizationPolicy` that:
   - Requires a valid JWT (denies requests without a token or with an invalid token)
3. Verify that requests with a valid token succeed and others fail

## Verification

```bash
# Without token — should be denied (403)
kubectl exec -n q17 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin:8000/get
# Expected: 403

# With invalid token — should be denied (401)
kubectl exec -n q17 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer invalid" httpbin:8000/get
# Expected: 401

# Get a sample JWT from Istio's test fixtures
TOKEN=$(curl -s https://raw.githubusercontent.com/istio/istio/release-1.26/security/tools/jwt/samples/demo.jwt)

# With valid token — should succeed
kubectl exec -n q17 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" -H "Authorization: Bearer $TOKEN" httpbin:8000/get
# Expected: 200
```

## Resources to create

- `security.istio.io/RequestAuthentication` (jwtRules)
- `security.istio.io/AuthorizationPolicy` (require requestPrincipals)
