# Q07 – Fault Injection

**Domain:** Traffic Management
**Namespace:** q07
**Workloads:** httpbin, sleep

## Task

Inject faults to test service resilience.

1. Create a `VirtualService` for `httpbin` that injects:
   - A **3 second delay** on **50%** of requests to `/delay/*`
   - An **HTTP 503 abort** on **100%** of requests to `/status/200`
2. Verify both fault types are working

## Verification

```bash
# Test delay injection (should take ~3s for ~50% of requests)
time kubectl exec -n q07 deploy/sleep -- curl -s -o /dev/null httpbin:8000/delay/0
# Run several times — about half should be slow

# Test abort injection (should return 503 instead of 200)
kubectl exec -n q07 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin:8000/status/200
# Expected: 503

# Normal endpoints should still work
kubectl exec -n q07 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin:8000/get
# Expected: 200
```

## Resources to create

- `networking.istio.io/VirtualService` (fault.delay, fault.abort)
