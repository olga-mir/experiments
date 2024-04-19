#!/bin/bash

set -eoux pipefail

# https://cloud.google.com/kubernetes-engine/docs/tutorials/serve-gemma-gpu-vllm


kubectl create secret generic hf-secret \
    --from-literal=hf_api_token=$HF_TOKEN \
    --dry-run=client -o yaml | kubectl apply -f -

# it - instruction tuned.
# pretrained - shouldn't be deployed before it is tuned.
