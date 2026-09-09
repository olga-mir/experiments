# Run results — Track A (CPU re-run) + Track B (I/O / network), 2026-09-09

First live run of the instrumentation added in
[`docs/latency-anomaly-investigation.md`](docs/latency-anomaly-investigation.md) §1–§5
(the two feature branches, now merged onto `deep-dive-ebpf`). Goal: decide whether the
original **"p99 run-queue latency ≈ 8.3 s"** headline in
[`ebpf-noisy-neighbor-analysis.md`](ebpf-noisy-neighbor-analysis.md) is a real measurement.

All times **UTC** (add 10 h for AEST / Sydney). Cluster `experiment-ebpf-cluster`
(`${PROJECT_ID}`, `australia-southeast1-a`). Single test node
`gke-experiment-ebpf-cluster-test-pool-5a54a179-qgvr` — `e2-standard-2` (2 vCPU),
kernel `6.12.94+`, COS, `cpuManagerPolicy: static`.

---

## TL;DR

| Question | Answer from this run |
|---|---|
| Is the 8.3 s p99 a real scheduling delay? | **No.** It is a `runq_enqueued` map-leak + PID-reuse artefact (§4 confirmed). |
| Does `runq_enqueued` leak? | **Yes, unbounded, from collector start.** 404 → 3 746 entries, ~99.5 % of them stale, oldest entry 82 min old and growing linearly with wall-clock. Workload type only changes the *fill rate*, never the direction. |
| Does the "honest ceiling" side-channel help? | It correctly stops fabricating a finite 8.39 s number, but `ebpf_runq_latency_max_nanoseconds` is itself poisoned by the same leak — it read **73 minutes** by end of run. Both signals need the leak fixed before either can be trusted. |
| CFS bandwidth throttling (§2)? | Still ruled out — unchanged from the earlier Metrics-Explorer check. |
| Hypervisor steal time (§3)? | **Present but small** on this E2 node: ~1–3 % of a core during load. A minor contributor, not the mechanism. |
| Does the kernel-thread / writeback / softirq preemption theory (Track B's purpose) hold? | **Untested — experiment gap.** The victim pod runs no workload, so it has no runnable tasks to preempt and registered exactly zero stall under every stressor. See "Gaps". |
| Does PSI attribution work? | **Yes, cleanly.** Node- and cgroup-scope PSI tracked each stressor to its subsystem and its pod in real time. |

---

## Timeline

| UTC | Event | Notes |
|---|---|---|
| ~23:31:28 | `ebpf-ds` collector (`ebpf-ds-m4z4j`) started | inferred from oldest map entry age |
| 23:38:51 | `ballast` + `victim-api` deployed | baseline; ballast pins cpu1 exclusively, everything else shares cpu0 |
| 23:41:52 | first probe line captured | already **404** map entries, oldest **625 s** old — leak is pre-existing, not load-induced |
| **23:47:20** | **`bully-hog` (CPU) START** | `stress-ng --cpu 2 --cpu-method matrixprod`, no CPU limit |
| ~00:06:45 | `bully-hog` STOP | ran ~19.4 min |
| **00:06:56** | **`bully-io` (disk) START** | `stress-ng --hdd 2 --hdd-bytes 512m --iomix 2` into 8 Gi `emptyDir` |
| 00:48:11 | `bully-io` STOP | ran ~41.3 min |
| **00:48:56** | **`bully-net` (network) START** | `stress-ng --sock 4 --udp 2` over loopback |
| 00:54:17 | end snapshot taken | `bully-net` still running at time of writing |

Stressors were run **one at a time** as the Track B docs require. `bully-hog` was
deleted before `bully-io` and `bully-io` before `bully-net` so each subsystem's PSI
signal is unambiguous.

---

## Track A — CPU re-run (`bully-hog`, 23:47:20 → ~00:06:45)

### §4 `runq_enqueued` leak — CONFIRMED

The collector's own probe (`debug.go` / `watchRunqEnqueued`, logged every 5 s and
exported as gauges) shows the exact signature §4 predicted:

| UTC | phase | `entries` | `stale(>10s)` | `max_age_s` | `raw_max` |
|---|---|--:|--:|--:|--:|
| 23:41:52 | collector +10 min, pre-bully | 404 | 401 | 625 | 2m41s |
| 23:47:42 | bully-hog +22 s | 540 | 529 | 975 | 2m41s |
| 23:48:08 | bully-hog +48 s | 548 | 544 | 1 000 | **11m42s** |
| 00:06:03 | bully-hog +19 min | 851 | 846 | 2 075 | 26m39s |
| 00:47:52 | (disk run) +41 min | 3 050 | 3 042 | 4 585 | 52m40s |
| 00:54:13 | (net run) +5 min | 3 746 | 3 732 | 4 965 | **1h13m28s** |

- **Monotonic growth from t=0.** The map had 404 entries and a 625 s-old oldest entry
  *before `bully-hog` was deployed*. It never shrinks. This matches the year-old note in
  `outcomes/step01-exploring-loaded-ebpf-program.md` ("this map constantly growing").
