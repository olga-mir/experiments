# Q30 - Karma: TLS Origination for External Services

## Namespace
`q30-karma`

## Workloads
- `client` (SA: default, curlimages/curl)

## Context

The mesh has `outboundTrafficPolicy: REGISTRY_ONLY` — external traffic is blocked unless
a ServiceEntry exists. Apps call `http://httpbin.org/get` (plain HTTP on port 80), but
the sidecar must transparently upgrade the connection to HTTPS on port 443 (TLS origination).

## Task

1. Create a **ServiceEntry** for `httpbin.org`:
   - Port 80 (HTTP) with `targetPort: 443` — tells the proxy to connect upstream on 443
   - Port 443 (HTTPS) — registers the upstream protocol
   - Resolution: DNS, Location: MESH_EXTERNAL

2. Create a **DestinationRule** for `httpbin.org`:
   - `portLevelSettings` on port **80** (not 443) — matches the app-facing port
   - TLS mode: SIMPLE (proxy verifies server cert via system CA, no client cert needed)

3. Optionally add a **VirtualService** for timeout (targetPort in SE handles the routing):

## Solution

```yaml
# ServiceEntry — port 80 with targetPort:443 handles the redirect without VS
apiVersion: networking.istio.io/v1
kind: ServiceEntry
metadata:
  name: httpbin-ext
  namespace: q30-karma
spec:
  hosts:
  - httpbin.org
  ports:
  - number: 80
    name: http-port
    protocol: HTTP
    targetPort: 443   # proxy connects to 443 even when app uses 80
  - number: 443
    name: https-port
    protocol: HTTPS
  resolution: DNS
  location: MESH_EXTERNAL
---
# DestinationRule — portLevelSettings on port 80 (app-facing port, not upstream port)
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: httpbin-ext
  namespace: q30-karma
spec:
  host: httpbin.org
  trafficPolicy:
    portLevelSettings:
    - port:
        number: 80
      tls:
        mode: SIMPLE
---
# VirtualService — optional, for timeout
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: httpbin-ext
  namespace: q30-karma
spec:
  hosts:
  - httpbin.org
  http:
  - timeout: 5s
    route:
    - destination:
        host: httpbin.org
        port:
          number: 80
```

## Verification

```bash
# App calls plain HTTP — sidecar upgrades to HTTPS
kubectl exec -n q30-karma deploy/client -- curl -s http://httpbin.org/get | jq .url
# Expected: "https://httpbin.org/get"  ← proves TLS origination worked
# (httpbin reflects the URL as seen by the server — it receives HTTPS on port 443)

# Verify the cluster is configured
istioctl proxy-config cluster deploy/client -n q30-karma | grep httpbin

# Without ServiceEntry (REGISTRY_ONLY blocks it):
# curl returns 502 or connection refused
```

## Key Concepts

| | Meaning |
|---|---|
| SE `targetPort: 443` on port 80 | Proxy connects to upstream:443 even when app used port 80 |
| DR `portLevelSettings.port: 80` | Matches the **app-facing** port, not the upstream port |
| `tls.mode: SIMPLE` | Proxy originates TLS; validates server cert via system CA |
| `tls.mode: MUTUAL` | Proxy also presents a client cert |
| `sni` field | Overrides SNI in ClientHello — only needed if TLS hostname ≠ SE host |

## Common mistakes

**Wrong DR port (443 instead of 80):**
When SE has `protocol: HTTPS` on port 443 and DR has portLevelSettings on 443,
Istio applies TLS to the port 80 cluster too → `WRONG_VERSION_NUMBER` on port 80.
portLevelSettings must match the **app-facing** port (80), not the upstream port.

**Global tls instead of portLevelSettings:**
`trafficPolicy.tls.mode: SIMPLE` (no portLevelSettings) applies TLS to ALL ports
including port 80 → same `WRONG_VERSION_NUMBER` error.

**VS without targetPort:**
If you use a VS to route port 80 → destination port 443, the DR portLevelSettings
must still be on port 80 (not 443). The VS changes the destination but the DR
matches the original service port.
