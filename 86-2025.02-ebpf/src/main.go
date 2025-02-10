package main

import (
	"context"
	"ebpf-hello/pkg/metrics"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/cilium/ebpf"
	"github.com/cilium/ebpf/link"
	"github.com/cilium/ebpf/ringbuf"
	"github.com/cilium/ebpf/rlimit"
)

//go:generate bpf2go -cc clang -cflags "-O2 -g -Wall -Werror" bpf bpf/noisy-neighbour.bpf.c -- -I/usr/include/bpf -I/usr/include

func main() {
	if err := rlimit.RemoveMemlock(); err != nil {
		log.Fatalf("Failed to remove rlimit: %v", err)
	}

	objs := bpfObjects{}
	if err := loadBpfObjects(&objs, nil); err != nil {
		log.Fatalf("Failed to load BPF program: %v", err)
	}
	defer objs.Close()

	wakeupLink, err := link.AttachTracing(link.TracingOptions{
		Program:    objs.TpSchedWakeup,
		AttachType: ebpf.AttachTraceRawTp,
	})
	if err != nil {
		log.Fatalf("Failed to attach sched_wakeup: %v", err)
	}
	defer wakeupLink.Close()

	switchLink, err := link.AttachTracing(link.TracingOptions{
		Program:    objs.TpSchedSwitch,
		AttachType: ebpf.AttachTraceRawTp,
	})
	if err != nil {
		log.Fatalf("Failed to attach sched_switch: %v", err)
	}
	defer switchLink.Close()

	log.Println("Successfully loaded and attached BPF program")
	log.Println("sudo cat /sys/kernel/debug/tracing/trace_pipe")

	// Create ring buffer reader
	rd, err := ringbuf.NewReader(objs.events)
	if err != nil {
		log.Fatalf("Failed to create ring buffer reader: %v", err)
	}
	defer rd.Close()

	// Create and start collector
	collector, err := metrics.NewCollector(rd, 30*time.Second)
	if err != nil {
		log.Fatalf("Failed to create collector: %v", err)
	}

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	if err := collector.Start(ctx); err != nil {
		log.Fatalf("Failed to start collector: %v", err)
	}
	defer collector.Stop()

	// Wait for a signal to cleanup
	stopper := make(chan os.Signal, 1)
	signal.Notify(stopper, os.Interrupt, syscall.SIGTERM)
	<-stopper

	log.Println("Cleaning up...")
}
