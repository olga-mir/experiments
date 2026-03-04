# Q18 – TLS Termination at Ingress Gateway

**Domain:** Securing Workloads
**Namespace:** q18
**Workloads:** httpbin, sleep

## Task

Configure HTTPS ingress with TLS termination at the gateway.

1. Generate a self-signed TLS certificate for `httpbin.q18.example.com`
2. Create a Kubernetes `Secret` (type: `kubernetes.io/tls`) with the cert and key
3. Create an Istio `Gateway` that:
   - Listens on port 443
   - Terminates TLS using the secret (mode: SIMPLE)
   - Accepts traffic for host `httpbin.q18.example.com`
4. Create a `VirtualService` to route traffic to httpbin:8000
5. Verify HTTPS access works

## Verification

```bash
# Generate self-signed cert
openssl req -x509 -sha256 -nodes -days 1 -newkey rsa:2048 \
  -subj '/CN=httpbin.q18.example.com/O=example' \
  -keyout /tmp/q18.key -out /tmp/q18.crt

# Create the secret
kubectl create secret tls -n q18 httpbin-tls --cert=/tmp/q18.crt --key=/tmp/q18.key

# After creating Gateway + VirtualService, test:
INGRESS_HOST=$(kubectl -n istio-system get svc istio-ingressgateway -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "localhost")
curl -sk --resolve "httpbin.q18.example.com:443:$INGRESS_HOST" https://httpbin.q18.example.com/get
```

## Resources to create

- `v1/Secret` (kubernetes.io/tls)
- `networking.istio.io/Gateway` (TLS mode: SIMPLE)
- `networking.istio.io/VirtualService`
