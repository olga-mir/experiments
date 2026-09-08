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

## Confine the experiment to one CPU (static CPU Manager + ballast)

The `test-pool` node pool (`e2-standard-2` = 2 vCPU) is created with kubelet
`cpuManagerPolicy: static` via `--system-config-from-file` — see
[`gke-node-system-config.yaml`](./gke-node-system-config.yaml), wired into
[`provision.sh`](./provision.sh). Under the static policy, a **Guaranteed-QoS**
pod that requests an **integer** number of CPUs is handed those cores
*exclusively*; they leave the shared pool that every other pod runs in.

[`k8s/ballast.yaml`](./k8s/ballast.yaml) is a do-nothing `pause` DaemonSet
requesting exactly `cpu: "1"` (request == limit for cpu and memory → Guaranteed).
It parks one whole core per node, leaving `bully-hog`, `victim-api`, the eBPF
collector and the kube-system DaemonSets to contend over the **one remaining
core**.

```bash
task deploy-ballast          # or: kubectl apply -f k8s/ballast.yaml
```

Deploy it *before* the experiment workloads so the core is fenced off first.

### Verify the core was actually pinned

```bash
# QoS class must be Guaranteed
kubectl get pod -l app=ballast -o jsonpath='{.items[0].status.qosClass}{"\n"}'

# kubelet CPU-manager state on the test node: defaultCpuSet (the shared pool)
# should collapse to a single CPU id; the ballast container maps to the other.
TEST_NODE=$(kubectl get pod -l app=ballast -o jsonpath='{.items[0].spec.nodeName}')
kubectl debug node/"$TEST_NODE" -it --image=busybox -- \
  cat /host/var/lib/kubelet/cpu_manager_state
```

Expected shape on `e2-standard-2`:

```json
{
  "policyName": "static",
  "defaultCpuSet": "0",
  "entries": { "<ballast-pod-uid>": { "ballast": "1" } }
}
```

If you change the node machine type, set the ballast `cpu` request to
`(node vCPUs − 1)` to keep the experiment on a single core.

## Generate load to create noisy neighbor pressure

### Option A — self-contained cpu-stressor DaemonSet (quickest)

Deploys `stress-ng` on every node. No other service needed.

```bash
kubectl apply -f k8s/cpu-stressor.yaml
kubectl top pods -l app=cpu-stressor   # confirm ~1–2 cores burning per node
```

Dashboard shows activity within ~1 minute (next scrape + 5 s poll).

Clean up when done:
```bash
kubectl delete -f k8s/cpu-stressor.yaml
```

**Why the CPU request is 10m:** the dev cluster nodes are 2-vCPU and nearly fully booked by system pods. The request only affects scheduling; the limit (4 CPU) is what stress-ng actually races for, which is what drives run-queue contention.

### Option B — perf-lab

If `perf-lab` is deployed, hit its CPU endpoint to saturate one replica's node:

```bash
# sustained CPU load — adjust QPS/duration to taste
fortio load -qps 50 -t 120s http://<perf-lab-svc>/cpu?iterations=100000

# fanout scenario spawns goroutines and creates scheduling churn
fortio load -qps 20 -t 120s http://<perf-lab-svc>/fanout?workers=20
```

## View in Cloud Monitoring

Import `gcp-dashboard.json` into Cloud Monitoring → Dashboards. The dashboard requires two filters to be set before data appears:

- **ebpf_node** — the eBPF DaemonSet pod name (one per node). Scopes all charts to a single node; mixing nodes makes the data unreadable since scheduling is per-node.
- **cgroup_pod** — (Noisy Neighbour section only) the victim pod to investigate, in `pod/<uid-prefix>/<cid-prefix>` form.

To find a pod's cgroup label:
```bash
kubectl get pod <name> -o jsonpath='{.metadata.uid}' | cut -c1-8
# use result as uid-prefix in pod/<uid-prefix>
```

Key metrics:
- `ebpf_runq_latency_nanoseconds` — run-queue latency histogram, labelled by `cgroup` (scheduled pod) and `prev_cgroup` (pod it preempted). Buckets cover 1µs–8s.
- `ebpf_events_total` — confirms data is flowing from the eBPF ring buffer.

Dashboard panels use `histogram_quantile` over PromQL — not the raw histogram aggregation — to get accurate p50/p99 percentiles. Example noisy-neighbour query (who is preempting pod X?):
```promql
histogram_quantile(
  0.99,
  sum by (prev_cgroup, le) (
    rate(ebpf_runq_latency_nanoseconds_bucket{pod=~"<ebpf-pod>", cgroup=~"pod/<uid>/.*"}[5m])
  )
) / 1e6
```

## Outcomes

I've documented some learnings in [./outcomes](./outcomes) folder.

The project builds, deploys to GKE as a daemonset, collects run-queue latency data in eBPF maps, and exports it as Prometheus metrics via a ring buffer consumer in the Go userspace program.
![Setup works – proof of concept](outcomes/gcp-dashboard-noisy-neighbour.png)

*Note: this is in progress, but this is proof that the setup works and more analysis will follow soon.*

# Note on Cloud Run

Cloud Run was considered as a deployment target early on. It does not support eBPF and there is no public commitment to add support:
https://issuetracker.google.com/issues/206477810