- **~99.5 % of entries are stale** (older than 10 s) in every sample — essentially every
  entry is an orphan: a wakeup timestamp written by `sched_wakeup` whose task was never
  matched as `next` in `sched_switch`.
- **`max_age_seconds` grows 1:1 with wall-clock** — 625 → 4 965 s over the same 72 min of
  real time. The oldest entry is never evicted.
- **PID reuse then reads those orphans as latency.** `ebpf_runq_latency_max_nanoseconds`
  (the Track A "true max" side-channel, `runq_lat_max` BPF map) climbed
  2m41s → 11m42s → 26m39s → 52m40s → **1h13m28s**. A single run-queue-latency sample of
  73 minutes is physically impossible under any scheduler; it is `now − <stale orphan
  timestamp from an unrelated earlier task that had this PID>`.

**Verdict:** the original 8.3 s p99 is this artefact. The BPF histogram's overflow bucket
(≥ 2^23 µs = 8.388608 s, unbounded) collected these fabricated multi-minute deltas, and the
old collector clamped that bucket to a finite `le = 8.388608 s`, so `histogram_quantile`
reported ~8.3 s. Nothing on this node ever actually waited 8 s on the run queue.

### §1 histogram ceiling — fix works, but the input is still poisoned

The merged-overflow-into-finite-`le` clamp is gone (overflow now counts only toward
`_count` / implicit `le="+Inf"`). That is the correct change — a p99 that ranks into the
unbounded region now resolves to `+Inf` instead of a fake 8.39 s. But until the §4 leak is
fixed, both the `+Inf` tail and `ebpf_runq_latency_max_nanoseconds` are dominated by
orphan reads, so neither yet gives a trustworthy ceiling. **Fix §4 first, then re-read.**

### §2 CFS bandwidth throttling — still ruled out

No new data needed; the earlier `container_cpu_cfs_throttled_periods_total` check (flat 0
for every pod on the `test` pool across the original window) stands. Nothing in this run
contradicts it.

### §3 hypervisor steal time — present, small

`node-exporter` (`task deploy-node-exporter`) is now scraping the test node. 30 s sample
during the network run:

| cpu | steal Δ over 30 s | ≈ % of one core |
|---|--:|--:|
| cpu0 (shared) | +0.84 s | 2.8 % |
| cpu1 (ballast) | +0.35 s | 1.2 % |

Non-zero — E2 is GCP's shared/dynamically-managed family and this is expected — but
~1–3 % of a core cannot produce multi-second latency. Steal time is a **minor background
contributor, not the mechanism**. Worth keeping the node-exporter scrape for future runs.

---

## Track B — disk run (`bully-io`, 00:06:56 → 00:48:11, ~41 min)

`stress-ng` reported `dispatching hogs: 2 hdd, 2 iomix`. Node CPU utilisation *dropped*
55 % → ~11 % (not CPU-bound, as intended). End-of-run PSI (`avg10`):

| scope | io `some` | io `full` | cpu `some` |
|---|--:|--:|--:|
| **node** | 97.2 % | 87.2 % | 6.3 % |
| **`bully-io`** `pod/61326982` | 99.1 % | 88.3 % | 8.4 % |
| **`victim-api`** `pod/182d9931` | **0 %** | 0 % | **0 %** |

`ebpf_psi_stall_seconds_total` over the run: node io `full` +2 073 s (≈ 85 % of wall-clock
with *all* tasks I/O-stalled), `bully-io` io `some` +2 417 s. `victim-api` io stall total:
**+0.0 s** (frozen at 0.45 ms lifetime).

**Reading:** PSI cleanly attributes a node-wide block-layer stall to the disk bully. The
disk leak fill-rate roughly tripled vs the CPU run (~0.28 → ~0.84 entries/s) — I/O
completions and writeback kworkers generate more wakeups — but still monotonic.
The victim was completely unaffected (see Gaps).

---

## Track B — network run (`bully-net`, 00:48:56 → ongoing)

`stress-ng` reported `dispatching hogs: 4 sock, 2 udp`. `bully-net` burns ~0.94 core;
node CPU utilisation ~61 %. After ~6 min soak, PSI:

| scope / window | cpu `some` | cpu `full` | io `some` |
|---|--:|--:|--:|
| **node** avg10 | 91.0 % | 0 % | 1.1 % |
| **node** avg60 | 89.7 % | 0 % | 1.7 % |
| **`bully-net`** `pod/c3a889f2` avg10 | 99.4 % | 3.9 % | 0 % |
| **`victim-api`** `pod/182d9931` avg10 | **0 %** | 0 % | 0 % |

`softirq` CPU time on the node ran ~7–10 % during the window (`node_cpu_seconds_total{mode="softirq"}`),
consistent with `NET_RX` / `ksoftirqd` load from the loopback packet rate. Node cpu `some`
stall counter +293 s over ~6.5 min (≈ 75 % of wall-clock with ≥ 1 task CPU-stalled), of
which `bully-net`'s own `some` cpu stall is +320 s — i.e. the stalled task is the bully
itself. `victim-api` cpu stall total: **+0.0 s**.

