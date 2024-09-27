#include <linux/bpf.h>

SEC("tracepoint/syscalls/sys_enter_execve")
int hello_bpf(void *ctx) {
    bpf_printk("Hello from eBPF on Cloud Run!\n");
    return 0;
}

char _license[] SEC("license") = "GPL";

