# Q01 – Gateway API Ingress

**Domain:** Traffic Management
**Namespace:** q01
**Workloads:** httpbin, sleep

## Task

Expose the `httpbin` service externally using the **Kubernetes Gateway API**.

1. Create a `Gateway` resource (gatewayClassName: `istio`) listening on port 80
2. Create an `HTTPRoute` that routes traffic from the Gateway to `httpbin` on port 8000
3. Verify you can reach httpbin through the gateway

## Verification

```bash
# Get the gateway address
kubectl get gateway -n q01

# Test from inside the cluster
kubectl exec -n q01 deploy/sleep -- curl -s httpbin:8000/get

# Test via the gateway (adjust IP/port from gateway status)
kubectl exec -n q01 deploy/sleep -- curl -s -H "Host: httpbin.q01.example.com" <GATEWAY_IP>/get
```

## Resources to create

- `gateway.networking.k8s.io/Gateway`
- `gateway.networking.k8s.io/HTTPRoute`
