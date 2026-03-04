# Q24 – Troubleshoot: Control Plane and Data Plane Diagnostics

**Domain:** Troubleshooting
**Namespace:** q24
**Workloads:** httpbin, sleep

## Task

Practice using Istio's diagnostic tools to inspect control plane and data plane state. This is an open-ended diagnostics exercise.

### Part A – Control Plane

1. Check that istiod is running and healthy
2. Verify all proxies are connected and in sync with the control plane
3. Check for any configuration warnings or errors

### Part B – Data Plane

1. Inspect the proxy configuration for the sleep pod:
   - List all clusters, routes, endpoints, and listeners
2. Verify the proxy version matches istiod
3. Check proxy logs for errors

## Commands to practice

```bash
# Control plane health
kubectl get pods -n istio-system
istioctl proxy-status
istioctl analyze --all-namespaces

# Data plane inspection
istioctl proxy-config clusters deploy/sleep -n q24
istioctl proxy-config routes deploy/sleep -n q24
istioctl proxy-config endpoints deploy/sleep -n q24
istioctl proxy-config listeners deploy/sleep -n q24
istioctl proxy-config log deploy/sleep -n q24

# Debug specific proxy
istioctl dashboard envoy deploy/sleep -n q24

# Check proxy-istiod sync
istioctl proxy-status deploy/sleep.q24

# Describe a pod to see injection/interception details
kubectl describe pod -n q24 -l app=sleep
istioctl experimental describe pod -n q24 $(kubectl get pod -n q24 -l app=sleep -o jsonpath='{.items[0].metadata.name}')
```

## Verification

No single "right answer" — the goal is fluency with these diagnostic commands.
