# q12-opal: Gateway with Multiple Hosts

**Namespace**: q12-opal

## Workloads
- `caller` (curlimages/curl) - initiates requests
- `web` (kong/httpbin) - backend service on port 8000
- `api-svc` (kong/httpbin) - second backend service on port 8000

## Task
1. Create ONE Gateway named `my-gateway` that accepts traffic for both `web.example.com` and `api.example.com` on port 80
2. Create a VirtualService for `web.example.com` that routes traffic to `web:8000`
3. Create a VirtualService for `api.example.com` that routes traffic to `api-svc:8000`

## Verification
```bash
# Test web host routing
curl -H "Host: web.example.com" http://<gateway-ip>:80/get

# Test api host routing
curl -H "Host: api.example.com" http://<gateway-ip>:80/get

# Check resources
kubectl get gateway,vs -n q12-opal -o yaml
```

## Resources to Create
- **Gateway** named `my-gateway` with port 80, HTTP protocol
  - Two hosts: `web.example.com` and `api.example.com`
- **VirtualService** for `web.example.com` routing to `web:8000`
- **VirtualService** for `api.example.com` routing to `api-svc:8000`
