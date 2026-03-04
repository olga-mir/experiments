# Q19 – Troubleshoot: Broken VirtualService

**Domain:** Troubleshooting
**Namespace:** q19
**Workloads:** httpbin, sleep
**Pre-deployed bug:** A VirtualService with an incorrect host reference

## Situation

A developer created a VirtualService to route traffic to httpbin, but requests are not being routed correctly. Traffic from sleep to httpbin works via the Service directly, but the VirtualService routing rules are not being applied.

## Task

1. Identify the misconfiguration in the VirtualService
2. Fix it so the VirtualService correctly routes to `httpbin` on port 8000
3. Verify the fix

## Hints

```bash
# Analyze the namespace for issues
istioctl analyze -n q19

# Look at the VirtualService
kubectl get vs -n q19 -o yaml

# Compare the VS host with actual services
kubectl get svc -n q19
```

## Verification

```bash
# After fix — traffic should flow correctly
kubectl exec -n q19 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin:8000/get
# Expected: 200

# istioctl analyze should report no issues
istioctl analyze -n q19
```
