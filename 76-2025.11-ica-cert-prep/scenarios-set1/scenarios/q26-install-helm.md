# Q26 – Install/Configure Istio with Helm

**Domain:** Installation & Configuration
**Namespace:** q26
**Workloads:** httpbin, sleep

## Task

Practice Istio's Helm-based installation workflow.

1. Know the four Helm charts and their install order:
   - `istio/base` – CRDs and cluster-wide resources
   - `istio/istiod` – control plane (Istiod)
   - `istio/cni` – CNI plugin (optional, required for ambient)
   - `istio/ztunnel` – ztunnel DaemonSet (ambient mode)
   - `istio/gateway` – ingress/egress gateways

2. Practice inspecting Helm values:
   ```bash
   helm repo add istio https://istio-release.storage.googleapis.com/charts
   helm show values istio/istiod
   helm show values istio/base
   ```

3. Practice customizing values:
   - Enable access logging
   - Change the default proxy resource limits
   - Set the trust domain

## Key Helm commands

```bash
# Install sequence
helm install istio-base istio/base -n istio-system --create-namespace
helm install istiod istio/istiod -n istio-system --wait
helm install istio-cni istio/cni -n istio-system --wait        # ambient
helm install ztunnel istio/ztunnel -n istio-system --wait       # ambient
helm install istio-ingress istio/gateway -n istio-ingress --create-namespace

# Check what's installed
helm list -n istio-system

# Inspect current values
helm get values istiod -n istio-system

# Upgrade with new values
helm upgrade istiod istio/istiod -n istio-system -f custom-values.yaml

# Uninstall (reverse order)
helm uninstall istio-ingress -n istio-ingress
helm uninstall ztunnel -n istio-system
helm uninstall istio-cni -n istio-system
helm uninstall istiod -n istio-system
helm uninstall istio-base -n istio-system
```

## Verification

```bash
helm list -n istio-system
kubectl get pods -n istio-system
kubectl exec -n q26 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin:8000/get
```
