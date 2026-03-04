# Q13 – mTLS Migration (PERMISSIVE → STRICT)

**Domain:** Securing Workloads
**Namespace:** q13
**Workloads:** httpbin, sleep

## Task

Simulate a zero-downtime mTLS migration.

1. Start by creating a `PeerAuthentication` in **PERMISSIVE** mode (accepts both plaintext and mTLS)
2. Verify httpbin is reachable from both mesh and non-mesh clients
3. Create a `DestinationRule` with `tls.mode: ISTIO_MUTUAL` to ensure mesh clients use mTLS
4. Migrate the `PeerAuthentication` to **STRICT** mode
5. Verify mesh clients still work

## Verification

```bash
# Step 1: PERMISSIVE — both plaintext and mTLS accepted
kubectl exec -n q13 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin:8000/get
# Expected: 200

# Step 2: After switching to STRICT — mesh clients still work
kubectl exec -n q13 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin:8000/get
# Expected: 200

# Check mTLS is actually being used
istioctl proxy-config endpoints deploy/sleep -n q13 | grep httpbin
# Should show STRICT or mTLS
```

## Resources to create

- `security.istio.io/PeerAuthentication` (PERMISSIVE, then STRICT)
- `networking.istio.io/DestinationRule` (tls.mode: ISTIO_MUTUAL)
