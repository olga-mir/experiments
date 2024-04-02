# About

This repo contains collection of test manifests and deploy scripts to run and test stuff in k8s or other services in GCP and AWS.

Other repos here to create clusters:

https://github.com/olga-mir/k8s-multi-cluster - AWS multi cluster setup provisioned with Cluster API and FluxCD
https://github.com/olga-mir/k8s - AWS with kOps, GKE with terraform or gcloud (with misc flavors: ASM, multi network for pods, etc)

# Repo Structure

[k8s-manifests-general](./k8s-manifests-general) - manifests to deploy on a k8s cluster

[gcp-secure-web-proxy](./gcp-secure-web-proxy) - GCP Secure Web Proxy: https://cloud.google.com/secure-web-proxy/docs/overview

[scripts](./scripts) -  generic scripts

# Run

Some fields are dynamic or private, they are templated out by env vars.

```
envsubst < alpine-targeted-node-tmpl.yaml > alpine-targeted-node-rendered.yaml
```

To render all tmpl found in the repo run [scripts/render.sh](./scripts/render.sh) from any location in repo dir and apply file that ends with `-rendered.yaml`


## Private Image Registry

Login to ECR and create docker login secret in $NAMESPACE (if not set or provided in command line default `test` is used):

```
./scripts/login-private-registry.sh [NAMEPACE]
```
