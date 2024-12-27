#!/bin/bash

# https://kwok.sigs.k8s.io/docs/user/kwok-out-cluster/
kwok \
  --kubeconfig=~/.kube/config \
  --manage-all-nodes=false \
  --manage-nodes-with-annotation-selector=kwok.x-k8s.io/node=fake \
  --manage-nodes-with-label-selector= \
  --manage-single-node= \
  --cidr=10.0.0.1/24 \
  --node-ip=10.0.0.1 \
  --node-lease-duration-seconds=40