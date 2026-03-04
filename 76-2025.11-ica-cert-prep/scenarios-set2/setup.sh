#!/usr/bin/env bash
set -euo pipefail

# ICA Exam Practice v3 — 40 focused scenarios
#
# Topics covered:
#   q01-q14  Traffic Management (gateways, VS, DR, routing)
#   q15-q24  Securing Workloads (PeerAuth, AuthzPolicy)
#   q25-q30  ServiceEntry + TLS Origination
#   q31-q35  Fault Injection & Resiliency
#   q36-q40  Sidecar Resource
#
# Usage:
#   ./setup-v3.sh              # deploy all (q01-q40)
#   ./setup-v3.sh 1-20         # deploy q01-q20 only
#   ./setup-v3.sh 21-40        # deploy q21-q40 only
#   ./setup-v3.sh 5-10         # deploy q05-q10 only
#   ./setup-v3.sh --delete     # tear down all q* namespaces
#   ./setup-v3.sh --delete 1-20  # tear down q01-q20 only

# ─── Parse range ──────────────────────────────────────────────────
RANGE_START=1
RANGE_END=40
DELETE=false

for arg in "$@"; do
  if [[ "$arg" == "--delete" ]]; then
    DELETE=true
  elif [[ "$arg" =~ ^([0-9]+)-([0-9]+)$ ]]; then
    RANGE_START=${BASH_REMATCH[1]}
    RANGE_END=${BASH_REMATCH[2]}
  fi
done

in_range() {
  local num=$1
  (( num >= RANGE_START && num <= RANGE_END ))
}

# ─── Handle --delete ──────────────────────────────────────────────
if [[ "$DELETE" == true ]]; then
  echo "Deleting exam namespaces (q$(printf '%02d' $RANGE_START)-q$(printf '%02d' $RANGE_END))..."
  kubectl get ns --no-headers -o custom-columns=':metadata.name' | grep '^q[0-9]' | while read -r ns; do
    num=$(echo "$ns" | grep -o '^q[0-9]*' | sed 's/^q0*//')
    if (( num >= RANGE_START && num <= RANGE_END )); then
      echo "  deleting $ns"
      kubectl delete namespace "$ns" --wait=false 2>/dev/null || true
    fi
  done
  echo "Done."
  exit 0
fi

# ─── Prerequisites ────────────────────────────────────────────────
command -v kubectl >/dev/null 2>&1 || { echo "kubectl not found"; exit 1; }
CTX=$(kubectl config current-context)
echo "Context: $CTX"
echo "Range:   q$(printf '%02d' $RANGE_START) — q$(printf '%02d' $RANGE_END)"

ISTIO_INSTALLED=false
if kubectl get crd virtualservices.networking.istio.io &>/dev/null; then
  ISTIO_INSTALLED=true
  echo "Istio CRDs: found"
else
  echo "Istio CRDs: NOT found — Istio config will be skipped"
fi
echo ""

# ─── Helper: create namespace ─────────────────────────────────────
create_ns() {
  local ns=$1 domain=$2 topic=$3
  kubectl create namespace "$ns" --dry-run=client -o yaml | kubectl apply -f - >/dev/null
  kubectl label namespace "$ns" exam-domain="$domain" --overwrite >/dev/null
  kubectl label namespace "$ns" istio-injection=enabled --overwrite >/dev/null
  kubectl annotate namespace "$ns" scenario="$topic" --overwrite >/dev/null
  printf "  %-14s [%-10s]  %s\n" "$ns" "$domain" "$topic"
}

# ─── Helper: deploy client (curl pod) with custom name ───────────
deploy_client() {
  local ns=$1 name=${2:-client} sa=${3:-$2}
  sa=${sa:-client}
  kubectl apply -n "$ns" -f - >/dev/null <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ${sa}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${name}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ${name}
  template:
    metadata:
      labels:
        app: ${name}
    spec:
      serviceAccountName: ${sa}
      containers:
      - name: curl
        image: curlimages/curl
        command: ["/bin/sh","-c","while true; do sleep 3600; done"]
        resources:
          requests: { cpu: 10m, memory: 32Mi }
          limits:   { memory: 64Mi }
---
apiVersion: v1
kind: Service
metadata:
  name: ${name}
spec:
  selector:
    app: ${name}
  ports:
  - name: http
    port: 80
EOF
}

