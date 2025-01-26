# About

Learning eBPF and the systems through eBPF lens at the same time.

# Experiments

## Hello World

basic hello world, just to setup the pipeline and build enviroment. Understanding basic moving parts.

## Noisy Neighbour

Following this article: https://netflixtechblog.com/noisy-neighbor-detection-with-ebpf-64b1f4b3bbdd
Learning more advanced eBPF programs and learning performance.

# Setup and Prerequisites

This project uses GKE cluster to deploy the eBPF programs to as a daemonset.
Access to a GCP project is required. GKE setup is outside of scope of this project.

# Build

Simple hello-world eBPF program can be built on local with `task local-build-push`.
However for more advanced programs a linux system might be required. This project uses [lima](https://lima-vm.io/) with QEMU, to start Lima instance run:

```terminal
task lima-start
```

In its current state the config is minimal, due to various errors, config clashes and other exciting problems, for now I've opted to run a startup script once bare minimum lima instance is up and running. [./lima-init.sh](./lima-init.sh). This script will install docker, taskfile and gcloud allowing to build and push from within lima instance. This can be simplified in the future, TODO markers explain how.

Configure docker auth for process inside lima instance and then build image

```terminal
# on local:
$ task docker-auth
$ limactl shell ebpf-dev

# inside lima:
$ task lima-build-push
```

This task will push image to GCP GAR and from there it can be deployed to a GKE cluster as described in section below

# GKE

```terminal
task deloy-k8s
```

# Cloud Run

Cloud Run does not officially support eBPF, and currently there is no public commitment to support it in the future:
https://issuetracker.google.com/issues/206477810?pli=1
