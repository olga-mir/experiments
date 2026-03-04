# q08-jade: Gateway + VirtualService with TLS Passthrough

## Namespace
`q08-jade`

## Workloads
- **probe**: curlimages/curl (test pod)
- **echo**: fortio/fortio (port 8080 → 8080)

## Task

1. Create a **Gateway** in `istio-system` with TLS mode `PASSTHROUGH` for host `echo.example.com` on port 443
2. Create a **VirtualService** with:
   - TLS route (not HTTP) matching `sniHosts: ["echo.example.com"]`
   - Routes to `echo:8080`
3. Explain what TLS passthrough means in the context of the gateway

## Verification

**TLS passthrough means:**
- The gateway does NOT terminate TLS (no decryption at the gateway)
- Encrypted traffic is forwarded directly to the backend
- The backend service must handle TLS termination
- Useful when backend wants to control TLS or when using mutual TLS between services

**Describe the gateway and VirtualService to verify configuration:**
```bash
kubectl get gateway -n istio-system jade-gateway -o yaml | grep -A 5 "tls:"
kubectl get vs -n q08-jade echo -o yaml | grep -A 10 "tls:"
```

Expected: Gateway shows `mode: PASSTHROUGH`, VirtualService shows TLS route with sniHosts.

## Resources to Create
- Namespace: `q08-jade`
- Deployments: `probe`, `echo` with fortio image
- Gateway: jade-gateway (TLS PASSTHROUGH, port 443)
- VirtualService: echo (TLS route with sniHosts)
