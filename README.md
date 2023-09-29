# About

This repo contains collection of test manifests and deploy scripts to run and test stuff on Kubernetes. Most of these can be deployed in `kind`.

Other repos here to create clusters:

https://github.com/olga-mir/k8s-multi-cluster - AWS multi cluster setup provisioned with Cluster API and FluxCD
https://github.com/olga-mir/k8s - AWS with kOps, GKE with terraform or gcloud (with misc flavors: ASM, multi network for pods, etc)

# Run

Some fields are dynamic or private, they are templated out by env vars.

```
envsubst < alpine-targeted-node-tmpl.yaml > alpine-targeted-node-rendered.yaml
```
