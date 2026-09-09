# eBPF Run-Queue Latency Analysis: Detecting Pod-to-Pod Starvation

**Updated 2026-09-09 — supersedes the original 8.3s findings below.** The initial write-up
(preserved further down, with corrections inline) concluded we'd measured an 8.3-second p99
run-queue latency spike caused by `bully-hog` starving `node-local-dns` and `netd`. That
number was wrong. It came from a real bug in our own instrumentation, not from anything
the Linux scheduler did. Full investigation trail: [`docs/latency-anomaly-investigation.md`](docs/latency-anomaly-investigation.md)
and [`run-results-2026-09-09.md`](run-results-2026-09-09.md).

## What we actually found

The `runq_enqueued` BPF map — which stores a wakeup timestamp per PID, deleted once that
PID is matched in `sched_switch` — leaked unboundedly, from the moment the collector
started, regardless of workload. A refactor had quietly rewritten `tp_sched_wakeup` from
`u64 *ctx` / `ctx[0]` to a plain `void *ctx`, dropping the array index into the tracepoint's
raw args. Every wakeup was then stored under a garbage key that `sched_switch` could never
match or clean up. Entries accumulated indefinitely (404 before any stressor was even
deployed, 3,746 by the end of a 90-minute session; ~99.5% stale in every sample); PID reuse
under load then let unrelated tasks "match" ancient orphaned timestamps, producing durations
with no relationship to real scheduling delay. The tell: the side-channel added to capture
the true unclamped maximum read **73 minutes** at one point — a single run-queue wait that
long is physically impossible under any scheduler, which is what confirmed this was an
instrumentation artifact rather than a real (if extreme) measurement.

