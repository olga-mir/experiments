#include <linux/bpf.h>
#include <linux/ptrace.h>
#include <linux/types.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_core_read.h>
#include <linux/types.h>
#include <bpf/bpf_tracing.h>
#include "vmlinux.h"

// https://netflixtechblog.com/noisy-neighbor-detection-with-ebpf-64b1f4b3bbdd

#define MAX_TASK_ENTRIES 10240

typedef u32 __u32
typedef u64 __u64

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, MAX_TASK_ENTRIES);
    __uint(key_size, sizeof(u32));
    __uint(value_size, sizeof(u64));
} runq_enqueued SEC(".maps");

SEC("tp_btf/sched_wakeup")
int tp_sched_wakeup(u64 *ctx)
{
    struct task_struct *task = (void *)ctx[0];
    u32 pid = task->pid;
    u64 ts = bpf_ktime_get_ns();

    bpf_map_update_elem(&runq_enqueued, &pid, &ts, BPF_NOEXIST);
    return 0;
}

SEC("tp_btf/sched_switch")
int tp_sched_switch(__u64 *ctx)
{
    struct task_struct *prev = (struct task_struct *)ctx[1];
    struct task_struct *next = (struct task_struct *)ctx[2];
    u32 prev_pid = BPF_CORE_READ(prev->pid);
    u32 next_pid = BPF_CORE_READ(next->pid);

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

    u64 prev_cgroup_id = get_task_cgroup_id(prev);
    u64 cgroup_id = get_task_cgroup_id(next);

    // per-cgroup-id-per-CPU rate-limiting
    // to balance observability with performance overhead
    u64 *last_ts = bpf_map_lookup_elem(&cgroup_id_to_last_event_ts, &cgroup_id);
    u64 last_ts_val = last_ts == NULL ? 0 : *last_ts;

    // check the rate limit for the cgroup_id in consideration
    // before doing more work
    if (now - last_ts_val < RATE_LIMIT_NS) {
        // Rate limit exceeded, drop the event
        return 0;
    }

    struct runq_event *event;
    event = bpf_ringbuf_reserve(&events, sizeof(*event), 0);

    if (event) {
        event->prev_cgroup_id = prev_cgroup_id;
        event->cgroup_id = cgroup_id;
        event->runq_lat = runq_lat;
        event->ts = now;
        bpf_ringbuf_submit(event, 0);
        // Update the last event timestamp for the current cgroup_id
        bpf_map_update_elem(&cgroup_id_to_last_event_ts, &cgroup_id,
            &now, BPF_ANY);

    }

    return 0;
}

void bpf_rcu_read_lock(void) __ksym;
void bpf_rcu_read_unlock(void) __ksym;

u64 get_task_cgroup_id(struct task_struct *task)
{
    struct css_set *cgroups;
    u64 cgroup_id;
    bpf_rcu_read_lock();
    cgroups = task->cgroups;
    cgroup_id = cgroups->dfl_cgrp->kn->id;
    bpf_rcu_read_unlock();
    return cgroup_id;
}

struct {
    __uint(type, BPF_MAP_TYPE_RINGBUF);
    __uint(max_entries, RINGBUF_SIZE_BYTES);
} events SEC(".maps");

struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_HASH);
    __uint(max_entries, MAX_TASK_ENTRIES);
    __uint(key_size, sizeof(u64));
    __uint(value_size, sizeof(u64));
} cgroup_id_to_last_event_ts SEC(".maps");

struct runq_event {
    u64 prev_cgroup_id;
    u64 cgroup_id;
    u64 runq_lat;
    u64 ts;
};

