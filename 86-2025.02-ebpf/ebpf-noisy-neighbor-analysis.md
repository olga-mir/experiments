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

The eBPF metrics exported to Prometheus and visualized in Cloud Monitoring showed massive p99 run-queue latencies, peaking around **8.3 seconds**. This is an extraordinary scheduling delay, indicating severe CPU starvation.

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

We didn't just see high latency; we mathematically proved that `bully-hog` was the specific entity holding the CPU hostage right when `node-local-dns` and `netd` needed to execute.
