# q01-mars: Classic Istio Gateway + VirtualService Ingress

## Namespace
`q01-mars`

## Workloads
- **client**: curlimages/curl (test pod)
- **my-app**: kong/httpbin (port 8000 → 80 internal)

## Task

1. Create a **Gateway** in `istio-ingress` namespace named `mars-gateway` listening on port 80 for host `my-app.example.com` (HTTP protocol)
2. Create a **VirtualService** in `q01-mars` that routes traffic from the gateway to `my-app:8000`
3. Verify the routing works both from inside the mesh and via the gateway

## Verification

**From inside the mesh (pod to pod):**
```bash
kubectl exec deploy/client -n q01-mars -- curl -s my-app:8000/get | jq .
```

**Via the gateway (from host, using port 8080 for ingress):**
```bash
curl -H "Host: my-app.example.com" http://localhost:8080/get | jq .
```

Expected: Both return HTTP 200 with httpbin response.

## Resources to Create
- Namespace: `q01-mars`
- Deployment: `client` + `my-app` with httpbin image
- Gateway: mars-gateway (port 80, host my-app.example.com)
- VirtualService: my-app (routes gateway → my-app:8000)
