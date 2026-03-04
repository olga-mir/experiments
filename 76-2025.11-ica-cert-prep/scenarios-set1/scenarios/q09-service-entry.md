# Q09 – ServiceEntry for External Services

**Domain:** Traffic Management
**Namespace:** q09
**Workloads:** sleep (no httpbin — this is about reaching external services)

## Task

Allow the sleep pod to access an external HTTP service through the mesh.

1. Create a `ServiceEntry` that registers `httpbin.org` as an external service:
   - Host: `httpbin.org`
   - Ports: 80 (HTTP) and 443 (HTTPS)
   - Resolution: DNS
   - Location: MESH_EXTERNAL
2. Optionally create a `VirtualService` to set a 3s timeout on requests to `httpbin.org`
3. Verify the sleep pod can reach the external service

## Verification

```bash
# Without ServiceEntry (may be blocked depending on outbound policy)
kubectl exec -n q09 deploy/sleep -- curl -sI http://httpbin.org/get

# After creating ServiceEntry — should work
kubectl exec -n q09 deploy/sleep -- curl -s http://httpbin.org/get | head -5

# Check that the service is known to the proxy
istioctl proxy-config clusters deploy/sleep -n q09 | grep httpbin.org
```

## Resources to create

- `networking.istio.io/ServiceEntry`
- `networking.istio.io/VirtualService` (optional, for timeout)
