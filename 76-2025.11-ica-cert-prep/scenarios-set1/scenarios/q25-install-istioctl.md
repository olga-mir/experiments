# Q25 – Install/Configure Istio with istioctl

**Domain:** Installation & Configuration
**Namespace:** q25
**Workloads:** httpbin, sleep

## Task

Practice installing and configuring Istio using `istioctl`.

1. List available Istio profiles: `istioctl profile list`
2. Dump the `default` profile configuration: `istioctl profile dump default`
3. Compare two profiles: `istioctl profile diff default demo`
4. Generate a manifest without applying: `istioctl manifest generate --set profile=default`
5. Verify the current installation: `istioctl verify-install`

### Bonus

Create an `IstioOperator` resource that customizes the installation:
- Set the mesh outbound traffic policy to `REGISTRY_ONLY`
- Enable access logging
- Set the proxy concurrency to 2

```yaml
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: custom-install
spec:
  meshConfig:
    outboundTrafficPolicy:
      mode: REGISTRY_ONLY
    accessLogFile: /dev/stdout
    defaultConfig:
      concurrency: 2
```

## Verification

```bash
# Check current install
istioctl verify-install

# Check mesh config
kubectl get configmap istio -n istio-system -o jsonpath='{.data.mesh}' | grep -E "outbound|accessLog"

# Verify workloads still function
kubectl exec -n q25 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin:8000/get
```

## Key commands to memorize

```bash
istioctl install --set profile=<name>
istioctl install -f <operator-file>.yaml
istioctl profile list
istioctl profile dump <profile>
istioctl profile diff <p1> <p2>
istioctl manifest generate
istioctl verify-install
istioctl uninstall --purge
```
