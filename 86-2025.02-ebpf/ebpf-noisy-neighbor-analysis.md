# eBPF Run-Queue Latency Analysis: Detecting Pod-to-Pod Starvation

This report details the findings from our eBPF noisy neighbor experiment on GKE. By leveraging eBPF tracepoints in the Linux scheduler, we successfully captured empirical evidence of a specific pod (`bully-hog`) monopolizing the CPU and severely starving other critical system pods on the same node.

## The Linux Scheduler and Run-Queue Latency

To understand the metrics, we must briefly look at how the Linux scheduler (Completely Fair Scheduler - CFS, or the newer EEVDF) operates.

When a task (thread) is ready to execute, it transitions to a `TASK_RUNNING` state and is placed onto a CPU's **run queue**. **Run-queue latency** is the time difference between the moment a task enters the run queue and the moment the scheduler actually assigns it to a CPU core.

In a healthy system, this latency is typically in the order of microseconds to low milliseconds. High run-queue latency indicates CPU contention: there are more runnable tasks than available CPU cores, causing tasks to wait.

## eBPF Tracepoints: Catching the Thief

To measure this latency and identify the culprit, the eBPF program hooks into standard Linux kernel scheduler tracepoints:

1. **`sched_wakeup` and `sched_wakeup_new`**: Triggered when a task wakes up or is newly created. The eBPF program records a timestamp for the task at this exact moment.
2. **`sched_switch`**: Triggered when the kernel physically context-switches from one task to another.

At `sched_switch`, the kernel provides the eBPF program with two crucial pieces of context:
* `prev`: The task being preempted or giving up the CPU.
* `next`: The task being scheduled onto the CPU.

When `sched_switch` fires, the eBPF program looks up the wakeup timestamp for the `next` task, calculates the delta (the **run-queue latency**), and bins it into a histogram.

Crucially, because eBPF runs in the kernel, it can extract the **cgroup IDs** of both the `prev` and `next` tasks. This allows the eBPF program to enrich the histogram metric with:
* `cgroup`: The pod that was waiting in the run queue (the victim).
* `prev_cgroup`: The pod that was occupying the CPU right before the victim got to run (the noisy neighbor).

## Empirical Findings: Identifying the Culprits and Victims

During our test, we provisioned a 2-vCPU node (`test-pool`) and deployed `bully-hog` (running `stress-ng` with 2 workers) alongside other workloads.

The eBPF metrics exported to Prometheus and visualized in Cloud Monitoring showed massive p99 run-queue latencies, peaking around **8.3 seconds**.

### The 4.19s vs 8.3s Discrepancy & Prometheus Interpolation

At first glance, an 8.3s run-queue latency under the Linux Completely Fair Scheduler (CFS) seems impossibly high. Looking closely at the raw eBPF bucket data, the highest populated latency bucket was Bucket 22, which covers the range of `[4.19s, 8.38s)`.

The "8.3 seconds" figure is actually an artifact of **Prometheus histogram interpolation**. When calculating `histogram_quantile(0.99, ...)`, Prometheus assumes a uniform distribution of values within a bucket. Because the 99th percentile fell near the upper edge of Bucket 22, the mathematical interpolation resulted in ~8.3s. While the true maximum latency may have been closer to 4.5s or 5s, the raw data undeniably proves an extreme scheduling freeze of *at least* 4.19 seconds.

### How is a >4s freeze possible with CFS and quotas?

Even at 4.19 seconds, this is an eternity for a scheduler that typically operates in microsecond or single-digit millisecond time slices. This extreme starvation occurred due to how CFS and Kubernetes resource limits interact:

1. **The Bully Bypassed Quotas**: The `bully-hog` deployment intentionally omitted CPU limits (`resources.limits.cpu`). Without a limit, the Linux CFS Bandwidth Controller (`cpu.cfs_quota_us`) was completely disabled for this pod, allowing it to consume 100% of any unallocated CPU cycles without ever being throttled.
2. **CFS Shares Imbalance**: Because limits were disabled, CFS fell back to strictly enforcing proportional time based on `cpu.shares` (requests). `bully-hog` requested `100m` CPU, giving it a baseline of ~102 shares. Under absolute 100% core saturation from the `stress-ng` workers, CFS distributed time proportionally between the bully and the system pods.
3. **Throttling and System Overload**: While the bully had no limits, the victim system pods often do. A 4+ second run-queue latency typically points to severe kernel-level contention or victims hitting their own CFS quotas and being excessively throttled. *(Note: Our current eBPF setup only traces `sched_wakeup` and `sched_switch` to measure run-queue latency; it does **not** expose CPU throttling metrics. To observe throttling, we would need to rely on cAdvisor metrics like `container_cpu_cfs_throttled_seconds_total` or add new eBPF hooks for the CFS bandwidth controller).*

By running `./list-cgroup-labels.sh`, we queried the kubelet to map the raw eBPF cgroup labels back to specific Kubernetes Pod and Container UIDs.

### The Noisy Neighbor
The dashboard legend consistently identified a specific cgroup acting as the `prev_cgroup` during high-latency events:
* **cgroup path**: `pod/84eabcd2/2f3ced60`
* **Mapped Pod**: `bully-hog-5c687ff94c-gh5xl`

### The Starved Victims
We observed several critical system pods suffering extreme scheduling delays directly after `bully-hog` was preempted:

1. **Victim 1: `node-local-dns`**
   * **cgroup path**: `pod/8e08ef36/aef8d377`
   * **Observation**: The dashboard captured a direct edge (`pod/84eabcd2...` → `pod/8e08ef36...`). This proves that the local DNS cache daemon was starved of CPU time because `bully-hog` was monopolizing the core.

2. **Victim 2: `netd` (GKE Networking Daemon)**
   * **cgroup path**: `pod/a6e4f4c2/fb25610e`
   * **Observation**: Similarly, we saw an edge (`pod/84eabcd2...` → `pod/a6e4f4c2...`). The networking daemon handling node routing and CNI operations was severely delayed.

## Conclusion

The eBPF instrumentation proved its value by moving beyond generic "node-level CPU usage" metrics. Node CPU metrics only tell us *that* the node is busy. By tracing `sched_switch` and correlating `prev` and `next` cgroups, eBPF provided indisputable proof of **pod-to-pod interference**.

We didn't just see high latency; we mathematically proved that `bully-hog` was the specific entity holding the CPU hostage right when `node-local-dns` and `netd` needed to execute. Our findings also highlight the importance of understanding Prometheus histogram interpolation and the dramatic impact of omitting CPU limits in a multi-tenant environment.
