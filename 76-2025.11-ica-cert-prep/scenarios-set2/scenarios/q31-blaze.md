# q31-blaze: Fault Injection — HTTP Abort

**Namespace:** `q31-blaze`

**Workloads:**
- `client` (curlimages/curl)
- `my-app` (kong/httpbin, port 8000→80)

## Task

Create a VirtualService for `my-app` that injects an HTTP abort fault returning 503 for 50% of requests.

**Steps:**
1. Apply a VirtualService named `my-app` with fault injection: abort with httpStatus 503 and percentage 50.
2. Route traffic to the `my-app` destination (port 8000).

## Verification

Run 10 curls from client pod to my-app:8000/get. Roughly half should return 503.

```bash
kubectl exec deploy/client -n q31-blaze -- bash -c 'for i in $(seq 1 10); do curl -s -o /dev/null -w "%{http_code}\n" my-app:8000/get; done'
```

Expected: Mix of 200 and 503 status codes (approximately 50/50).

## Resources to Create

- **VirtualService** `my-app`: fault injection with abort (httpStatus: 503, percentage: 50)
