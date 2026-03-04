# Q04 – Traffic Shifting (Weighted Canary)

**Domain:** Traffic Management
**Namespace:** q04
**Workloads:** httpbin-v1, httpbin-v2, sleep

## Task

Implement a canary deployment by shifting traffic gradually between versions.

1. Create a `DestinationRule` for `httpbin` with subsets `v1` and `v2`
2. Create a `VirtualService` that sends **80%** of traffic to `v1` and **20%** to `v2`
3. Verify the approximate distribution
4. Then update the weights to **50/50**

## Verification

```bash
# Run 20 requests and count distribution
for i in $(seq 1 20); do
  kubectl exec -n q04 deploy/sleep -- curl -s httpbin:8000/headers 2>/dev/null
done | grep -c "v2"
# Expect ~4 out of 20 for 80/20, ~10 for 50/50
```

## Resources to create

- `networking.istio.io/DestinationRule`
- `networking.istio.io/VirtualService` (with weighted routes)
