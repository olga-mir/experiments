# Q06 – Timeouts and Retries

**Domain:** Traffic Management
**Namespace:** q06
**Workloads:** httpbin, sleep

## Task

Configure timeout and retry policies for httpbin.

1. Create a `VirtualService` for `httpbin` that:
   - Sets a **3 second timeout** on all requests
   - Configures **3 retry attempts** on `5xx` errors with a **2 second per-try timeout**
2. Test the timeout by requesting httpbin's `/delay/5` endpoint (should timeout)
3. Test normal requests still work via `/get`

## Verification

```bash
# This should succeed (fast response)
kubectl exec -n q06 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin:8000/get
# Expected: 200

# This should timeout (5s delay > 3s timeout)
kubectl exec -n q06 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin:8000/delay/5
# Expected: 504

# This should succeed (2s delay < 3s timeout)
kubectl exec -n q06 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin:8000/delay/2
# Expected: 200
```

## Resources to create

- `networking.istio.io/VirtualService` (timeout, retries)
