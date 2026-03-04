# Q11 – Traffic Mirroring

**Domain:** Traffic Management
**Namespace:** q11
**Workloads:** httpbin-v1, httpbin-v2, sleep

## Task

Mirror live traffic to a second version for testing without affecting production.

1. Create a `DestinationRule` for `httpbin` with subsets `v1` and `v2`
2. Create a `VirtualService` that:
   - Routes **100% of traffic** to `v1`
   - **Mirrors** traffic to `v2`
3. Verify v1 handles all real requests and v2 receives mirrored copies

## Verification

```bash
# Send a request (response comes from v1)
kubectl exec -n q11 deploy/sleep -- curl -s httpbin:8000/headers

# Check v2 logs — it should show the mirrored request
kubectl logs -n q11 deploy/httpbin-v2 -c httpbin | tail -5

# Send several requests and verify both pods log them
for i in $(seq 1 5); do
  kubectl exec -n q11 deploy/sleep -- curl -s httpbin:8000/get > /dev/null
done
kubectl logs -n q11 deploy/httpbin-v1 -c httpbin --tail=5
kubectl logs -n q11 deploy/httpbin-v2 -c httpbin --tail=5
```

## Resources to create

- `networking.istio.io/DestinationRule`
- `networking.istio.io/VirtualService` (mirror field)
