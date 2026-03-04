# Q30 – Canary Upgrade with Revision Labels

**Domain:** Installation & Configuration
**Namespace:** q30
**Workloads:** httpbin, sleep

## Task

Practice the Istio canary upgrade workflow using revision labels.

1. Understand the current Istio revision installed
2. Know how revision labels work for gradual migration
3. Relabel namespace q30 to use a specific revision
4. Verify workloads connect to the correct control plane revision

## Steps

```bash
# 1. Check current Istio revision
istioctl version
kubectl get pods -n istio-system -l app=istiod --show-labels

# 2. List installed revisions
kubectl get mutatingwebhookconfigurations | grep istio

# 3. Check current namespace label
kubectl get ns q30 --show-labels

# 4. For sidecar mode — label with a revision instead of istio-injection=enabled
#    kubectl label namespace q30 istio-injection- istio.io/rev=<new-revision>
#    kubectl rollout restart deployment -n q30

# 5. For ambient mode — no pod restart needed, just relabel
#    kubectl label namespace q30 istio.io/rev=<new-revision> --overwrite
```

## Canary upgrade workflow summary

```
1. Install new Istio version with a revision tag:
   istioctl install --set revision=1-27-0

2. Both old and new istiod run side by side

3. Migrate namespaces one at a time:
   kubectl label namespace <ns> istio.io/rev=1-27-0 --overwrite
   kubectl rollout restart deployment -n <ns>   # sidecar mode only

4. Verify workloads use the new revision:
   istioctl proxy-status

5. When all namespaces are migrated, remove the old revision:
   istioctl uninstall --revision <old-revision>
```

## Verification

```bash
# Check which revision the proxies in q30 are connected to
istioctl proxy-status | grep q30

# Should show the revision in the ISTIOD column
```

## Key points

- Canary upgrades allow zero-downtime Istio version migration
- Old and new control planes run simultaneously
- Namespaces are migrated individually by changing the revision label
- In-place upgrades (`istioctl upgrade`) are simpler but riskier
