#!/usr/bin/env bash
set -euo pipefail

# ICA Exam Practice - Scenario Setup
# Creates 30 namespaces (q01-q30) with workloads covering all ICA curriculum topics.
#
# Distribution (matches exam weights):
#   q01-q11  Traffic Management        (35%)
#   q12-q18  Securing Workloads        (25%)
#   q19-q24  Troubleshooting           (20%)
#   q25-q30  Installation & Config     (20%)
#
# Usage:
#   ./setup.sh           # deploy everything
#   ./setup.sh --delete  # tear down all 30 namespaces

# ─── Handle --delete ──────────────────────────────────────────────
if [[ "${1:-}" == "--delete" ]]; then
  echo "Deleting all exam namespaces (q01-q30)..."
  for i in $(seq -w 1 30); do
    kubectl delete namespace "q$i" --ignore-not-found --wait=false
  done
  echo "Done."
  exit 0
fi

# ─── Prerequisites ────────────────────────────────────────────────
command -v kubectl >/dev/null 2>&1 || { echo "kubectl not found"; exit 1; }
CTX=$(kubectl config current-context)
echo "Context: $CTX"

ISTIO_INSTALLED=false
if kubectl get crd virtualservices.networking.istio.io &>/dev/null; then
  ISTIO_INSTALLED=true
  echo "Istio CRDs: found"
else
  echo "Istio CRDs: NOT found (troubleshooting broken-config scenarios will be skipped)"
fi
echo ""

# ─── Ensure images in local registry (if running) ────────────────
ensure_images() {
  local registry="kind-registry"
  local port=5001
  if docker inspect "$registry" &>/dev/null; then
    local images=("curlimages/curl:latest" "kong/httpbin:latest" "fortio/fortio:latest")
    for img in "${images[@]}"; do
      local name="${img%%:*}"   # e.g. curlimages/curl
      local tag="${img##*:}"
      # check if already in registry
      if curl -sf "http://localhost:${port}/v2/${name}/tags/list" 2>/dev/null | grep -q "$tag"; then
        continue
      fi
      echo "Caching $img in local registry..."
      docker pull "$img" 2>/dev/null \
        && docker tag "$img" "localhost:${port}/${name}:${tag}" \
        && docker push "localhost:${port}/${name}:${tag}" 2>/dev/null \
        || echo "  (could not cache $img – will pull directly)"
    done
  fi
}
ensure_images

# ─── Helper: create namespace ─────────────────────────────────────
create_ns() {
  local ns=$1 domain=$2 topic=$3
  kubectl create namespace "$ns" --dry-run=client -o yaml | kubectl apply -f - >/dev/null
  kubectl label namespace "$ns" exam-domain="$domain" --overwrite >/dev/null
  kubectl annotate namespace "$ns" scenario="$topic" --overwrite >/dev/null
  printf "  %-5s  [%-13s]  %s\n" "$ns" "$domain" "$topic"
}

# ─── Helper: deploy sleep (curl client) ──────────────────────────
deploy_sleep() {
  local ns=$1
  kubectl apply -n "$ns" -f - >/dev/null <<'EOF'
apiVersion: v1
kind: ServiceAccount
metadata:
  name: sleep
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: sleep
spec:
  replicas: 1
  selector:
    matchLabels:
      app: sleep
  template:
    metadata:
      labels:
        app: sleep
    spec:
      serviceAccountName: sleep
      containers:
      - name: sleep
        image: curlimages/curl
        command: ["/bin/sh","-c","while true; do sleep 3600; done"]
        resources:
          requests: { cpu: 10m, memory: 32Mi }
          limits:   { memory: 64Mi }
---
apiVersion: v1
kind: Service
metadata:
  name: sleep
spec:
  selector:
    app: sleep
  ports:
  - name: http
    port: 80
EOF
}

# ─── Helper: deploy httpbin (single version) ─────────────────────
deploy_httpbin() {
  local ns=$1
  kubectl apply -n "$ns" -f - >/dev/null <<'EOF'
apiVersion: v1
kind: ServiceAccount
metadata:
  name: httpbin
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: httpbin
spec:
  replicas: 1
  selector:
    matchLabels:
      app: httpbin
      version: v1
  template:
    metadata:
      labels:
        app: httpbin
        version: v1
    spec:
      serviceAccountName: httpbin
      containers:
      - name: httpbin
        image: kong/httpbin
        ports:
        - containerPort: 80
        resources:
          requests: { cpu: 10m, memory: 64Mi }
          limits:   { memory: 128Mi }
---
apiVersion: v1
kind: Service
metadata:
  name: httpbin
spec:
  selector:
    app: httpbin
  ports:
  - name: http
    port: 8000
    targetPort: 80
EOF
}

