# Q28 - Ionic: Egress Control — ServiceEntry + VS Routing

## Namespace
`q28-ionic`

## Workloads
- `client` (SA: default, curlimages/curl)

## Task

1. Create a ServiceEntry for `edition.cnn.com`:
   - Ports: 80 (HTTP) and 443 (HTTPS)
   - Resolution: DNS
   - Location: MESH_EXTERNAL

2. Create a VirtualService for `edition.cnn.com` that adds a 3-second timeout for all requests.

3. This allows controlled egress to the external service with traffic policies.

## Verification

```bash
# From client, curl edition.cnn.com (timeout applies)
kubectl exec -it client -n q28-ionic -- curl -I http://edition.cnn.com

# Verify VirtualService has timeout configured
kubectl get virtualservice -n q28-ionic -o yaml
```

## Resources to Create

- ServiceEntry (hosts: edition.cnn.com, ports: 80 HTTP + 443 HTTPS, resolution DNS, location MESH_EXTERNAL)
- VirtualService (host: edition.cnn.com, timeout: 3s)
