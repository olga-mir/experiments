# Q26 - Grain: ServiceEntry + DestinationRule TLS Origination

## Namespace
`q26-grain`

## Workloads
- `client` (SA: default, curlimages/curl)

## Task

1. Create a ServiceEntry for `httpbin.org`:
   - Ports: 80 (HTTP) and 443 (HTTPS)
   - Resolution: DNS
   - Location: MESH_EXTERNAL

2. Create a DestinationRule for `httpbin.org` that enables TLS origination:
   - Client sends HTTP on port 80 to the sidecar
   - The sidecar upgrades to TLS and connects to httpbin.org port 443

3. This transparent upgrade is invisible to the client.

## Verification

```bash
# From client, curl http://httpbin.org (sidecar does TLS upgrade)
kubectl exec -it client -n q26-grain -- curl http://httpbin.org/get

# Verify DestinationRule has TLS origination configured
kubectl get destinationrule -n q26-grain -o yaml
```

## Resources to Create

- ServiceEntry (hosts: httpbin.org, ports: 80 HTTP + 443 HTTPS, resolution DNS, location MESH_EXTERNAL)
- DestinationRule (host: httpbin.org, portLevelSettings with TLS SIMPLE origination)
