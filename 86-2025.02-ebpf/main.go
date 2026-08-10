package main

import (
	"bytes"
	"encoding/binary"
	"errors"
	"log"
	"net/http"
	"os"
	"os/signal"
	"path/filepath"
	"strings"
	"sync"
	"syscall"
	"time"

	"github.com/cilium/ebpf"
	"github.com/cilium/ebpf/link"
	"github.com/cilium/ebpf/ringbuf"
	"github.com/cilium/ebpf/rlimit"
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

//go:generate bpf2go -cc clang -cflags "-O2 -g -Wall -Werror" bpf bpf/noisy-neighbour.bpf.c -- -I/usr/include/bpf -I/usr/include

const cgroupRoot = "/sys/fs/cgroup"

var (
	runqLatency = promauto.NewHistogramVec(prometheus.HistogramOpts{
		Name:    "ebpf_runq_latency_nanoseconds",
		Help:    "Run queue latency in nanoseconds, labeled by the scheduled cgroup and the cgroup it preempted",
		Buckets: prometheus.ExponentialBuckets(1_000, 2, 24), // 1µs → ~8s
	}, []string{"cgroup", "prev_cgroup"})

	eventsTotal = promauto.NewCounter(prometheus.CounterOpts{
		Name: "ebpf_events_total",
		Help: "Total ring buffer events consumed from the kernel",
	})
)

// runqEvent mirrors the C struct layout from noisy-neighbour.bpf.c.
type runqEvent struct {
	PrevCgroupID uint64
	CgroupID     uint64
	RunqLat      uint64
	Ts           uint64
}

// cgroupMapper resolves kernel cgroup IDs to human-readable labels.
// In cgroupv2 the cgroup ID equals the inode of the cgroup directory; in GKE
// the inode is the lower 32 bits of kernfs_node.id so we try both.
type cgroupMapper struct {
	mu    sync.RWMutex
	byIno map[uint64]string
}

func newCgroupMapper() *cgroupMapper {
	m := &cgroupMapper{byIno: make(map[uint64]string)}
	m.refresh()
	go func() {
		t := time.NewTicker(30 * time.Second)
		defer t.Stop()
		for range t.C {
			m.refresh()
		}
	}()
	return m
}

func (m *cgroupMapper) refresh() {
	next := make(map[uint64]string)
	_ = filepath.WalkDir(cgroupRoot, func(path string, d os.DirEntry, err error) error {
		if err != nil || !d.IsDir() {
			return nil
		}
		info, err := d.Info()
		if err != nil {
			return nil
		}
		st, ok := info.Sys().(*syscall.Stat_t)
		if !ok {
			return nil
		}
		next[st.Ino] = cgroupLabel(path)
		return nil
	})
	m.mu.Lock()
	m.byIno = next
	m.mu.Unlock()
}

func (m *cgroupMapper) name(id uint64) string {
	m.mu.RLock()
	defer m.mu.RUnlock()
	if label, ok := m.byIno[id]; ok {
		return label
	}
	// kernfs_node.id packs generation in upper 32 bits; inode lives in lower 32.
	if label, ok := m.byIno[id&0xFFFFFFFF]; ok {
		return label
	}
	return "unresolved"
}

// cgroupLabel derives a concise Prometheus-friendly label from a cgroup path.
//
// GKE cgroupv2 layout (containerd):
//   kubepods.slice/kubepods-burstable.slice/kubepods-burstable-pod<uid>.slice/cri-containerd-<cid>.scope
//
// We extract pod-uid prefix and container-id prefix to keep cardinality low.
func cgroupLabel(path string) string {
	rel := strings.TrimPrefix(strings.TrimSuffix(path, "/"), cgroupRoot)
	rel = strings.TrimPrefix(rel, "/")
	if rel == "" {
		return "root"
	}
	parts := strings.Split(rel, "/")
	for i, p := range parts {
		for _, qos := range []string{"kubepods-burstable-pod", "kubepods-besteffort-pod", "kubepods-guaranteed-pod", "kubepods-pod", "pod"} {
			if strings.HasPrefix(p, qos) {
				uid := shortID(strings.TrimSuffix(strings.TrimPrefix(p, qos), ".slice"))
				if i+1 < len(parts) {
					cid := shortContainerID(parts[i+1])
					return "pod/" + uid + "/" + cid
				}
				return "pod/" + uid
			}
		}
	}
	// Fallback: last two path components.
	if len(parts) > 2 {
		return strings.Join(parts[len(parts)-2:], "/")
	}
	return rel
}

func shortID(s string) string {
	s = strings.ReplaceAll(s, "_", "-")
	if len(s) > 8 {
		return s[:8]
	}
	return s
}

func shortContainerID(s string) string {
	s = strings.TrimSuffix(s, ".scope")
	for _, pfx := range []string{"cri-containerd-", "docker-"} {
		if strings.HasPrefix(s, pfx) {
			s = strings.TrimPrefix(s, pfx)
			break
		}
	}
	if len(s) > 8 {
		return s[:8]
	}
	return s
}

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

	rd, err := ringbuf.NewReader(objs.Events)
	if err != nil {
		log.Fatalf("Failed to open ring buffer: %v", err)
	}
	defer rd.Close()

	mapper := newCgroupMapper()

	go func() {
		http.Handle("/metrics", promhttp.Handler())
		log.Println("Metrics available at :9090/metrics")
		log.Fatal(http.ListenAndServe(":9090", nil))
	}()

	stopper := make(chan os.Signal, 1)
	signal.Notify(stopper, os.Interrupt, syscall.SIGTERM)
	go func() {
		<-stopper
		rd.Close()
	}()

	log.Println("Collecting run-queue events from eBPF ring buffer...")

	var ev runqEvent
	for {
		rec, err := rd.Read()
		if err != nil {
			if errors.Is(err, ringbuf.ErrClosed) {
				log.Println("Shutting down")
				return
			}
			log.Printf("ring buffer read error: %v", err)
			continue
		}
		if err := binary.Read(bytes.NewReader(rec.RawSample), binary.LittleEndian, &ev); err != nil {
			log.Printf("parse event: %v", err)
			continue
		}
		cgroup := mapper.name(ev.CgroupID)
		if strings.HasPrefix(cgroup, "pod/") {
			runqLatency.
				WithLabelValues(cgroup, mapper.name(ev.PrevCgroupID)).
				Observe(float64(ev.RunqLat))
		}
		eventsTotal.Inc()
	}
}
