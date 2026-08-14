Here is a step-by-step implementation plan to take your existing eBPF code, package it, run synthetic load tests on your dedicated `e2-standard-2` GKE node pool, and visualize the run-queue contention.

---

## Phase 1: Package & Deploy the eBPF Collector

DONE.

---

## Phase 2: Deploy Test Workloads to Dedicated Node

Select one specific `e2-standard-2` node in your dedicated node pool and isolate your experiment onto it using labels and node selectors.

### 1. Target Node Pool Selection

Ensure nodes in the nodepool have the following label and taint (or applied to your target test node):

```bash
kubectl label node <YOUR_TEST_NODE_NAME> workload=noisy-node
kubectl taint node <YOUR_TEST_NODE_NAME> dedicated=noisy-node:NoSchedule
```

### 2. Deploy the "Victim" (API Service) (`victim-api.yaml`)

A lightweight web server with explicit CPU requests and limits.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: victim-api
spec:
  replicas: 1
  selector:
    matchLabels:
      app: victim-api
  template:
    metadata:
      labels:
        app: victim-api
    spec:
      nodeSelector:
        workload: noisy-node
      tolerations:
      - key: "dedicated"
        operator: "Equal"
        value: "noisy-node"
        effect: "NoSchedule"
      containers:
      - name: api
        image: hashicorp/http-echo:latest
        args: ["-text=hello-from-victim"]
        ports:
        - containerPort: 5678
        resources:
          requests:
            cpu: "200m"
            memory: "128Mi"
          limits:
            cpu: "1000m"
            memory: "256Mi"

```

---

### 3. Deploy the "Bully" (CPU Hog) (`bully-hog.yaml`)

A 2-worker stress process designed to occupy **both vCPUs** on the `e2-standard-2` instance without setting CPU limits.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bully-hog
spec:
  replicas: 1
  selector:
    matchLabels:
      app: bully-hog
  template:
    metadata:
      labels:
        app: bully-hog
    spec:
      nodeSelector:
        workload: noisy-node
      tolerations:
      - key: "dedicated"
        operator: "Equal"
        value: "noisy-node"
        effect: "NoSchedule"
      containers:
      - name: stress
        image: alexeiled/stress-ng:latest
        args:
        - "--cpu"
        - "2"                  # Matches 2 vCPUs on e2-standard-2
        - "--cpu-method"
        - "matrixprod"
        resources:
          requests:
            cpu: "100m"        # Minimum request to get scheduled easily
          # DO NOT SET CPU LIMITS: allows it to consume all unallocated core time

```

---

### 4. Deploy the Load Generator (`fortio-job.yaml`)

Run `fortio` on a **different node** (or target locally via `kubectl port-forward`) so its traffic generation overhead does not distort the test node's run-queue metrics.

```bash
kubectl port-forward svc/victim-api 5678:5678 &
fortio load -c 10 -qps 100 -t 60s http://localhost:5678/

```

---

## Phase 3: Execution & Metric Verification Strategy

> [!IMPORTANT]
> **Kernel Filter Awareness:** Your eBPF kernel code drops all events where $\text{runq\_lat} < 1\text{ ms}$ (`MIN_RUNQ_LAT_NS = 1_000_000`). Under normal, non-saturated cluster conditions, run-queue delays are in microseconds, so **the eBPF map will be empty until the Bully is actively saturating the CPU cores.**

### Step-by-Step Test Sequence

| Phase | Actions | Expected Standard K8s Dashboard (`kubectl top`) | Expected eBPF Dashboard |
| --- | --- | --- | --- |
| **1. Baseline** | Run `fortio` against `victim-api` **without** `bully-hog` active. | `victim-api` CPU usage: ~5%. All node cores healthy. | **Empty/Zero events** (Run-queue latency $< 1\text{ ms}$ filtered out). |
| **2. Attack** | Deploy `bully-hog` (2 workers) + run `fortio` against `victim-api`. | `victim-api` CPU usage remains low (~5%). `cfs_throttled_seconds` = 0. | **Spike in Run-Queue Latency** ($\ge 10\text{ms} - 50\text{ms}$). Prometheus histograms populate. |
| **3. Verification** | Query Prometheus / Grafana for `prev_cgroup` on elevated latency buckets. | Shows zero correlation to pod performance drops. | Identifies `pod/<bully-pod-uid>` as the direct `prev_cgroup` causing preemption. |

---

## Phase 4: PromQL Dashboard Queries

When sending metrics to Prometheus/Cloud Monitoring, use these PromQL expressions to build your dashboard panels.

### 1. Overall p99 Run-Queue Latency by Victim Pod

Calculates the 99th percentile scheduling delay experienced by pods in milliseconds:

```promql
histogram_quantile(
  0.99,
  sum(rate(ebpf_runq_latency_nanoseconds_bucket[2m])) by (le, cgroup)
) / 1000000

```

### 2. Identify the Noisy Neighbor (`prev_cgroup` Attributed Latency)

Shows which cgroup was executing when your target victim pod suffered run-queue latency:

```promql
sum(rate(ebpf_runq_latency_nanoseconds_bucket{cgroup=~"pod/.*"}[2m])) by (cgroup, prev_cgroup)

```

---

## Phase 5: Troubleshooting & Verification Checklist

1. **Unresolved Cgroup Names (`unresolved` in metrics):**
* *Cause:* GKE container runtime (`containerd`) packs generation numbers into `kernfs_node.id` upper 32 bits.
* *Fix:* Ensure your Go `cgroupMapper` performs the bitwise AND operation (`id & 0xFFFFFFFF`) as documented in your section 4.1.


2. **Metrics Show No Events During Load:**
* *Cause:* The `bully-hog` has fewer worker threads than node vCPUs, leaving an idle vCPU core for `victim-api`.
* *Fix:* Verify that `stress-ng` `--cpu` parameter strictly matches or exceeds the node's vCPU count (`nproc`).


3. **High Overhead / Dropped Events:**
* *Cause:* BPF maps filling up due to excessive low-latency scheduling churn.
* *Fix:* Keep `MIN_RUNQ_LAT_NS` at `1_000_000` ($1\text{ ms}$) in kernel space to ensure short context switches are discarded instantly at the probe level.
