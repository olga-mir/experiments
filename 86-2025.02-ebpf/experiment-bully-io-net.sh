#!/bin/bash

set -eoux pipefail

CTX=gke_${PROJECT_ID}_${ZONE}_experiment-ebpf-cluster
safedate=$(date +%F_%H_%M_%S)

kubectl --context "$CTX" run fortio-load --image=fortio/fortio --restart=Never -- \
  load -c 4 -qps 100 -t 0 http://victim-api.default.svc.cluster.local:5678/ &
sleep 5

kubectl --context "$CTX" apply -f k8s/bully-io.yaml
task dump-runq-enqueued  > ./outputs/${safedate}-runq-enqueued-1.txt
task list-pod-cgroups | grep test-pool | grep -v kube-system | awk 'OFS=" - " {print $3, $5}'
sleep 120
# observe a few minutes, then:
kubectl --context "$CTX" delete -f k8s/bully-io.yaml


kubectl --context "$CTX" apply -f k8s/bully-net.yaml
task dump-runq-enqueued  > ./outputs/${safedate}-runq-enqueued-2.txt
task list-pod-cgroups | grep test-pool | grep -v kube-system | awk 'OFS=" - " {print $3, $5}'
sleep 120
# observe, then:
kubectl --context "$CTX" delete -f k8s/bully-net.yaml

# experiment cleanup
kubectl --context "$CTX" delete pod fortio-load --ignore-not-found
task dump-runq-enqueued  > ./outputs/${safedate}-runq-enqueued-3.txt

