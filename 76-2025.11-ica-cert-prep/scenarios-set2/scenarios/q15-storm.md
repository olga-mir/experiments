# q15-storm: PeerAuthentication STRICT mTLS

**Namespace**: q15-storm

## Workloads
- `client` (curlimages/curl) - initiates requests
- `backend` (kong/httpbin) - service on port 8000

## Task
1. Create a namespace-wide PeerAuthentication in q15-storm that enforces STRICT mTLS
   - This applies to all workloads in the namespace
   - STRICT means both sides must use mTLS
2. Verify that traffic between client and backend continues to work
3. Confirm mTLS is active using istioctl

## Verification
```bash
# Test traffic still works (both pods are in mesh with sidecar injection)
kubectl exec -it <client-pod> -n q15-storm -- curl backend:8000/get

# Verify PeerAuthentication is applied
kubectl get peerauthenctication -n q15-storm -o yaml

# Check mTLS status on backend pod
istioctl x describe pod <backend-pod> -n q15-storm

# Look for: "MTLS: Strict"
```

## Resources to Create
- **PeerAuthentication** named `default` (or any name) with:
  - No selector (applies to all workloads in namespace)
  - `spec.mtls.mode: STRICT`
