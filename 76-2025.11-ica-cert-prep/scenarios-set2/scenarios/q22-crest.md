# Q22 - Crest: mTLS Migration PERMISSIVE → STRICT

## Namespace
`q22-crest`

## Workloads
- `probe` (SA: default, curlimages/curl)
- `my-app` (SA: my-app, kong/httpbin:latest)

## Task

1. A PeerAuthentication with PERMISSIVE mode already exists in the namespace.

2. Migrate from PERMISSIVE to STRICT mode on the PeerAuthentication resource.

3. Both workloads are already in the mesh (sidecars injected). Verify traffic still works after migration.

## Verification

```bash
# Update PeerAuthentication mode to STRICT
kubectl patch peerauthentication -n q22-crest <name> --type merge -p '{"spec":{"mtls":{"mode":"STRICT"}}}'

# Test traffic (should still work since both sidecars are in the mesh)
kubectl exec -it probe -n q22-crest -- curl http://my-app:8000/get

# Confirm with istioctl
istioctl x describe -n q22-crest pod probe
```

## Resources to Create

- Update existing PeerAuthentication mode to STRICT
- No new resources needed