# ─── Helper: deploy httpbin v1 + v2 (two versions, one Service) ──
deploy_httpbin_v1v2() {
  local ns=$1
  kubectl apply -n "$ns" -f - >/dev/null <<'EOF'
apiVersion: v1
kind: ServiceAccount
metadata:
  name: httpbin
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: httpbin-v1
spec:
  replicas: 1
  selector:
    matchLabels:
      app: httpbin
      version: v1
  template:
    metadata:
      labels:
        app: httpbin
        version: v1
    spec:
      serviceAccountName: httpbin
      containers:
      - name: httpbin
        image: kong/httpbin
        ports:
        - containerPort: 80
        resources:
          requests: { cpu: 10m, memory: 64Mi }
          limits:   { memory: 128Mi }
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: httpbin-v2
spec:
  replicas: 1
  selector:
    matchLabels:
      app: httpbin
      version: v2
  template:
    metadata:
      labels:
        app: httpbin
        version: v2
    spec:
      serviceAccountName: httpbin
      containers:
      - name: httpbin
        image: kong/httpbin
        ports:
        - containerPort: 80
        resources:
          requests: { cpu: 10m, memory: 64Mi }
          limits:   { memory: 128Mi }
---
apiVersion: v1
kind: Service
metadata:
  name: httpbin
spec:
  selector:
    app: httpbin
  ports:
  - name: http
    port: 8000
    targetPort: 80
EOF
}

# ─── Helper: deploy fortio (load generator) ──────────────────────
deploy_fortio() {
  local ns=$1
  kubectl apply -n "$ns" -f - >/dev/null <<'EOF'
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fortio
spec:
  replicas: 1
  selector:
    matchLabels:
      app: fortio
  template:
    metadata:
      labels:
        app: fortio
    spec:
      containers:
      - name: fortio
        image: fortio/fortio
        ports:
        - containerPort: 8080
        resources:
          requests: { cpu: 10m, memory: 64Mi }
          limits:   { memory: 128Mi }
---
apiVersion: v1
kind: Service
metadata:
  name: fortio
spec:
  selector:
    app: fortio
  ports:
  - name: http
    port: 8080
EOF
}

# ──────────────────────────────────────────────────────────────────
# TRAFFIC MANAGEMENT  (35%)  q01-q11
# ──────────────────────────────────────────────────────────────────
echo "Traffic Management (q01-q11)"

create_ns q01 traffic "Gateway API ingress (Gateway + HTTPRoute)"
deploy_httpbin q01; deploy_sleep q01

create_ns q02 traffic "Classic Istio ingress (Gateway + VirtualService)"
deploy_httpbin q02; deploy_sleep q02

create_ns q03 traffic "Request routing – header and path based"
deploy_httpbin_v1v2 q03; deploy_sleep q03

create_ns q04 traffic "Traffic shifting – weighted canary"
deploy_httpbin_v1v2 q04; deploy_sleep q04

create_ns q05 traffic "DestinationRule subsets + load balancing"
deploy_httpbin_v1v2 q05; deploy_sleep q05

create_ns q06 traffic "Timeouts and retries"
deploy_httpbin q06; deploy_sleep q06

create_ns q07 traffic "Fault injection (delay + abort)"
deploy_httpbin q07; deploy_sleep q07

create_ns q08 traffic "Circuit breaking + outlier detection"
deploy_httpbin q08; deploy_sleep q08; deploy_fortio q08

create_ns q09 traffic "ServiceEntry – reach external services"
deploy_sleep q09

create_ns q10 traffic "Egress gateway control"
deploy_httpbin q10; deploy_sleep q10

create_ns q11 traffic "Traffic mirroring"
deploy_httpbin_v1v2 q11; deploy_sleep q11

# ──────────────────────────────────────────────────────────────────
# SECURING WORKLOADS  (25%)  q12-q18
# ──────────────────────────────────────────────────────────────────
echo ""
echo "Securing Workloads (q12-q18)"

create_ns q12 security "Strict mTLS – PeerAuthentication"
deploy_httpbin q12; deploy_sleep q12

create_ns q13 security "mTLS migration (PERMISSIVE → STRICT)"
deploy_httpbin q13; deploy_sleep q13

create_ns q14 security "AuthorizationPolicy – ALLOW rules"
deploy_httpbin q14; deploy_sleep q14

create_ns q15 security "AuthorizationPolicy – DENY rules"
deploy_httpbin q15; deploy_sleep q15

create_ns q16 security "L7 AuthorizationPolicy (path + method + header)"
deploy_httpbin q16; deploy_sleep q16

create_ns q17 security "JWT authentication (RequestAuthentication)"
deploy_httpbin q17; deploy_sleep q17

create_ns q18 security "TLS termination at ingress gateway"
deploy_httpbin q18; deploy_sleep q18

# ──────────────────────────────────────────────────────────────────
# TROUBLESHOOTING  (20%)  q19-q24
# ──────────────────────────────────────────────────────────────────
echo ""
echo "Troubleshooting (q19-q24)"

