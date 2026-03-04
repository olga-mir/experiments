# Q28 – Enable Sidecar Injection

**Domain:** Installation & Configuration
**Namespace:** q28
**Workloads:** httpbin, sleep (NOT injected)

## Task

Enable Istio sidecar injection for namespace q28.

1. Verify pods currently have NO sidecar (1/1 containers, not 2/2)
2. Label the namespace for automatic sidecar injection
3. Restart the pods to trigger injection
4. Verify sidecars are running

## Steps

```bash
# 1. Check current state — pods should be 1/1
kubectl get pods -n q28

# 2. Label namespace
kubectl label namespace q28 istio-injection=enabled

# 3. Restart pods to trigger injection
kubectl rollout restart deployment -n q28

# 4. Wait and verify — pods should now be 2/2
kubectl get pods -n q28
```

## Verification

```bash
# Pods should be 2/2 (app container + istio-proxy)
kubectl get pods -n q28
# Expected: 2/2 Running

# Should appear in proxy-status
istioctl proxy-status | grep q28

# Traffic should work
kubectl exec -n q28 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin:8000/get
# Expected: 200
```

## Key points

- Sidecar injection requires the `istio-injection=enabled` label on the namespace
- Existing pods must be **restarted** for injection to take effect
- You can override per-pod with annotation `sidecar.istio.io/inject: "true"` or `"false"`
- If using revisions: `istio.io/rev=<revision>` instead of `istio-injection=enabled`
