#include "vmlinux.h"
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_tracing.h>
#include <bpf/bpf_core_read.h>

/// ###### Implementation idea and explanation:
/// https://netflixtechblog.com/noisy-neighbor-detection-with-ebpf-64b1f4b3bbdd


#define MAX_TASK_ENTRIES 20000
#define MAX_HIST_ENTRIES 50000
#define MIN_RUNQ_LAT_NS 1000000 // 1 ms threshold to record significant delays
#define NUM_BUCKETS 24

typedef __u32 u32;
typedef __u64 u64;

void bpf_rcu_read_lock(void) __ksym;
void bpf_rcu_read_unlock(void) __ksym;

static __u64 get_task_cgroup_id(struct task_struct *task)
{
    struct css_set *cgroups;
    __u64 cgroup_id;

    bpf_rcu_read_lock();
    cgroups = BPF_CORE_READ(task, cgroups);
    cgroup_id = BPF_CORE_READ(cgroups, dfl_cgrp, kn, id);
    bpf_rcu_read_unlock();

    return cgroup_id;
}

struct runq_hist_key {
    u64 cgroup_id;
    u64 prev_cgroup_id;
    u32 bucket;
};

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_HIST_ENTRIES);
    __uint(key_size, sizeof(struct runq_hist_key));
    __uint(value_size, sizeof(u64));
} runq_histograms SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_TASK_ENTRIES);
    __uint(key_size, sizeof(u32));
    __uint(value_size, sizeof(u64));
} runq_enqueued SEC(".maps");

static __always_inline u32 get_hist_bucket(u64 lat_ns)
{
    // Buckets mirror Prometheus ExponentialBuckets(1000, 2, 24)
    // bucket 0: < 2µs, bucket 1: < 4µs, ..., bucket 23: >= ~8.3s
    u64 v = lat_ns / 1000;
    if (v == 0) return 0;

    u32 b = 0;
    while (v > 1 && b < (NUM_BUCKETS - 1)) {
        v >>= 1;
        b++;
    }
    return b;
}

SEC("tp_btf/sched_wakeup")
int tp_sched_wakeup(void *ctx)
{
    struct task_struct *task;

    task = (struct task_struct *)ctx;
    __u32 pid = BPF_CORE_READ(task, pid);
    __u64 ts = bpf_ktime_get_ns();

    bpf_map_update_elem(&runq_enqueued, &pid, &ts, BPF_NOEXIST);
    return 0;
}

SEC("tp_btf/sched_switch")
int tp_sched_switch(__u64 *ctx)
{
    struct task_struct *prev = (struct task_struct *)ctx[1];
    struct task_struct *next = (struct task_struct *)ctx[2];
    u32 next_pid = BPF_CORE_READ(next, pid);

    // fetch timestamp of when the next task was enqueued
    u64 *tsp = bpf_map_lookup_elem(&runq_enqueued, &next_pid);
    if (tsp == NULL) {
        return 0; // missed enqueue
    }

    // calculate runq latency before deleting the stored timestamp
    u64 now = bpf_ktime_get_ns();
    u64 runq_lat = now - *tsp;

    // delete pid from enqueued map
    bpf_map_delete_elem(&runq_enqueued, &next_pid);

    // Filter out minor scheduling delays to focus on heavy-hitter noisy neighbor interference
    if (runq_lat < MIN_RUNQ_LAT_NS) {
        return 0;
    }

    u64 prev_cgroup_id = get_task_cgroup_id(prev);
    u64 cgroup_id = get_task_cgroup_id(next);

    struct runq_hist_key key = {
        .cgroup_id = cgroup_id,
        .prev_cgroup_id = prev_cgroup_id,
        .bucket = get_hist_bucket(runq_lat),
    };

    u64 *count = bpf_map_lookup_elem(&runq_histograms, &key);
    if (count) {
        __sync_fetch_and_add(count, 1);
    } else {
        u64 initial_count = 1;
        bpf_map_update_elem(&runq_histograms, &key, &initial_count, BPF_NOEXIST);
    }

    return 0;
}

char LICENSE[] SEC("license") = "GPL";