# q19 – broken VirtualService (wrong host name)
create_ns q19 troubleshoot "Fix broken VirtualService (wrong host)"
deploy_httpbin q19; deploy_sleep q19
if [[ "$ISTIO_INSTALLED" == true ]]; then
  kubectl apply -n q19 -f - >/dev/null <<'EOF'
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: httpbin-vs
spec:
  hosts:
  - httpbin-typo          # BUG: should be "httpbin"
  http:
  - route:
    - destination:
        host: httpbin-typo
        port:
          number: 8000
EOF
fi

# q20 – namespace not enrolled in mesh
create_ns q20 troubleshoot "Fix missing mesh enrollment"
deploy_httpbin q20; deploy_sleep q20
# intentionally no mesh label

# q21 – AuthorizationPolicy blocks everything
create_ns q21 troubleshoot "Fix overly restrictive AuthorizationPolicy"
deploy_httpbin q21; deploy_sleep q21
if [[ "$ISTIO_INSTALLED" == true ]]; then
  kubectl apply -n q21 -f - >/dev/null <<'EOF'
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: deny-all
spec: {}
EOF
fi

# q22 – DestinationRule subset label mismatch
create_ns q22 troubleshoot "Fix DestinationRule subset mismatch"
deploy_httpbin q22; deploy_sleep q22
if [[ "$ISTIO_INSTALLED" == true ]]; then
  kubectl apply -n q22 -f - >/dev/null <<'EOF'
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: httpbin-dr
spec:
  host: httpbin
  subsets:
  - name: v1
    labels:
      version: v-one      # BUG: actual pod label is "v1"
---
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: httpbin-vs
spec:
  hosts:
  - httpbin
  http:
  - route:
    - destination:
        host: httpbin
        subset: v1
        port:
          number: 8000
EOF
fi

# q23 – DestinationRule TLS mode conflicts with PeerAuthentication
create_ns q23 troubleshoot "Fix TLS mode mismatch (DR vs PeerAuthentication)"
deploy_httpbin q23; deploy_sleep q23
if [[ "$ISTIO_INSTALLED" == true ]]; then
  kubectl apply -n q23 -f - >/dev/null <<'EOF'
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: httpbin-pa
spec:
  selector:
    matchLabels:
      app: httpbin
  mtls:
    mode: DISABLE
---
apiVersion: networking.istio.io/v1
kind: DestinationRule
metadata:
  name: httpbin-dr
spec:
  host: httpbin
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL   # BUG: requires mTLS but PeerAuth disables it
EOF
fi

# q24 – general control plane + data plane diagnostics
create_ns q24 troubleshoot "Diagnose control plane and data plane issues"
deploy_httpbin q24; deploy_sleep q24

# ──────────────────────────────────────────────────────────────────
# INSTALLATION & CONFIGURATION  (20%)  q25-q30
# ──────────────────────────────────────────────────────────────────
echo ""
echo "Installation & Configuration (q25-q30)"

create_ns q25 install "Install/configure Istio with istioctl"
deploy_httpbin q25; deploy_sleep q25

create_ns q26 install "Install/configure Istio with Helm"
deploy_httpbin q26; deploy_sleep q26

create_ns q27 install "Enroll namespace in ambient mesh"
deploy_httpbin q27; deploy_sleep q27
# user must add: kubectl label ns q27 istio.io/dataplane-mode=ambient

create_ns q28 install "Enable sidecar injection for namespace"
deploy_httpbin q28; deploy_sleep q28
# user must add: kubectl label ns q28 istio-injection=enabled + restart pods

create_ns q29 install "Deploy waypoint proxy for L7 in ambient"
deploy_httpbin q29; deploy_sleep q29
# user must: istioctl waypoint apply -n q29

create_ns q30 install "Canary upgrade with revision labels"
deploy_httpbin q30; deploy_sleep q30
# user must: relabel namespace with istio.io/rev=<revision>

# ──────────────────────────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────────────────────────
echo ""
echo "============================================"
echo " Setup complete – 30 namespaces created"
echo "============================================"
echo ""
echo "Waiting for pods to schedule..."
sleep 3

total=$(kubectl get pods -l 'app in (sleep,httpbin,fortio)' --all-namespaces --no-headers 2>/dev/null | wc -l)
ready=$(kubectl get pods -l 'app in (sleep,httpbin,fortio)' --all-namespaces --no-headers 2>/dev/null | grep -c Running || true)
echo "Pods: ${ready}/${total} running (remaining will come up shortly)"
echo ""
echo "Quick reference:"
echo "  kubectl get pods -n q<NN>                     # check workloads"
echo "  kubectl exec -n q<NN> deploy/sleep -- curl -s httpbin:8000/get   # test connectivity"
echo "  kubectl get ns -l exam-domain                 # list all exam namespaces"
echo "  ./setup.sh --delete                           # tear down everything"
