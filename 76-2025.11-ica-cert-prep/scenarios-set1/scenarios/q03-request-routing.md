# Q03 – Request Routing (Header/Path Based)

**Domain:** Traffic Management
**Namespace:** q03
**Workloads:** httpbin-v1, httpbin-v2, sleep

## Task

Route traffic to different httpbin versions based on request headers.

1. Create a `DestinationRule` for `httpbin` with two subsets: `v1` (version: v1) and `v2` (version: v2)
2. Create a `VirtualService` for `httpbin` that:
   - Routes requests with header `x-version: v2` to subset `v2`
   - Routes all other requests to subset `v1`
3. Verify both routes work

## Verification

```bash
# Should hit v1 (default)
kubectl exec -n q03 deploy/sleep -- curl -s httpbin:8000/headers

# Should hit v2
kubectl exec -n q03 deploy/sleep -- curl -s -H "x-version: v2" httpbin:8000/headers

# Run multiple times to confirm consistency
for i in $(seq 1 5); do
  kubectl exec -n q03 deploy/sleep -- curl -s httpbin:8000/headers | grep -c "v1" || true
done
```

## Resources to create

- `networking.istio.io/DestinationRule`
- `networking.istio.io/VirtualService`
