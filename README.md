# About

This repo is a collection of POCs built primarily on GCP and Kubernetes. The goal is to continuously learn new tech, experiemt with new combinations, reverse engineer while also documenting and sharing the knowledge with my team and the community.

POCs that use k8s assume pre-existing cluster and access with sufficient permission to GCP and/or AWS account. For creating Kubernetes clusters I use other repos:

https://github.com/olga-mir/k8s-multi-cluster - AWS multi cluster setup provisioned with Cluster API and FluxCD
https://github.com/olga-mir/k8s - AWS with kOps, GKE with terraform or gcloud (with misc flavors: ASM, multi network for pods, etc)

# Repo Structure

Most folders contain self-containted POCs or experiments. These folders are prefixed with 2-digit number in such a way that latest experiments appear at the top.

Other general purpose folders:

[k8s-manifests-general](./k8s-manifests-general) - manifests to deploy on a k8s cluster

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