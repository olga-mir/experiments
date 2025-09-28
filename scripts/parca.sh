#!/bin/bash

PARCA_VERSION="v0.24.2"
PARCA_AGENT_VERSION="v0.41.1"
# https://github.com/parca-dev/parca-agent

kubectl create namespace parca
kubectl apply -f https://github.com/parca-dev/parca/releases/download/$PARCA_VERSION/kubernetes-manifest.yaml
kubectl apply -f https://github.com/parca-dev/parca-agent/releases/download/$PARCA_AGENT_VERSION/kubernetes-manifest.yaml
