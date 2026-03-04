# Q22 – Troubleshoot: DestinationRule Subset Mismatch

**Domain:** Troubleshooting
**Namespace:** q22
**Workloads:** httpbin (version: v1), sleep
**Pre-deployed bug:** DestinationRule with wrong subset label + VirtualService referencing that subset

## Situation

A VirtualService routes traffic to httpbin using a DestinationRule subset named `v1`. However, all requests return 503 (no healthy upstream). The httpbin pods are running and healthy.

## Task

1. Identify the mismatch between the DestinationRule subset label and the actual pod labels
2. Fix the DestinationRule so the subset selector matches the real pod labels
3. Verify traffic flows correctly

## Hints

```bash
# Check pod labels
kubectl get pods -n q22 --show-labels

# Check the DestinationRule subset selector
kubectl get dr -n q22 -o yaml

# Check what istioctl says
istioctl analyze -n q22

# Check proxy config for the endpoint
istioctl proxy-config endpoints deploy/sleep -n q22 | grep httpbin
```

## Verification

```bash
# After fix — requests should succeed
kubectl exec -n q22 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin:8000/get
# Expected: 200
```