The original 8.3s figure was a second, compounding issue on top of that: the histogram's
overflow bucket (everything ≥ 8.388608s, genuinely unbounded) was being clamped to a fake
finite boundary for Prometheus's sake, so `histogram_quantile` reported ~8.3s regardless of
whether the underlying (already-fabricated) values were 9 seconds or 90 minutes. Both bugs are fixed in the current source — `ctx[0]` restored in `tp_sched_wakeup`, a
`sched_process_exit` hook added to mop up orphaned entries, and the histogram's last bucket
now resolves honestly to `+Inf` instead of a fabricated ceiling — and the fix is now
**confirmed live and clean**, verified three independent ways: `runq_enqueued` reads 0-2
entries (snapshot noise, not backlog) at every checkpoint including after a full stress
run; a controlled idle-then-stress sequence showed no growth during a 90s idle window with
zero stressors running; and the one small residual anomaly in the raw BPF map (a handful of
multi-second-bucketed events, including some during pure idle) traced to
`system.slice/containerd.service` and the cgroup root itself — the node's own container
runtime, not a pod, not `bully-hog` — and every one of those events already gets filtered
out before export to Prometheus (`runqCollector.Collect()` only exports victims resolving
to `pod/*`), so it never reached the dashboard in the first place. Full verification trail:
[`run-results-2026-09-09.md`](run-results-2026-09-09.md#follow-up-verification-2026-09-09-later--leak-fix-confirmed-clean).

**The corrected p99 for pod-to-pod scheduling latency on this workload is genuinely clean —
dominated by sub-100ms events, with no evidence of real multi-second pod starvation.**

### What's confirmed, independent of the leak

- **CFS bandwidth throttling is ruled out** as a contributor — `container_cpu_cfs_throttled_periods_total`
  stayed flat at 0 for every pod on the test node pool across the full test window.
- **Hypervisor steal time is real but small** on this E2 node (~1-3% of a core under load)
  — present, as expected for GCP's dynamically-managed shared-core family, but nowhere near
  enough to explain multi-second figures.
- **PSI (`/proc/pressure/*`) attribution works cleanly** — disk and network stress each show
  up as pressure on exactly the right subsystem (`io` vs `cpu`/softirq) and exactly the
  right pod, both at node and cgroup scope.

### What's still open

The reason Track B (I/O and network stress) exists — testing whether kernel threads
(`kworker` writeback, `ksoftirqd`) rather than the noisy pod itself end up preempting the
victim under I/O pressure — is **untested, not disproven**. The victim pod carried no
traffic during the disk/network runs, so it had no runnable tasks to preempt and recorded
zero stall under both 97% node I/O pressure and 91% node CPU pressure. That experiment needs
a victim under real load before it says anything.

### On the original pod-to-pod attribution

One thing the leak does *not* corrupt: `cgroup` (victim) and `prev_cgroup` (preemptor) are
read live at the moment of each `sched_switch` event, not reconstructed from a stored
timestamp — so the original observation that `bully-hog` (`pod/84eabcd2/2f3ced60`) directly
preceded `node-local-dns` (`pod/8e08ef36/aef8d377`) and `netd` (`pod/a6e4f4c2/fb25610e`) in
the scheduling sequence during high-latency-flagged events is still a real, valid
observation — bully-hog genuinely was on the CPU immediately before those pods got their
turn. What's not trustworthy is *how long* those pods then waited; that part needs
re-measuring with the fixed collector before it belongs in a talk.

---

## Original write-up (2026-08-11), preserved for reference — see corrections above

This report details the findings from our eBPF noisy neighbor experiment on GKE. By leveraging eBPF tracepoints in the Linux scheduler, we captured evidence of a specific pod (`bully-hog`) directly preceding other pods in the scheduling sequence on the same node. **The severity and exact duration claimed below have since been retracted — see "What we actually found" at the top of this document.**

## The Linux Scheduler and Run-Queue Latency

To understand the metrics, we must briefly look at how the Linux scheduler (Completely Fair Scheduler - CFS, or the newer EEVDF) operates.

When a task (thread) is ready to execute, it transitions to a `TASK_RUNNING` state and is placed onto a CPU's **run queue**. **Run-queue latency** is the time difference between the moment a task enters the run queue and the moment the scheduler actually assigns it to a CPU core.

In a healthy system, this latency is typically in the order of microseconds to low milliseconds. High run-queue latency indicates CPU contention: there are more runnable tasks than available CPU cores, causing tasks to wait.

## eBPF Tracepoints: Catching the Thief

To measure this latency and identify the culprit, the eBPF program hooks into standard Linux kernel scheduler tracepoints:

1. **`sched_wakeup`**: Triggered when a task wakes up. The eBPF program records a timestamp for the task at this exact moment. *(Correction: `sched_wakeup_new` is not currently hooked — freshly forked/cloned tasks are not covered.)*
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

~~The eBPF metrics exported to Prometheus and visualized in Cloud Monitoring showed massive p99 run-queue latencies, peaking around **8.3 seconds**.~~ **Retracted — this was a fabricated value produced by a map-leak bug in the collector itself. See "What we actually found" above.**

By running `./list-cgroup-labels.sh`, we queried the kubelet to map the raw eBPF cgroup labels back to specific Kubernetes Pod and Container UIDs.

### The Noisy Neighbor
The dashboard legend consistently identified a specific cgroup acting as the `prev_cgroup` during flagged high-latency events:
* **cgroup path**: `pod/84eabcd2/2f3ced60`
* **Mapped Pod**: `bully-hog-5c687ff94c-gh5xl`

### The Starved Victims
We observed the following pods scheduled directly after `bully-hog` was preempted — the ordering is real (see "On the original pod-to-pod attribution" above); the previously-claimed wait durations are not:

1. **Victim 1: `node-local-dns`**
   * **cgroup path**: `pod/8e08ef36/aef8d377`
   * **Observation**: A direct edge (`pod/84eabcd2...` → `pod/8e08ef36...`) was recorded — `bully-hog` was on the CPU immediately before the local DNS cache daemon got scheduled. Wait duration: unverified, pending re-measurement.

2. **Victim 2: `netd` (GKE Networking Daemon)**
   * **cgroup path**: `pod/a6e4f4c2/fb25610e`
   * **Observation**: Similarly, an edge (`pod/84eabcd2...` → `pod/a6e4f4c2...`) was recorded. Wait duration: unverified, pending re-measurement.

## Conclusion

The eBPF instrumentation proved its value by moving beyond generic "node-level CPU usage" metrics — tracing `sched_switch` and correlating `prev` and `next` cgroups gives direct evidence of *which* pod preceded *which* on the CPU, something node-level metrics can't show.

It also, less comfortably, proved its own fallibility: the headline latency number from this
same instrumentation was wrong, and only caught because a follow-up re-investigation
insisted on cross-checking it rather than taking a plausible-looking `histogram_quantile`
result at face value. That's arguably the more useful finding to carry into the talk — not
"here is 8.3 seconds of starvation," but "here is how you catch your own tool lying to you."
