# q38-kite: Sidecar — Workload-Specific Scope

**Namespace:** `q38-kite`

**Workloads:**
- `client` (curlimages/curl)
- `api-svc` (kong/httpbin, port 8000→80)
- `web` (kong/httpbin, port 8000→80)

## Task

Create a Sidecar with workloadSelector for `app=client` that limits its egress to only `api-svc` (not `web`).

Client should only see api-svc in its service configuration.

**Steps:**
1. Apply a Sidecar named `client-sidecar` with workloadSelector matching app=client.
2. Configure egress hosts: ["./api-svc.q38-kite.svc.cluster.local"]
3. Specify port 8000 for the api-svc egress rule.

## Verification

Check Envoy clusters for client pod:

```bash
istioctl pc clusters deploy/client -n q38-kite | grep -E "api-svc|web"
```

Test connectivity:

```bash
# Should work: curl to api-svc
kubectl exec deploy/client -n q38-kite -- curl -s api-svc:8000/get | head -5

# Should fail: curl to web (not in egress policy)
kubectl exec deploy/client -n q38-kite -- curl -s web:8000/get
```

Expected: api-svc appears in Envoy clusters; web does not. Curl to api-svc succeeds; curl to web fails.

## Resources to Create

- **Sidecar** `client-sidecar` (workloadSelector: app=client): egress hosts ["./api-svc.q38-kite.svc.cluster.local"] on port 8000
