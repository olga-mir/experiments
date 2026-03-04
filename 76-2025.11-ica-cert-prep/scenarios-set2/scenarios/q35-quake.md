# q35-quake: Circuit Breaking + Outlier Detection

**Namespace:** `q35-quake`

**Workloads:**
- `client` (curlimages/curl)
- `store` (kong/httpbin, port 8000→80)
- `fortio` (fortio/fortio, load generator on port 8080)

## Task

Create a DestinationRule for `store` with:
1. Circuit breaking: maxConnections 1, http1MaxPendingRequests 1, http2MaxRequests 1
2. Outlier detection: consecutive5xxErrors 3, interval 10s, baseEjectionTime 30s

Use fortio to generate concurrent load and trigger the circuit breaker.

**Steps:**
1. Apply a DestinationRule named `store` with circuit breaking and outlier detection configured.
2. Optionally create a VirtualService for `store` (required for some scenarios) pointing to the destination.
3. Use fortio from the fortio pod to generate load.

## Verification

Run fortio load test with 3 concurrent connections and 20 requests. Observe circuit breaker behavior.

```bash
kubectl exec deploy/fortio -n q35-quake -- fortio load -c 3 -qps 0 -n 20 http://store:8000/get
```

Expected: Some requests should fail with 503 (circuit broken) due to maxConnections=1 being exceeded.

## Resources to Create

- **DestinationRule** `store`: circuit breaking (maxConnections: 1, http1MaxPendingRequests: 1, http2MaxRequests: 1) + outlierDetection (consecutive5xxErrors: 3, interval: 10s, baseEjectionTime: 30s)
- **VirtualService** `store` (if needed): simple route to store destination
