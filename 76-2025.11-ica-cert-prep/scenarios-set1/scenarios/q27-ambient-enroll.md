# Q27 – Enroll Namespace in Ambient Mesh

**Domain:** Installation & Configuration
**Namespace:** q27
**Workloads:** httpbin, sleep (NOT enrolled in mesh)

## Task

Enroll namespace q27 in Istio ambient mode.

1. Verify the workloads are currently NOT part of the mesh
2. Label the namespace for ambient mode
3. Verify ztunnel is now intercepting traffic for these pods
4. Confirm mTLS is active between sleep and httpbin

## Steps

```bash
# 1. Check current state — pods should NOT appear in proxy-status
istioctl proxy-status | grep q27

# 2. Enroll the namespace
kubectl label namespace q27 istio.io/dataplane-mode=ambient

# 3. Pods don't need restart in ambient mode — ztunnel picks them up automatically

# 4. Verify enrollment
istioctl proxy-status | grep q27
kubectl logs -n istio-system ds/ztunnel | grep q27
```

## Verification

```bash
# Traffic should work with L4 mTLS
kubectl exec -n q27 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin:8000/get
# Expected: 200

# Pods should show in ztunnel status
istioctl proxy-status | grep q27
```

## Key difference from sidecar mode

- No pod restart needed
- No sidecar container added
- L4 only (for L7 features, deploy a waypoint proxy — see q29)
