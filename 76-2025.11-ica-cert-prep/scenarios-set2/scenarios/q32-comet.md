# q32-comet: Fault Injection — Delay

**Namespace:** `q32-comet`

**Workloads:**
- `tester` (curlimages/curl)
- `backend` (kong/httpbin, port 8000→80)

## Task

Create a VirtualService for `backend` that injects a 5-second delay for 100% of requests.

**Steps:**
1. Apply a VirtualService named `backend` with fault injection: delay of 5s (5000ms) at percentage 100.
2. Route traffic to the `backend` destination (port 8000).

## Verification

Time a curl from tester pod to backend:8000/get — should take approximately 5 seconds.

```bash
kubectl exec deploy/tester -n q32-comet -- sh -c "time curl -s backend:8000/get > /dev/null"
```

Expected: Real time ~5 seconds (plus network overhead).

## Resources to Create

- **VirtualService** `backend`: fault injection with delay (fixedDelay: 5s, percentage: 100)
