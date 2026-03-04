# Q02 – Classic Istio Ingress

**Domain:** Traffic Management
**Namespace:** q02
**Workloads:** httpbin, sleep

## Task

Expose the `httpbin` service externally using **classic Istio Gateway + VirtualService**.

1. Create an Istio `Gateway` that listens on port 80 for host `httpbin.q02.example.com`
2. Create a `VirtualService` bound to the gateway that routes traffic to `httpbin:8000`
3. Verify the routing works

## Verification

```bash
# Check configs are accepted
istioctl analyze -n q02

# Test via the ingress gateway
INGRESS_HOST=$(kubectl -n istio-system get svc istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "localhost")
curl -s -H "Host: httpbin.q02.example.com" http://$INGRESS_HOST/get
```

## Resources to create

- `networking.istio.io/Gateway`
- `networking.istio.io/VirtualService`
