# Q27 - Helix: ServiceEntry Onboarding In-Cluster Service

## Namespace
`q27-helix`

## Workloads
- `client` (SA: default, curlimages/curl)
- `echo` (fortio on port 8080, may not have sidecar)

## Task

1. Create a ServiceEntry to register the in-cluster `echo` service in the mesh's service registry.

2. Configuration:
   - Hosts: `echo.q27-helix.svc.cluster.local`
   - Port: 8080 (HTTP)
   - Resolution: STATIC
   - Location: MESH_INTERNAL
   - Endpoint address: ClusterIP of echo service (e.g., 10.96.x.x)

3. This allows mesh clients to reach services that may not have sidecars.

## Verification

```bash
# From client, curl echo on port 8080
kubectl exec -it client -n q27-helix -- curl http://echo:8080/echo

# Verify ServiceEntry
kubectl get serviceentry -n q27-helix -o yaml
```

## Resources to Create

- ServiceEntry (hosts: echo.q27-helix.svc.cluster.local, port 8080 HTTP, resolution STATIC, location MESH_INTERNAL, endpoint address from echo service ClusterIP)
