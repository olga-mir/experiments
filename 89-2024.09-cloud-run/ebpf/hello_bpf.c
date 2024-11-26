#include <linux/bpf.h>
#include <linux/ptrace.h>
#include <linux/types.h>

SEC("tracepoint/syscalls/sys_enter_execve")
int hello_world(void *ctx) {
    bpf_printk("Hello, eBPF World from Cloud Run!\n");
    return 0;
}

char _license[] SEC("license") = "GPL";

