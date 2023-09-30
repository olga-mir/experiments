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

 To render all tmpl found in the repo run [scripts/render.sh](./scripts/render.sh) from any location in repo dir and apply file that ends with `-rendered.yaml`


## Private Image Registry

Login to ECR and create docker login secret in $NAMESPACE (if not set or provided in command line default `test` is used):

```
./scripts/login-private-registry.sh [NAMEPACE]
```
