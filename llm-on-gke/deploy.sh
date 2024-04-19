#!/bin/bash

set -eoux pipefail

# https://cloud.google.com/kubernetes-engine/docs/tutorials/serve-gemma-gpu-vllm


kubectl create secret generic hf-secret \
    --from-literal=hf_api_token=$HF_TOKEN \
    --dry-run=client -o yaml | kubectl apply -f -

kubectl apply -f "./k8s-manifests-gemma-2b-it-vllm.yaml"

kubectl wait --for=condition=Available --timeout=700s deployment/vllm-gemma-deployment

# kubectl logs -f -l app=gemma-server

# kubectl port-forward service/llm-service 8000:8000

# it - instruction tuned.
# pretrained - shouldn't be deployed before it is tuned.