# ─── Helper: deploy httpbin-based server with custom name ─────────
deploy_server() {
  local ns=$1 name=${2:-my-app} sa=${3:-$2}
  sa=${sa:-my-app}
  kubectl apply -n "$ns" -f - >/dev/null <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ${sa}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${name}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ${name}
      version: v1
  template:
    metadata:
      labels:
        app: ${name}
        version: v1
    spec:
      serviceAccountName: ${sa}
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
  name: ${name}
spec:
  selector:
    app: ${name}
  ports:
  - name: http
    port: 8000
    targetPort: 80
EOF
}

# ─── Helper: deploy httpbin-based server v1+v2 ────────────────────
deploy_server_v1v2() {
  local ns=$1 name=${2:-my-app} sa=${3:-$2}
  sa=${sa:-my-app}
  kubectl apply -n "$ns" -f - >/dev/null <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ${sa}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${name}-v1
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ${name}
      version: v1
  template:
    metadata:
      labels:
        app: ${name}
        version: v1
    spec:
      serviceAccountName: ${sa}
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
  name: ${name}-v2
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ${name}
      version: v2
  template:
    metadata:
      labels:
        app: ${name}
        version: v2
    spec:
      serviceAccountName: ${sa}
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
  name: ${name}
spec:
  selector:
    app: ${name}
  ports:
  - name: http
    port: 8000
    targetPort: 80
EOF
}

# ─── Helper: deploy v1+v2+v3 ─────────────────────────────────────
deploy_server_v1v2v3() {
  local ns=$1 name=${2:-my-app} sa=${3:-$2}
  sa=${sa:-my-app}
  deploy_server_v1v2 "$ns" "$name" "$sa"
  kubectl apply -n "$ns" -f - >/dev/null <<EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${name}-v3
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ${name}
      version: v3
  template:
    metadata:
      labels:
        app: ${name}
        version: v3
    spec:
      serviceAccountName: ${sa}
      containers:
      - name: httpbin
        image: kong/httpbin
        ports:
        - containerPort: 80
        resources:
          requests: { cpu: 10m, memory: 64Mi }
          limits:   { memory: 128Mi }
EOF
}

# ─── Helper: deploy fortio (echo/load server) ────────────────────
deploy_fortio() {
  local ns=$1 name=${2:-echo}
  kubectl apply -n "$ns" -f - >/dev/null <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: ${name}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${name}
spec:
  replicas: 1
  selector:
    matchLabels:
      app: ${name}
  template:
    metadata:
      labels:
        app: ${name}
    spec:
      serviceAccountName: ${name}
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
  name: ${name}
spec:
  selector:
    app: ${name}
  ports:
  - name: http
    port: 8080
EOF
}

# ══════════════════════════════════════════════════════════════════
# TRAFFIC MANAGEMENT  q01-q14
# ══════════════════════════════════════════════════════════════════
if in_range 1 || in_range 2 || in_range 3 || in_range 4 || in_range 5 || \
   in_range 6 || in_range 7 || in_range 8 || in_range 9 || in_range 10 || \
   in_range 11 || in_range 12 || in_range 13 || in_range 14; then
  echo "Traffic Management (q01-q14)"
fi

if in_range 1; then
  create_ns q01-mars traffic "Classic Istio Gateway + VirtualService ingress"
  deploy_client q01-mars client
  deploy_server q01-mars my-app
fi

if in_range 2; then
  create_ns q02-titan traffic "VirtualService header-based routing (v1/v2)"
  deploy_client q02-titan tester
  deploy_server_v1v2 q02-titan backend
fi

if in_range 3; then
  create_ns q03-nova traffic "VS path-based routing to multiple services"
  deploy_client q03-nova client
  deploy_server q03-nova api-svc
  deploy_server q03-nova portal
fi

if in_range 4; then
  create_ns q04-spark traffic "VS rule ordering — specific before catch-all"
  deploy_client q04-spark caller
  deploy_server_v1v2 q04-spark web
fi

if in_range 5; then
  create_ns q05-drift traffic "Traffic shifting — weighted 80/20 canary"
  deploy_client q05-drift client
  deploy_server_v1v2 q05-drift store
fi

if in_range 6; then
  create_ns q06-ember traffic "DestinationRule subsets + ROUND_ROBIN LB"
  deploy_client q06-ember tester
  deploy_server_v1v2 q06-ember my-app
fi

if in_range 7; then
  create_ns q07-frost traffic "Traffic mirroring to shadow version"
  deploy_client q07-frost client
  deploy_server_v1v2 q07-frost backend
fi

if in_range 8; then
  create_ns q08-jade traffic "Gateway + VS with TLS passthrough"
  deploy_client q08-jade probe
  deploy_fortio q08-jade echo
fi

