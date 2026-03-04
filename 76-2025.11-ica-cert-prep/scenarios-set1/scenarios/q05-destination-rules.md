# Q05 – DestinationRule Subsets and Load Balancing

**Domain:** Traffic Management
**Namespace:** q05
**Workloads:** httpbin-v1, httpbin-v2, sleep

## Task

Configure traffic policies using DestinationRule.

1. Create a `DestinationRule` for `httpbin` with:
   - Subset `v1` (version: v1) using `ROUND_ROBIN` load balancing
   - Subset `v2` (version: v2) using `RANDOM` load balancing
   - A connection pool limiting to 10 max connections and 5 HTTP1 connections per host
2. Create a `VirtualService` that routes all traffic to subset `v1`
3. Verify the configuration is applied

## Verification

```bash
# Check proxy config received the destination rule
istioctl proxy-config clusters deploy/sleep -n q05 | grep httpbin

# Verify traffic goes to v1 only
kubectl exec -n q05 deploy/sleep -- curl -s httpbin:8000/headers

# Check config analysis
istioctl analyze -n q05
```

## Resources to create

- `networking.istio.io/DestinationRule` (subsets, trafficPolicy, connectionPool)
- `networking.istio.io/VirtualService`
