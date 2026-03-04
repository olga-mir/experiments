# Q25 - Flint: ServiceEntry for External HTTP Service

## Namespace
`q25-flint`

## Workloads
- `client` (SA: default, curlimages/curl)

## Task

1. Create a ServiceEntry for `httpbin.org`.

2. Configuration:
   - Port: 80 (HTTP)
   - Resolution: DNS
   - Location: MESH_EXTERNAL

3. This makes the external service explicitly available to mesh clients.

## Verification

```bash
# From client, curl httpbin.org (should work)
kubectl exec -it client -n q25-flint -- curl http://httpbin.org/get

# Verify ServiceEntry was created
kubectl get serviceentry -n q25-flint -o yaml
```

## Resources to Create

- ServiceEntry (hosts: httpbin.org, port 80 HTTP, resolution DNS, location MESH_EXTERNAL)
