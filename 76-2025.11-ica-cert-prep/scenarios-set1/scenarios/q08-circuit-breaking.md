# Q08 – Circuit Breaking and Outlier Detection

**Domain:** Traffic Management
**Namespace:** q08
**Workloads:** httpbin, sleep, fortio

## Task

Configure circuit breaking to protect httpbin from overload.

1. Create a `DestinationRule` for `httpbin` with:
   - **Connection pool**: max 1 HTTP connection, max 1 pending request
   - **Outlier detection**: consecutive 5xx errors = 1, eject for 30s, scan every 10s
2. Use fortio to generate concurrent load and trigger the circuit breaker

## Verification

```bash
# First verify normal single request works
kubectl exec -n q08 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin:8000/get

# Generate load with fortio: 2 concurrent connections, 20 requests
kubectl exec -n q08 deploy/fortio -- fortio load -c 2 -qps 0 -n 20 -loglevel Warning http://httpbin:8000/get
# Look for non-200 responses — these are circuit breaker tripping (503s)

# Increase concurrency to see more tripping
kubectl exec -n q08 deploy/fortio -- fortio load -c 5 -qps 0 -n 50 -loglevel Warning http://httpbin:8000/get

# Check upstream_rq_pending_overflow in proxy stats
kubectl exec -n q08 deploy/fortio -c istio-proxy -- pilot-agent request GET stats | grep httpbin | grep pending
```

## Resources to create

- `networking.istio.io/DestinationRule` (connectionPool, outlierDetection)
