#!/bin/bash

set -eoux pipefail

create_deployment() {
  kubectl create deployment test-deployment-$1 --image=nginx
  kubectl expose deployment test-deployment-$1 --port=80
}

delete_deployment() {
  kubectl delete deployment test-deployment-$1
  kubectl delete service test-deployment-$1
}

create_virtualservice() {
  cat <<EOF | kubectl apply -f -
apiVersion: networking.istio.io/v1alpha3
kind: VirtualService
metadata:
  name: test-virtualservice-$1
spec:
  hosts:
  - "*"
  gateways:
  - istio-system/istio-ingressgateway
  http:
  - match:
    - uri:
        prefix: /test-$1
    route:
    - destination:
        host: test-deployment-$1
        port:
          number: 80
EOF
}

delete_virtualservice() {
  kubectl delete virtualservice test-virtualservice-$1
}

# Loop to create and delete resources repeatedly
for i in {1..50}; do
  echo "Iteration $i: Creating resources..."
  create_deployment $i
  create_virtualservice $i
  
  # Sleep for a short period to allow xDS updates
  sleep 10
  
  echo "Iteration $i: Deleting resources..."
  delete_virtualservice $i
  delete_deployment $i
  
  # Sleep for a short period to allow xDS updates
  sleep 10
done

echo "Load generation complete."