**Reading:** the network stressor shows up as *CPU* pressure (softirq stealing cycles),
not I/O pressure — exactly the distinction Track B was built to surface. Node vs cgroup PSI
correctly separates "the node is contended" from "this pod is the cause".

---

## Gaps — what this run could NOT establish

1. **The writeback / softirq preemption theory (§5, Track B's whole point) is still
   untested.** `victim-api` is `hashicorp/http-echo` with **no client traffic** — it has
   essentially no runnable tasks, so nothing can preempt it and it recorded exactly zero
   PSI stall and zero run-queue impact under all three stressors, even with the node at
   97 % I/O pressure or 91 % CPU pressure. A pod that never runs cannot be starved.
   *To actually test §5:* drive the victim with sustained load (`fortio load` against
   `victim-api:5678`, or swap in a victim that does periodic CPU + disk work), then check
   whether `prev_cgroup` on its delayed `ebpf_runq_latency_nanoseconds` events shows
   `root` / `system.slice/*` (kworker, `ksoftirqd`, `wb_workfn`).
2. **`prev_cgroup` attribution not inspected.** That check needs a PromQL query against
   GKE Managed Prometheus / the Cloud Monitoring dashboard (with the `prev_cgroup` filter
   *widened* to include `root` / `system.slice/*`), which isn't reachable from the run
   host. The collector emits `prev_cgroup` unfiltered, so the data is in Prometheus for
   whoever opens the dashboard.
3. **`task dump-runq-enqueued` is broken** — two independent bugs, pre-existing:
   - `k8s/bpftool-daemonset.yaml` has **no toleration** for the test node's
     `dedicated=noisy-node:NoSchedule` taint and **no `nodeSelector`**, so its one pod
     lands on `default-pool`, never on the test node the dump script targets.
   - That pod is also in `CrashLoopBackOff` — its entrypoint builds `bpftool` from source
     and fails: `sign.c:16:10: fatal error: openssl/opensslv.h: No such file or directory`.
   The collector's own `ebpf_runq_enqueued_*` gauges + probe log cover the same §4
   evidence, so this didn't block the verdict, but the raw map dump cross-check is still
   owed. Fix: add the toleration + `nodeSelector: {workload: noisy-node}` to the bpftool
   DaemonSet and use a prebuilt `bpftool` image (or install `libssl-dev` / drop `sign.o`).

---

## Recommended next actions

1. **Fix the §4 leak** and re-run — this is now the critical path, everything else is
   downstream of it:
   - hook `sched_process_exit` to delete the entry when a task dies, **and/or**
   - key `runq_enqueued` on `pid + task start-time` (`BPF_CORE_READ(task, start_time)`)
     instead of `pid` alone.
   After the fix, `entries` should track the count of *currently runnable* tasks (tens,
   not thousands) and `max_age` should stay sub-second.

   **Root cause found + fixed (2026-09-09, commits follow this report):** not PID reuse —
   a refactor (`03888db`) had rewritten `tp_sched_wakeup` from `u64 *ctx` /
   `(void *)ctx[0]` to `void *ctx` / `(struct task_struct *)ctx`, dropping the `[0]`
   index into the `tp_btf` args array. Every `sched_wakeup` then stored `runq_enqueued`
   under a garbage key that `sched_switch` (still correctly using `ctx[2]`) could never
   match or delete → unbounded growth, ~99 % stale, fabricated multi-second latencies.
   Fix restores `ctx[0]` in `tp_sched_wakeup` and adds a `sched_process_exit` mop-up
   hook. Built, pushed, deployed; verification in progress. See
   `docs/latency-anomaly-investigation.md` §4 "Root cause found".
2. **Re-read the ceiling** once (1) is done: `histogram_quantile(0.99, …)` and
   `ebpf_runq_latency_max_nanoseconds` for the CPU run. Expectation: low-ms p99, and the
   "8.3 s" story is retired for the talk (replace with "our first number was an
   instrumentation bug — here's how eBPF let us catch it").
3. **Give the victim a real workload** and re-run disk + network with `prev_cgroup`
   widened on the dashboard, to finally test §5.
4. Fix `k8s/bpftool-daemonset.yaml` (toleration + selector + prebuilt image) so the raw
   map dump is available as a cross-check.
5. Decide whether `bully-net` stays up — it's still running and the leak is still growing
   while it is. `kubectl delete -f k8s/bully-net.yaml` when done inspecting the dashboard.

---

## Appendix — dashboard filters for this run

- `ebpf_node` = `ebpf-ds-m4z4j`
- victim (`cgroup_pod`) = `pod/182d9931`
- `bully-hog` (`prev_cgroup`) = `pod/31a344ff`  *(deleted)*
- `bully-io` (`prev_cgroup`) = `pod/61326982`  *(deleted)*
- `bully-net` (`prev_cgroup`) = `pod/c3a889f2`

Steal-time check query: `rate(node_cpu_seconds_total{mode="steal"}[5m])` on the test node.
