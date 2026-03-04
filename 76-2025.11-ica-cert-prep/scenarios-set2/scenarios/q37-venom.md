# q37-venom: Sidecar — Ingress Listener Configuration

**Namespace:** `q37-venom`

**Workloads:**
- `tester` (curlimages/curl)
- `backend` (kong/httpbin, port 8000→80)

## Task

Create a Sidecar with workloadSelector matching `app=backend` that configures an ingress listener:
- Port: 8000
- Protocol: HTTP
- DefaultEndpoint: 127.0.0.1:80

**Steps:**
1. Apply a Sidecar named `backend-sidecar` with workloadSelector for app=backend.
2. Configure ingress listener: port 8000, protocol HTTP, defaultEndpoint 127.0.0.1:80.
3. This explicitly declares the port mapping for incoming traffic.

## Verification

Verify tester can curl backend:8000/get (should still work):

```bash
kubectl exec deploy/tester -n q37-venom -- curl -s backend:8000/get | head -20
```

Check the Sidecar resource is applied to the backend pod:

```bash
kubectl get sidecar -n q37-venom
kubectl get sidecar backend-sidecar -n q37-venom -o yaml
```

Expected: Curl succeeds (200 OK); Sidecar shows ingress listener config.

## Resources to Create

- **Sidecar** `backend-sidecar` (workloadSelector: app=backend): ingress listener (port: 8000, protocol: HTTP, defaultEndpoint: 127.0.0.1:80)
