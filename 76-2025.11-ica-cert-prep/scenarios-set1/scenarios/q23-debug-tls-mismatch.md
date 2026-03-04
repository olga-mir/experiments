# Q23 – Troubleshoot: TLS Mode Mismatch

**Domain:** Troubleshooting
**Namespace:** q23
**Workloads:** httpbin, sleep
**Pre-deployed bug:** DestinationRule requires ISTIO_MUTUAL but PeerAuthentication disables mTLS

## Situation

Requests from sleep to httpbin fail with connection reset or 503 errors. The issue is a conflict between the DestinationRule TLS settings and the PeerAuthentication configuration.

## Task

1. Examine the DestinationRule and PeerAuthentication in namespace q23
2. Identify the TLS mode conflict:
   - The DestinationRule sets `tls.mode: ISTIO_MUTUAL` (client sends mTLS)
   - The PeerAuthentication sets `mtls.mode: DISABLE` (server expects plaintext)
3. Fix the conflict so both sides agree on TLS mode
4. Verify traffic flows correctly

## Hints

```bash
# Check the resources
kubectl get peerauthentication,destinationrule -n q23 -o yaml

# Check proxy-config for TLS settings
istioctl proxy-config endpoints deploy/sleep -n q23 | grep httpbin

# Run analysis
istioctl analyze -n q23
```

## Verification

```bash
# After fix — requests should succeed
kubectl exec -n q23 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin:8000/get
# Expected: 200
```
