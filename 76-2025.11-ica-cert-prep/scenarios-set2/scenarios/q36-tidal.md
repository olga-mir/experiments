# q36-tidal: Sidecar — Limit Egress to Specific Services

**Namespace:** `q36-tidal`

**Workloads:**
- `client` (curlimages/curl)
- `my-app` (kong/httpbin, port 8000→80)

## Task

Create a Sidecar resource (namespace-wide, no workloadSelector) that limits egress to only:
- `my-app.q36-tidal.svc.cluster.local` on port 8000
- `istio-system/*` (for Istio control plane communication)

**Steps:**
1. Apply a Sidecar named `default` (or `namespace-sidecar`) with no workloadSelector (namespace-wide scope).
2. Configure egress hosts: ["./my-app.q36-tidal.svc.cluster.local", "istio-system/*"]
3. Specify port 8000 for the my-app egress rule.

## Verification

Test egress restrictions:

```bash
# Should work: curl to my-app
kubectl exec deploy/client -n q36-tidal -- curl -s my-app:8000/get | head -5

# Should fail: attempt to reach other namespaces (if tested)
kubectl exec deploy/client -n q36-tidal -- curl -v other-service.other-ns:8000/get
```

Expected: Curl to my-app succeeds (200); requests to services outside the egress policy fail.

## Resources to Create

- **Sidecar** (namespace-wide): egress hosts ["./my-app.q36-tidal.svc.cluster.local", "istio-system/*"] on port 8000
