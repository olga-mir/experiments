# About

Learning eBPF and the systems through eBPF lens at the same time.

# Experiments

## Hello World

basic hello world, just to setup the pipeline and build enviroment. Understanding eBPF basics. [./bpf-snippets](./bpf-snippets/)

## Noisy Neighbour

Following this article: https://netflixtechblog.com/noisy-neighbor-detection-with-ebpf-64b1f4b3bbdd
Learning more advanced eBPF programs and learning performance.

This article provides full eBPF code, however reading results and exporting them as a metrics to your own system is not covered.
This is the next step of this experiment.

# Setup and Prerequisites

This project uses GKE cluster to deploy the eBPF programs to as a daemonset.
Access to a GCP project is required. GKE setup is outside of scope of this project.

# Build

Simple hello-world eBPF program can be built on local with `task local-build-push`.
However for more advanced programs a linux system might be required. This project uses [lima](https://lima-vm.io/) with QEMU, to start Lima instance run:

```terminal
task lima-start
```

In its current state, lima config is minimal. This is to due to various errors when provisioning all the required tools during boot. For now tools are installed using [./lima-init.sh](./lima-init.sh) after the instance is running. This script will install docker, taskfile and gcloud allowing to build and push from within lima instance. This can be simplified in the future, TODO markers explain how.

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

To explore eBPF on the host direclty is challenging in GKE because (rightfully so) there is no `apt` or `make`. It should be possible to download `bpftool` with `curl` but it would require building it from source to target COS env somehere which is not COS.

It is a lot easier to run `bpftool` in another container inside a priviledged pod. Technically would be even easier to have it in the app image itself, less secure.

Install `pbftool` for exploration:
```
k apply -f k8s/bpftool-daemonset.yaml
```

The cluster already has GKE Managed Prometheus running — playground-sre has a PodMonitoring and uses it. So the infra is ready.

## Deploy eBPF daemonset to GKE Cluster

These steps use infrastructure from  and workloads from

Deploy Daemonset with image built in previous step. This image is a go userspace program that loads eBPF program:

```
task lima-build-image   # or local-build-image if cross-compile works for you
task deploy-k8s
task deploy-monitoring  # deploys pod-monitoring.yaml
```

When this is proved working, this can be integrated into the playground projects.

## Generate load with perf-lab to create noisy neighbor pressure

`perf-lab` already has scenarios implemented. Hit the CPU endpoint on one replica — that saturates CPU time on the node and causes run-queue latency for everything else sharing that node:

```
# sustained CPU load — adjust QPS/duration to taste
fortio load -qps 50 -t 120s http://<perf-lab-svc>/cpu?iterations=100000

# or the fanout scenario which spawns goroutines and creates scheduling churn
fortio load -qps 20 -t 120s http://<perf-lab-svc>/fanout?workers=20
```

If fortio isn't deployed separately, perf-lab itself can be the source since it has the CPU scenario built in — two concurrent load patterns on the same node are enough to see the effect.

## View in Cloud Monitoring

Metrics Explorer → query:
- `prometheus.googleapis.com/ebpf_runq_latency_nanoseconds/histogram`: group by cgroup to see which pods are experiencing the most scheduling delay
- `prometheus.googleapis.com/ebpf_events_total`: confirms data is flowing

The cgroup labels will look like `pod/abc12345/cri12345` (pod-uid prefix + container-id prefix).

## Outcomes

I've documented some learnings in [./outcomes](./outcomes) folder.

Currently this project successfully builds, deploys to k8s environment and collects data in eBPF maps. There is no user-space code yet that reads this data and exports this as metrics. This is WIP.


# Cloud Run

Cloud Run does not officially support eBPF, and currently there is no public commitment to support it in the future:
https://issuetracker.google.com/issues/206477810?pli=1
