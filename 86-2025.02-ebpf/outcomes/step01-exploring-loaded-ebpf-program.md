
## Let's get into it

### prog list

```
$ bpftool prog list
...
1087: tracing  name tp_sched_switch  tag 939fb6722315f4d8  gpl
        loaded_at 2025-02-08T01:51:33+0000  uid 0
        xlated 1784B  jited 1130B  memlock 4096B  map_ids 290,291,292
        btf_id 441
1088: tracing  name tp_sched_wakeup  tag 30dd9a4649cf2ffa  gpl
        loaded_at 2025-02-08T01:51:33+0000  uid 0
        xlated 272B  jited 188B  memlock 4096B  map_ids 290
        btf_id 442
```

These are our programs successfully jited and attached to sched switch and wakeup, too easy! They are using maps 290, 291, 292. Let's look at those.

### map list

```
$ bpftool map list
....
290: hash  name runq_enqueued  flags 0x0
        key 4B  value 8B  max_entries 20000  memlock 1806016B
291: percpu_hash  name cgroup_id_to_la  flags 0x0
        key 8B  value 8B  max_entries 20000  memlock 3085440B
292: ringbuf  name events  flags 0x0
        key 0B  value 0B  max_entries 16384  memlock 29144B
```

These maps are defined here https://github.com/olga-mir/experiments/blob/f97143f60b20a263d8f04d1cef2f7cbf38b44492/86-2025.02-ebpf/bpf/noisy-neighbour.bpf.c#L33-L50

e.g. `cgroup_id_to_la` (ID 291):

Per-CPU hash map type
8-byte keys (cgroup IDs)
8-byte values

Let's have a look what's inside!

### Dive into a map

```
$ bpftool map dump id 290
...
key: 58 77 9f 01  value: 81 57 a6 b3 93 03 00 00
key: 30 ff b1 10  value: 4e 19 45 70 46 03 00 00
key: 58 67 d6 01  value: 9d fd e7 e1 3f 03 00 00
key: 28 1f 06 00  value: 16 b1 a2 a6 b0 03 00 00
key: 40 7c 13 01  value: 05 a3 00 3f 50 03 00 00
key: 58 87 91 02  value: 56 fc 4e c3 77 03 00 00
Found 489 elements
```

Looks like matrix to me. That's what AI translated it to:

---
This is raw byte data from your `runq_enqueued` map. Let me help interpret it:

Format of the data:

Keys are 4 bytes (32 bits): `58 77 9f 01`
Values are 8 bytes (64 bits): `81 57 a6 b3 93 03 00 00`

Structure from your map definition:

Keys appear to be PIDs or task IDs (4 bytes is typical for PIDs)
Values are likely timestamps or counters (8 bytes suggests it could be a timestamp or accumulated value)

For example, taking the first entry:

```
key: 58 77 9f 01 = 27017048 (decimal, if interpreted as little-endian uint32)
value: 81 57 a6 b3 93 03 00 00 = 15196981633921 (decimal, if interpreted as little-endian uint64)
```

---

We don't need to understand this yet. Next step will be reading this data from user-space and converting them to metrics.
This map constantly growing as it collects more and more data.

### BPF_MAP_TYPE_PERCPU_HASH map

Let's look at another map:

```
$ bpftool map dump id 291
key:
01 00 00 00 00 00 00 00
value (CPU 00): 74 b4 44 4e 3f 03 00 00
value (CPU 01): 8b bb 29 4e 3f 03 00 00
value (CPU 02): 1a ae 40 4e 3f 03 00 00
value (CPU 03): 00 00 00 00 00 00 00 00
value (CPU 04): 91 3f 41 4e 3f 03 00 00
value (CPU 05): 1c 15 44 4e 3f 03 00 00
value (CPU 06): d9 67 43 4e 3f 03 00 00
value (CPU 07): cb 65 44 4e 3f 03 00 00
Found 1 element
```

This corresponds to

```c
struct {
    __uint(type, BPF_MAP_TYPE_PERCPU_HASH);
    __uint(max_entries, MAX_TASK_ENTRIES);
    __uint(key_size, sizeof(u64));
    __uint(value_size, sizeof(u64));
} cgroup_id_to_last_event_ts SEC(".maps");
```

I am not entirely sure if this is what I expect to see of if this experiment will give me a view on the node, given that the key is cgroup ID 1, isn't it container view? Even though the container is hostPID: true and is previleged. To be continued...