# q40-xenith: Sidecar — outboundTrafficPolicy REGISTRY_ONLY

**Namespace:** `q40-xenith`

**Workloads:**
- `client` (curlimages/curl)
- `my-app` (kong/httpbin, port 8000→80)

## Task

Create a Sidecar with outboundTrafficPolicy mode `REGISTRY_ONLY`.

This blocks all traffic to services not in the Istio registry (no passthrough to unknown external hosts).

**Steps:**
1. Apply a Sidecar with outboundTrafficPolicy mode REGISTRY_ONLY (no passthrough for unknown services).
2. Create a VirtualService or ServiceEntry for `my-app` so it is registered.
3. Configure basic egress route to my-app.

## Verification

Test traffic to known service (my-app):

```bash
# Should work: my-app is in registry
kubectl exec deploy/client -n q40-xenith -- curl -s my-app:8000/get | head -5
```

Test traffic to unknown external service (if external access is available):

```bash
# Should fail: unknown host not in registry, no passthrough
kubectl exec deploy/client -n q40-xenith -- curl -s -o /dev/null -w "%{http_code}\n" httpbin.org
```

Expected: Known services work (200); unknown external services fail (0 or 000 status).

## Resources to Create

- **Sidecar**: outboundTrafficPolicy (mode: REGISTRY_ONLY)
- **ServiceEntry** or **VirtualService** for `my-app` (to register in Istio)
