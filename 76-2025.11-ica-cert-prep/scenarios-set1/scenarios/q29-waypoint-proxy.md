# Q29 – Deploy Waypoint Proxy (Ambient L7)

**Domain:** Installation & Configuration
**Namespace:** q29
**Workloads:** httpbin, sleep

## Task

Deploy a waypoint proxy to enable L7 traffic management in ambient mode.

1. Ensure namespace q29 is enrolled in ambient mesh (label it if not)
2. Deploy a waypoint proxy for the namespace
3. Create an L7 policy (e.g., AuthorizationPolicy checking HTTP methods) to verify the waypoint works
4. Verify L7 features are functional

## Steps

```bash
# 1. Enroll in ambient (if not already)
kubectl label namespace q29 istio.io/dataplane-mode=ambient --overwrite

# 2. Deploy a waypoint proxy
istioctl waypoint apply -n q29 --enroll-namespace

# Or manually with Gateway API:
# kubectl apply -n q29 -f - <<EOF
# apiVersion: gateway.networking.k8s.io/v1
# kind: Gateway
# metadata:
#   name: waypoint
#   labels:
#     istio.io/waypoint-for: service
# spec:
#   gatewayClassName: istio-waypoint
#   listeners:
#   - name: mesh
#     protocol: HBONE
#     port: 15008
# EOF

# 3. Verify waypoint is running
kubectl get gateway -n q29
kubectl get pods -n q29 -l gateway.networking.k8s.io/gateway-name=waypoint
```

## Verification

```bash
# Create a test L7 policy
kubectl apply -n q29 -f - <<EOF
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: allow-get-only
spec:
  targetRefs:
  - kind: Service
    group: ""
    name: httpbin
  action: ALLOW
  rules:
  - to:
    - operation:
        methods: ["GET"]
EOF

# GET should work
kubectl exec -n q29 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" httpbin:8000/get
# Expected: 200

# POST should be denied
kubectl exec -n q29 deploy/sleep -- curl -s -o /dev/null -w "%{http_code}" -X POST httpbin:8000/post
# Expected: 403
```

## Key points

- Without a waypoint, ambient mode only provides L4 (mTLS, L4 AuthzPolicy)
- Waypoint proxies add L7 capabilities: HTTP routing, L7 AuthzPolicy, JWT, fault injection
- Waypoints are deployed per-namespace or per-service-account
