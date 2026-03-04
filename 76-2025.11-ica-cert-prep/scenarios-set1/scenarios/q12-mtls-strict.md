# Q12 – Strict mTLS with PeerAuthentication

**Domain:** Securing Workloads
**Namespace:** q12
**Workloads:** httpbin, sleep

## Task

Enforce strict mutual TLS for the httpbin service.

1. Create a `PeerAuthentication` in namespace `q12` that enforces **STRICT** mTLS for all workloads
2. Verify that in-mesh clients can still reach httpbin
3. Verify that a request from a non-mesh pod would be rejected

## Verification

```bash
# In-mesh sleep should succeed (mTLS between proxies)
kubectl exec -n q12 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin:8000/get
# Expected: 200

# Check mTLS status
istioctl authn tls-check deploy/sleep.q12 httpbin.q12.svc.cluster.local

# Verify PeerAuthentication is applied
kubectl get peerauthentication -n q12

# Check proxy config for TLS settings
istioctl proxy-config endpoints deploy/sleep -n q12 | grep httpbin
```

## Resources to create

- `security.istio.io/PeerAuthentication` (mode: STRICT)
