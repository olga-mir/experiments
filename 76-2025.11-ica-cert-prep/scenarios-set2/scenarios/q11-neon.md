# q11-neon: DestinationRule Connection Pool Settings

**Namespace**: q11-neon

## Workloads
- `client` (curlimages/curl) - initiates requests
- `my-app` (kong/httpbin) - backend service on port 8000

## Task
1. Create a DestinationRule for `my-app` service that configures connection pool limits:
   - TCP connections: max 10
   - HTTP/1.x max pending requests: 5
   - HTTP/2 max requests: 10
2. Apply the DestinationRule
3. Verify the configuration is in place

## Verification
```bash
# Check the DestinationRule configuration
kubectl get dr -n q11-neon -o yaml

# Describe the DestinationRule to inspect connectionPool fields
kubectl describe dr my-app -n q11-neon
```

## Resources to Create
- **DestinationRule** named `my-app` for service `my-app.q11-neon.svc.cluster.local`
  - `connectionPool.tcp.maxConnections: 10`
  - `connectionPool.http.http1MaxPendingRequests: 5`
  - `connectionPool.http.http2MaxRequests: 10`
