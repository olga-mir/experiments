package metrics

import (
	"bytes"
	"context"
	"encoding/binary"
	"log"
	"sync"
	"time"

	"github.com/cilium/ebpf/ringbuf"
)

type Collector struct {
	exporter      *MetricsExporter
	resolver      *ContainerResolver
	reader        *ringbuf.Reader
	collectPeriod time.Duration
	stopCh        chan struct{}
	wg            sync.WaitGroup
}

func NewCollector(reader *ringbuf.Reader, collectPeriod time.Duration) (*Collector, error) {
	exporter, err := NewMetricsExporter()
	if err != nil {
		return nil, err
	}

	return &Collector{
		exporter:      exporter,
		resolver:      NewContainerResolver(),
		reader:        reader,
		collectPeriod: collectPeriod,
		stopCh:        make(chan struct{}),
	}, nil
}

func (c *Collector) Start(ctx context.Context) error {
	c.wg.Add(1)
	go c.collect(ctx)
	return nil
}

func (c *Collector) Stop() {
	close(c.stopCh)
	c.wg.Wait()
}

func (c *Collector) collect(ctx context.Context) {
	defer c.wg.Done()
	ticker := time.NewTicker(c.collectPeriod)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-c.stopCh:
			return
		case <-ticker.C:
			if err := c.processEvents(); err != nil {
				log.Printf("Error processing events: %v", err)
			}
		}
	}
}

func (c *Collector) processEvents() error {
	// Process all available events in the ring buffer
	for {
		record, err := c.reader.Read()
		if err != nil {
			if err == ringbuf.ErrClosed {
				return nil
			}
			return err
		}

		// Parse the event
		var event runq_event
		if err := binary.Read(bytes.NewReader(record.RawSample), binary.LittleEndian, &event); err != nil {
			log.Printf("Failed to parse event: %v", err)
			continue
		}

		// Get container info
		containerInfo, err := c.resolver.GetContainerInfo(event.CgroupID)
		if err != nil {
			log.Printf("Failed to get container info: %v", err)
			continue
		}

		// Emit metrics
		if err := c.exporter.createTimeSeriesLatency(&event, containerInfo); err != nil {
			log.Printf("Failed to emit latency metric: %v", err)
		}

		// For preemption events
		preemptionType := determinePreemptionType(event.PrevCgroupID, event.CgroupID)
		if err := c.exporter.createTimeSeriesPreemption(&event, containerInfo, preemptionType); err != nil {
			log.Printf("Failed to emit preemption metric: %v", err)
		}
	}
}

/* clean buffers
func (c *Collector) cleanupMaps(maps *bpfMaps) error {
    // Clear the maps after reading
    if err := maps.cgroup_id_to_last_event_ts.Clear(); err != nil {
        return fmt.Errorf("failed to clear last_event_ts map: %v", err)
    }
    if err := maps.runq_enqueued.Clear(); err != nil {
        return fmt.Errorf("failed to clear runq_enqueued map: %v", err)
    }
    return nil
}
*/
