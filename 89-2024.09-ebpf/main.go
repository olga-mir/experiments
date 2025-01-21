package main

import (
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/cilium/ebpf/link"
	"github.com/cilium/ebpf/rlimit"
)

//go:generate bpf2go -cc clang -cflags "-O2 -g -Wall -Werror" bpf bpf/noisy-neighbour.bpf.c -- -I/usr/include/bpf -I/usr/include

func main() {
	// Allow the current process to lock memory for eBPF resources
	if err := rlimit.RemoveMemlock(); err != nil {
		log.Fatalf("Failed to remove rlimit: %v", err)
	}

	// Load pre-compiled programs into the kernel
	objs := bpfObjects{}
	if err := loadBpfObjects(&objs, nil); err != nil {
		log.Fatalf("Failed to load BPF program: %v", err)
	}
	defer objs.Close()

	// Attach the program to the tracepoint
	tp, err := link.Tracepoint("syscalls", "sys_enter_execve", objs.HelloWorld, nil)
	if err != nil {
		log.Fatalf("Failed to attach BPF program: %v", err)
	}
	defer tp.Close()

	log.Println("Successfully loaded and attached BPF program")
	log.Println("You can now check trace_pipe:")
	log.Println("sudo cat /sys/kernel/debug/tracing/trace_pipe")

	// Wait for a signal to cleanup
	stopper := make(chan os.Signal, 1)
	signal.Notify(stopper, os.Interrupt, syscall.SIGTERM)
	<-stopper

	log.Println("Cleaning up...")
}
