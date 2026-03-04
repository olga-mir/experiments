# Q20 – Troubleshoot: Missing Mesh Enrollment

**Domain:** Troubleshooting
**Namespace:** q20
**Workloads:** httpbin, sleep (NOT enrolled in mesh)

## Situation

The httpbin and sleep pods are deployed but traffic is not being managed by the Istio mesh. There are no sidecars injected (sidecar mode) or ztunnel interception (ambient mode). mTLS is not being applied, and Istio traffic policies have no effect.

## Task

1. Diagnose why the workloads are not part of the mesh
2. Fix the issue so that traffic between sleep and httpbin goes through the mesh
3. Verify mTLS is active between the pods

## Hints

```bash
# Check namespace labels
kubectl get ns q20 --show-labels

# Check if pods have sidecars or are intercepted by ztunnel
kubectl get pods -n q20 -o wide
istioctl proxy-status | grep q20

# In ambient mode, check ztunnel logs
kubectl logs -n istio-system ds/ztunnel | grep q20
```

## Verification

```bash
# After fix, pods should appear in proxy-status
istioctl proxy-status | grep q20

# Traffic should work with mTLS
kubectl exec -n q20 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin:8000/get
# Expected: 200
```
