# Q10 – Egress Gateway Control

**Domain:** Traffic Management
**Namespace:** q10
**Workloads:** httpbin, sleep

## Task

Route outbound traffic through an Istio egress gateway.

1. Ensure an egress gateway is deployed (check `istio-egressgateway` in `istio-system`)
2. Create a `ServiceEntry` for an external host (e.g., `httpbin.org`)
3. Create a `Gateway` resource for the egress gateway listening on port 80
4. Create a `VirtualService` that:
   - Matches traffic to `httpbin.org` from the mesh
   - Routes it through the egress gateway
5. Create a `DestinationRule` for the egress gateway
6. Verify traffic flows through the egress gateway

## Verification

```bash
# Test external access
kubectl exec -n q10 deploy/sleep -- curl -s http://httpbin.org/headers

# Check egress gateway logs for the request
kubectl logs -n istio-system deploy/istio-egressgateway | tail -5

# Verify the routing via proxy config
istioctl proxy-config routes deploy/sleep -n q10 | grep httpbin.org
```

## Resources to create

- `networking.istio.io/ServiceEntry`
- `networking.istio.io/Gateway` (egress)
- `networking.istio.io/VirtualService`
- `networking.istio.io/DestinationRule`
