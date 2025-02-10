package observability

import (
	"bytes"
	"context"
	"encoding/binary"
	"fmt"
	"log"
	"time"

	monitoring "cloud.google.com/go/monitoring/apiv3"
	"cloud.google.com/go/monitoring/apiv3/v2/monitoringpb"
	"github.com/cilium/ebpf/ringbuf"
	metricpb "google.golang.org/genproto/googleapis/api/metric"
	monitoredres "google.golang.org/genproto/googleapis/api/monitoredres"
	"google.golang.org/protobuf/types/known/timestamppb"
)

const (
	metricPrefix = "custom.googleapis.com/ebpf"
)

type MetricsExporter struct {
	client      *monitoring.MetricClient
	projectPath string
}

func NewMetricsExporter() (*MetricsExporter, error) {
	ctx := context.Background()
	client, err := monitoring.NewMetricClient(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to create metric client: %v", err)
	}

	return &MetricsExporter{
		client:      client,
		projectPath: fmt.Sprintf("projects/%s", projectID),
	}, nil
}

func (m *MetricsExporter) createTimeSeriesLatency(event *runq_event, containerName string) error {
	now := time.Now()
	req := &monitoringpb.CreateTimeSeriesRequest{
		Name: m.projectPath,
		TimeSeries: []*monitoringpb.TimeSeries{{
			Metric: &metricpb.Metric{
				Type: fmt.Sprintf("%s/runq/latency", metricPrefix),
				Labels: map[string]string{
					"container": containerName,
				},
			},
			Resource: &monitoredres.MonitoredResource{
				Type: "k8s_container",
				Labels: map[string]string{
					"container_name": containerName,
					"location":       "your-cluster-location",
					"cluster_name":   "your-cluster-name",
					"namespace_name": "your-namespace",
					"pod_name":       "your-pod-name",
				},
			},
			Points: []*monitoringpb.Point{{
				Interval: &monitoringpb.TimeInterval{
					EndTime: &timestamppb.Timestamp{
						Seconds: now.Unix(),
					},
				},
				Value: &monitoringpb.TypedValue{
					Value: &monitoringpb.TypedValue_DoubleValue{
						DoubleValue: float64(event.runq_lat) / 1000000.0, // Convert to milliseconds
					},
				},
			}},
		}},
	}

	ctx := context.Background()
	return m.client.CreateTimeSeries(ctx, req)
}

func (m *MetricsExporter) createTimeSeriesPreemption(event *runq_event, containerName, preemptionType string) error {
	now := time.Now()
	req := &monitoringpb.CreateTimeSeriesRequest{
		Name: m.projectPath,
		TimeSeries: []*monitoringpb.TimeSeries{{
			Metric: &metricpb.Metric{
				Type: fmt.Sprintf("%s/sched/switch/out", metricPrefix),
				Labels: map[string]string{
					"container":       containerName,
					"preemption_type": preemptionType,
				},
			},
			Resource: &monitoredres.MonitoredResource{
				Type: "k8s_container",
				Labels: map[string]string{
					"container_name": containerName,
					"location":       "your-cluster-location",
					"cluster_name":   "your-cluster-name",
					"namespace_name": "your-namespace",
					"pod_name":       "your-pod-name",
				},
			},
			Points: []*monitoringpb.Point{{
				Interval: &monitoringpb.TimeInterval{
					EndTime: &timestamppb.Timestamp{
						Seconds: now.Unix(),
					},
				},
				Value: &monitoringpb.TypedValue{
					Value: &monitoringpb.TypedValue_Int64Value{
						Int64Value: 1,
					},
				},
			}},
		}},
	}

	ctx := context.Background()
	return m.client.CreateTimeSeries(ctx, req)
}

func main() {
	// Initialize metrics exporter
	metricsExporter, err := NewMetricsExporter()
	if err != nil {
		log.Fatalf("Failed to create metrics exporter: %v", err)
	}

	// Load and attach eBPF program (your existing code here)
	// ...

	// Create ring buffer reader
	rd, err := ringbuf.NewReader(objs.events)
	if err != nil {
		log.Fatalf("Failed to create ring buffer reader: %v", err)
	}
	defer rd.Close()

	// Process events from ring buffer
	var event runq_event
	for {
		record, err := rd.Read()
		if err != nil {
			if err == ringbuf.ErrClosed {
				return
			}
			log.Printf("Error reading from ring buffer: %v", err)
			continue
		}

		// Parse the event
		err = binary.Read(bytes.NewReader(record.RawSample), binary.LittleEndian, &event)
		if err != nil {
			log.Printf("Failed to parse event: %v", err)
			continue
		}

		// Get container name from cgroup ID (you'll need to implement this)
		containerName, err := getCgroupContainerName(event.cgroup_id)
		if err != nil {
			log.Printf("Failed to get container name: %v", err)
			continue
		}

		// Emit latency metric
		if err := metricsExporter.createTimeSeriesLatency(&event, containerName); err != nil {
			log.Printf("Failed to emit latency metric: %v", err)
		}

		// Determine preemption type
		preemptionType := determinePreemptionType(event.prev_cgroup_id, event.cgroup_id)

		// Emit preemption metric
		if err := metricsExporter.createTimeSeriesPreemption(&event, containerName, preemptionType); err != nil {
			log.Printf("Failed to emit preemption metric: %v", err)
		}
	}
}

func determinePreemptionType(prevCgroupID, newCgroupID uint64) string {
	if prevCgroupID == newCgroupID {
		return "same_container"
	}
	if prevCgroupID == 0 || newCgroupID == 0 {
		return "system_service"
	}
	return "other_container"
}

// You'll need to implement this function to map cgroup IDs to container names
func getCgroupContainerName(cgroupID uint64) (string, error) {
	// Implementation depends on your container runtime and setup
	// You might want to use the kubernetes API or container runtime API
	// to get this information
	return "", fmt.Errorf("not implemented")
}