if in_range 9; then
  create_ns q09-lunar traffic "VS regex match + URI rewrite"
  deploy_client q09-lunar client
  deploy_server q09-lunar api-svc
fi

if in_range 10; then
  create_ns q10-mist traffic "VS delegate — multi-VS for same host"
  deploy_client q10-mist tester
  deploy_server q10-mist portal
  deploy_server q10-mist store
fi

if in_range 11; then
  create_ns q11-neon traffic "DestinationRule connection pool settings"
  deploy_client q11-neon client
  deploy_server q11-neon my-app
fi

if in_range 12; then
  create_ns q12-opal traffic "Gateway with multiple hosts (SNI routing)"
  deploy_client q12-opal caller
  deploy_server q12-opal web
  deploy_server q12-opal api-svc
fi

if in_range 13; then
  create_ns q13-peak traffic "VS catch-all + specific overrides (v1/v2/v3)"
  deploy_client q13-peak client
  deploy_server_v1v2v3 q13-peak backend
fi

if in_range 14; then
  create_ns q14-ridge traffic "Request headers manipulation (add/remove in VS)"
  deploy_client q14-ridge tester
  deploy_server q14-ridge my-app
fi

# ══════════════════════════════════════════════════════════════════
# SECURING WORKLOADS  q15-q24
# ══════════════════════════════════════════════════════════════════
if in_range 15 || in_range 16 || in_range 17 || in_range 18 || in_range 19 || \
   in_range 20 || in_range 21 || in_range 22 || in_range 23 || in_range 24; then
  echo ""
  echo "Securing Workloads (q15-q24)"
fi

if in_range 15; then
  create_ns q15-storm security "PeerAuthentication STRICT mTLS namespace-wide"
  deploy_client q15-storm client
  deploy_server q15-storm backend
fi

if in_range 16; then
  create_ns q16-umbra security "PeerAuthentication port-level mTLS override"
  deploy_client q16-umbra tester
  deploy_server q16-umbra api-svc
fi

if in_range 17; then
  create_ns q17-wave security "AuthzPolicy ALLOW by ServiceAccount"
  deploy_client q17-wave client
  deploy_server q17-wave payments
  deploy_server q17-wave store
fi

if in_range 18; then
  create_ns q18-xenon security "AuthzPolicy DENY specific HTTP methods + paths"
  deploy_client q18-xenon caller
  deploy_server q18-xenon my-app
fi

if in_range 19; then
  create_ns q19-zinc security "AuthzPolicy combining SA + methods + paths (L7)"
  deploy_client q19-zinc client client
  deploy_client q19-zinc tester tester
  deploy_server q19-zinc web
  deploy_server q19-zinc backend
fi

if in_range 20; then
  create_ns q20-apex security "AuthzPolicy CUSTOM action (ext-authz)"
  deploy_client q20-apex tester
  deploy_server q20-apex portal
fi

if in_range 21; then
  create_ns q21-bolt security "AuthzPolicy multiple rules and precedence"
  deploy_client q21-bolt client
  deploy_server q21-bolt api-svc
fi

if in_range 22; then
  create_ns q22-crest security "mTLS migration PERMISSIVE → STRICT"
  deploy_client q22-crest probe
  deploy_server q22-crest my-app
  if [[ "$ISTIO_INSTALLED" == true ]]; then
    kubectl apply -n q22-crest -f - >/dev/null <<'EOF'
apiVersion: security.istio.io/v1
kind: PeerAuthentication
metadata:
  name: default
spec:
  mtls:
    mode: PERMISSIVE
EOF
  fi
fi

if in_range 23; then
  create_ns q23-delta security "AuthzPolicy deny-all + granular allow"
  deploy_client q23-delta client client
  deploy_client q23-delta sender sender
  deploy_server q23-delta payments
  deploy_server q23-delta store
  if [[ "$ISTIO_INSTALLED" == true ]]; then
    kubectl apply -n q23-delta -f - >/dev/null <<'EOF'
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: deny-all
spec: {}
EOF
  fi
fi

if in_range 24; then
  create_ns q24-edge security "AuthzPolicy source namespaces + principals"
  deploy_client q24-edge tester
  deploy_server q24-edge backend
fi

# ══════════════════════════════════════════════════════════════════
# SERVICE ENTRY + TLS ORIGINATION  q25-q30
# ══════════════════════════════════════════════════════════════════
if in_range 25 || in_range 26 || in_range 27 || in_range 28 || in_range 29 || in_range 30; then
  echo ""
  echo "ServiceEntry + TLS Origination (q25-q30)"
fi

if in_range 25; then
  create_ns q25-flint egress "ServiceEntry for external HTTP service"
  deploy_client q25-flint client
