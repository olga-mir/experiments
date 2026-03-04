# q16-umbra: PeerAuthentication Port-Level Override

**Namespace**: q16-umbra

## Workloads
- `tester` (curlimages/curl) - initiates requests
- `api-svc` (kong/httpbin) - service on port 8000 (container port 8000)

## Task
1. Create a PeerAuthentication that:
   - Sets namespace-wide mTLS mode to STRICT
   - Adds a port-level override for port 80 (or 8000 if that's the container port) to PERMISSIVE
   - The override allows non-mTLS traffic on that specific port while enforcing mTLS elsewhere
2. Apply the configuration
3. Verify the port-level override is in place

## Verification
```bash
# Check PeerAuthentication with port-level config
kubectl describe pa -n q16-umbra

# View YAML
kubectl get peerauthenctication -n q16-umbra -o yaml

# Check pod description to see mTLS mode and port exceptions
istioctl x describe pod <api-svc-pod> -n q16-umbra
```

## Resources to Create
- **PeerAuthentication** with:
  - `spec.mtls.mode: STRICT` (namespace-wide)
  - `spec.portLevelMtls` entry for port 8000 (or 80): `mode: PERMISSIVE`
