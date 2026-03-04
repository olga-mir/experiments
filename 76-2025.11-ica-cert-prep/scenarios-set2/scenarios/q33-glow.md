# q33-glow: Retries with retryOn Conditions

**Namespace:** `q33-glow`

**Workloads:**
- `client` (curlimages/curl)
- `api-svc` (kong/httpbin, port 8000→80)

## Task

Create a VirtualService for `api-svc` with retry configuration:
- attempts: 3
- perTryTimeout: 2s
- retryOn: "5xx,connect-failure,refused-stream"

**Steps:**
1. Apply a VirtualService named `api-svc` with retries configured as specified.
2. Route traffic to the `api-svc` destination (port 8000).

## Verification

Check the VirtualService configuration and confirm retry settings are applied.

```bash
kubectl get vs -n q33-glow -o yaml | grep -A 10 "retries:"
```

Verify connectivity works:

```bash
kubectl exec deploy/client -n q33-glow -- curl -s api-svc:8000/get | head -20
```

Expected: VirtualService shows retry config; curl returns 200 OK.

## Resources to Create

- **VirtualService** `api-svc`: retries (attempts: 3, perTryTimeout: 2s, retryOn: "5xx,connect-failure,refused-stream")