fi

if in_range 26; then
  create_ns q26-grain egress "ServiceEntry + DestinationRule TLS origination"
  deploy_client q26-grain client
fi

if in_range 27; then
  create_ns q27-helix egress "ServiceEntry onboarding in-cluster service to mesh"
  deploy_client q27-helix client
  deploy_fortio q27-helix echo
fi

if in_range 28; then
  create_ns q28-ionic egress "Egress control — ServiceEntry + VS routing"
  deploy_client q28-ionic client
fi

if in_range 29; then
  create_ns q29-jewel egress "ServiceEntry with multiple endpoints + locality"
  deploy_client q29-jewel client
fi

if in_range 30; then
  create_ns q30-karma egress "TLS origination with custom SNI via DR"
  deploy_client q30-karma client
fi

# ══════════════════════════════════════════════════════════════════
# FAULT INJECTION & RESILIENCY  q31-q35
# ══════════════════════════════════════════════════════════════════
if in_range 31 || in_range 32 || in_range 33 || in_range 34 || in_range 35; then
  echo ""
  echo "Fault Injection & Resiliency (q31-q35)"
fi

if in_range 31; then
  create_ns q31-blaze resiliency "Fault injection — HTTP abort"
  deploy_client q31-blaze client
  deploy_server q31-blaze my-app
fi

if in_range 32; then
  create_ns q32-comet resiliency "Fault injection — delay"
  deploy_client q32-comet tester
  deploy_server q32-comet backend
fi

if in_range 33; then
  create_ns q33-glow resiliency "Retries with retryOn conditions"
  deploy_client q33-glow client
  deploy_server q33-glow api-svc
fi

if in_range 34; then
  create_ns q34-haze resiliency "Timeout configuration"
  deploy_client q34-haze caller
  deploy_server q34-haze web
fi

if in_range 35; then
  create_ns q35-quake resiliency "Circuit breaking + outlier detection"
  deploy_client q35-quake client
  deploy_server q35-quake store
  deploy_fortio q35-quake fortio
fi

# ══════════════════════════════════════════════════════════════════
# SIDECAR RESOURCE  q36-q40
# ══════════════════════════════════════════════════════════════════
if in_range 36 || in_range 37 || in_range 38 || in_range 39 || in_range 40; then
  echo ""
  echo "Sidecar Resource (q36-q40)"
fi

if in_range 36; then
  create_ns q36-tidal sidecar "Sidecar — limit egress to specific services"
  deploy_client q36-tidal client
  deploy_server q36-tidal my-app
fi

if in_range 37; then
  create_ns q37-venom sidecar "Sidecar — ingress listener config"
  deploy_client q37-venom tester
  deploy_server q37-venom backend
fi

if in_range 38; then
  create_ns q38-kite sidecar "Sidecar — workload-specific scope (selector)"
  deploy_client q38-kite client
  deploy_server q38-kite api-svc
  deploy_server q38-kite web
fi

if in_range 39; then
  create_ns q39-pluto sidecar "Sidecar — namespace-wide exportTo restriction"
  deploy_client q39-pluto caller
  deploy_server q39-pluto portal
  deploy_server q39-pluto store
fi

if in_range 40; then
  create_ns q40-xenith sidecar "Sidecar — outboundTrafficPolicy REGISTRY_ONLY"
  deploy_client q40-xenith client
  deploy_server q40-xenith my-app
fi

# ──────────────────────────────────────────────────────────────────
# Summary
# ──────────────────────────────────────────────────────────────────
echo ""
echo "============================================"
echo " Setup complete (q$(printf '%02d' $RANGE_START)-q$(printf '%02d' $RANGE_END))"
echo "============================================"
echo ""
echo "Waiting for pods to schedule..."
sleep 3

total=$(kubectl get pods --all-namespaces --no-headers -l 'app' 2>/dev/null | grep '^q[0-9]' | wc -l)
ready=$(kubectl get pods --all-namespaces --no-headers -l 'app' 2>/dev/null | grep '^q[0-9]' | grep -c Running || true)
echo "Pods: ${ready}/${total} running (remaining will come up shortly)"
echo ""
echo "Quick reference:"
echo "  ls scenarios-v3/                              # list all scenarios"
echo "  kubectl exec -n q01-mars deploy/client -- curl -s my-app:8000/get"
echo "  kubectl get ns -l exam-domain                 # list exam namespaces"
echo "  ./setup-v3.sh --delete                        # tear down everything"
echo "  ./setup-v3.sh --delete 1-20                   # tear down q01-q20 only"
