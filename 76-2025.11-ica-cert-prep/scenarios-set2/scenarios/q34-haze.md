# q34-haze: Timeout Configuration

**Namespace:** `q34-haze`

**Workloads:**
- `caller` (curlimages/curl)
- `web` (kong/httpbin, port 8000→80)

## Task

Create a VirtualService for `web` with:
1. A 3-second timeout
2. Fault injection: 5-second delay at 100% percentage

The timeout should trigger before the delay completes, returning a 504 Gateway Timeout.

**Steps:**
1. Apply a VirtualService named `web` with timeout 3s.
2. Configure fault injection with fixedDelay 5s at 100%.
3. Route traffic to the `web` destination (port 8000).

## Verification

Curl web:8000/get from caller pod — should return 504 Gateway Timeout before the 5-second delay completes.

```bash
kubectl exec deploy/caller -n q34-haze -- curl -v web:8000/get
```

Expected: HTTP 504 response with timeout message, actual response time ~3 seconds.

## Resources to Create

- **VirtualService** `web`: timeout (3s) + fault injection delay (5s, 100%)
