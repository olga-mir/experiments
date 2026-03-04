# ICA Exam Practice

30 namespaces (q01–q30) each with pre-deployed workloads.
Run `./setup.sh` to create everything, `./setup.sh --delete` to tear down.

## Namespace Overview

| NS | Domain | Scenario | Workloads |
|----|--------|----------|-----------|
| **q01** | traffic | Gateway API ingress (Gateway + HTTPRoute) | httpbin, sleep |
| **q02** | traffic | Classic Istio ingress (Gateway + VirtualService) | httpbin, sleep |
| **q03** | traffic | Request routing – header and path based | httpbin-v1, httpbin-v2, sleep |
| **q04** | traffic | Traffic shifting – weighted canary | httpbin-v1, httpbin-v2, sleep |
| **q05** | traffic | DestinationRule subsets + load balancing | httpbin-v1, httpbin-v2, sleep |
| **q06** | traffic | Timeouts and retries | httpbin, sleep |
| **q07** | traffic | Fault injection (delay + abort) | httpbin, sleep |
| **q08** | traffic | Circuit breaking + outlier detection | httpbin, sleep, fortio |
| **q09** | traffic | ServiceEntry – reach external services | sleep only |
| **q10** | traffic | Egress gateway control | httpbin, sleep |
| **q11** | traffic | Traffic mirroring | httpbin-v1, httpbin-v2, sleep |
| **q12** | security | Strict mTLS – PeerAuthentication | httpbin, sleep |
| **q13** | security | mTLS migration (PERMISSIVE → STRICT) | httpbin, sleep |
| **q14** | security | AuthorizationPolicy – ALLOW rules | httpbin, sleep |
| **q15** | security | AuthorizationPolicy – DENY rules | httpbin, sleep |
| **q16** | security | L7 AuthorizationPolicy (path + method + header) | httpbin, sleep |
| **q17** | security | JWT authentication (RequestAuthentication) | httpbin, sleep |
| **q18** | security | TLS termination at ingress gateway | httpbin, sleep |
| **q19** | troubleshoot | Fix broken VirtualService (wrong host) | httpbin, sleep + broken VS |
| **q20** | troubleshoot | Fix missing mesh enrollment | httpbin, sleep (no mesh label) |
| **q21** | troubleshoot | Fix overly restrictive AuthorizationPolicy | httpbin, sleep + deny-all policy |
| **q22** | troubleshoot | Fix DestinationRule subset mismatch | httpbin, sleep + broken DR+VS |
| **q23** | troubleshoot | Fix TLS mode mismatch (DR vs PeerAuth) | httpbin, sleep + conflicting DR+PA |
| **q24** | troubleshoot | Diagnose control plane and data plane issues | httpbin, sleep |
| **q25** | install | Install/configure Istio with istioctl | httpbin, sleep |
| **q26** | install | Install/configure Istio with Helm | httpbin, sleep |
| **q27** | install | Enroll namespace in ambient mesh | httpbin, sleep (not enrolled) |
| **q28** | install | Enable sidecar injection for namespace | httpbin, sleep (not injected) |
| **q29** | install | Deploy waypoint proxy for L7 in ambient | httpbin, sleep |
| **q30** | install | Canary upgrade with revision labels | httpbin, sleep |

## Curriculum Coverage

- **Traffic Management (35%)** → q01–q11 (11 scenarios)
- **Securing Workloads (25%)** → q12–q18 (7 scenarios)
- **Troubleshooting (20%)** → q19–q24 (6 scenarios)
- **Installation & Configuration (20%)** → q25–q30 (6 scenarios)

## Istio Resource Types Covered

| API Group | Resources |
|-----------|-----------|
| networking.istio.io | VirtualService, DestinationRule, Gateway, ServiceEntry, Sidecar |
| gateway.networking.k8s.io | Gateway, HTTPRoute |
| security.istio.io | PeerAuthentication, RequestAuthentication, AuthorizationPolicy |
| telemetry.istio.io | Telemetry |
| install.istio.io | IstioOperator |

## Quick Commands

```bash
# test connectivity in any namespace
kubectl exec -n q<NN> deploy/sleep -- curl -s httpbin:8000/get

# check what's deployed
kubectl get all -n q<NN>

# list all exam namespaces
kubectl get ns -l exam-domain

# check Istio configs in a namespace
kubectl get virtualservices,destinationrules,authorizationpolicies,peerauthentications -n q<NN>
```
