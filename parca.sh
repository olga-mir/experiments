#!/bin/bash

PARCA_VERSION="v0.19.0"
PARCA_AGENT_VERSION="v0.25.1"
kubectl create namespace parca
kubectl apply -f https://github.com/parca-dev/parca/releases/download/$PARCA_VERSION/kubernetes-manifest.yaml
kubectl apply -f https://github.com/parca-dev/parca-agent/releases/download/$PARCA_AGENT_VERSION/kubernetes-manifest.yaml
