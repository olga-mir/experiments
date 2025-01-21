package main

import (
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/cilium/ebpf/link"
)

//go:generate go run github.com/cilium/ebpf/cmd/bpf2go -target bpf hello hello.bpf.c -- -I. -I/usr/include/bpf

func main() {
	// Allow the current process to lock memory for eBPF resources
	if err := os.Setrlimit(syscall.RLIMIT_MEMLOCK, &syscall.Rlimit{
		Current: syscall.RLIM_INFINITY,
		Max:     syscall.RLIM_INFINITY,
	}); err != nil {
		log.Fatalf("Failed to set rlimit: %v", err)
	}

	// Load pre-compiled programs into the kernel
	objs := bpfObjects{}
	if err := loadBpfObjects(&objs, nil); err != nil {
		log.Fatalf("Failed to load BPF program: %v", err)
	}
	defer objs.Close()

	// Attach the program to the tracepoint
	tp, err := link.Tracepoint("syscalls", "sys_enter_execve", objs.HelloWorld)
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
