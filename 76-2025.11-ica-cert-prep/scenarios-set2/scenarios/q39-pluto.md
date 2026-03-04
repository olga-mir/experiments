# q39-pluto: Sidecar — Namespace-Wide exportTo Restriction

**Namespace:** `q39-pluto`

**Workloads:**
- `caller` (curlimages/curl)
- `portal` (kong/httpbin, port 8000→80)
- `store` (kong/httpbin, port 8000→80)

## Task

Create a Sidecar (no workloadSelector = namespace-wide) with egress hosts:
- "./*" (all services in the current namespace)
- "istio-system/*" (Istio control plane)

This restricts all workloads in q39-pluto to only see services in their own namespace and istio-system.

**Steps:**
1. Apply a Sidecar named `namespace-sidecar` with no workloadSelector (applies to all pods in namespace).
2. Configure egress hosts: ["./*", "istio-system/*"]
3. Omit workloadSelector to make it namespace-wide.

## Verification

Check Envoy clusters for caller pod — should only show q39-pluto services:

```bash
istioctl pc clusters deploy/caller -n q39-pluto | grep "outbound"
```

Test connectivity to in-namespace services:

```bash
# Should work: curl to services in q39-pluto
kubectl exec deploy/caller -n q39-pluto -- curl -s portal:8000/get | head -5
kubectl exec deploy/caller -n q39-pluto -- curl -s store:8000/get | head -5
```

Expected: Only q39-pluto and istio-system services appear in Envoy config. Curls to in-namespace services succeed.

## Resources to Create

- **Sidecar** (namespace-wide, no workloadSelector): egress hosts ["./*", "istio-system/*"]
