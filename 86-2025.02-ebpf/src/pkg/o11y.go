package observability

import (
	"bytes"
	"context"
	"encoding/binary"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"sync"
	"time"

	monitoring "cloud.google.com/go/monitoring/apiv3"
	"cloud.google.com/go/monitoring/apiv3/v2/monitoringpb"
	"github.com/cilium/ebpf/ringbuf"
	metricpb "google.golang.org/genproto/googleapis/api/metric"
	monitoredres "google.golang.org/genproto/googleapis/api/monitoredres"
	"google.golang.org/protobuf/types/known/timestamppb"
)

const (
	metricPrefix   = "custom.googleapis.com/ebpf"
	metadataServer = "http://metadata.google.internal"
)

// GKEMetadata holds cluster information
type GKEMetadata struct {
	projectID   string
	location    string
	clusterName string
	nodeName    string
}

type MetricsExporter struct {
	client      *monitoring.MetricClient
	projectPath string
	metadata    *GKEMetadata
}

// getMetadataValue retrieves value from GCE metadata server
func getMetadataValue(path string) (string, error) {
	client := &http.Client{Timeout: 5 * time.Second}
	req, err := http.NewRequest("GET", metadataServer+"/computeMetadata/v1/"+path, nil)
	if err != nil {
		return "", err
	}
	req.Header.Set("Metadata-Flavor", "Google")

	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("metadata server returned status %d", resp.StatusCode)
	}

	value, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	return string(value), nil
}

// getGKEMetadata retrieves cluster information from GKE environment
func getGKEMetadata() (*GKEMetadata, error) {
	// Project ID can be determined automatically by the client library
	projectID, err := getMetadataValue("project/project-id")
	if err != nil {
		return nil, fmt.Errorf("failed to get project ID: %v", err)
	}

	// Get cluster name and location from metadata server
	clusterName, err := getMetadataValue("instance/attributes/cluster-name")
	if err != nil {
		return nil, fmt.Errorf("failed to get cluster name: %v", err)
	}

	location, err := getMetadataValue("instance/attributes/cluster-location")
	if err != nil {
		return nil, fmt.Errorf("failed to get cluster location: %v", err)
	}

	nodeName, err := getMetadataValue("instance/hostname")
	if err != nil {
		return nil, fmt.Errorf("failed to get node name: %v", err)
	}

	return &GKEMetadata{
		projectID:   projectID,
		location:    location,
		clusterName: clusterName,
		nodeName:    nodeName,
	}, nil
}

func NewMetricsExporter() (*MetricsExporter, error) {
	ctx := context.Background()

	// The client library will automatically detect the project ID
	client, err := monitoring.NewMetricClient(ctx)
	if err != nil {
		return nil, fmt.Errorf("failed to create metric client: %v", err)
	}

	metadata, err := getGKEMetadata()
	if err != nil {
		return nil, fmt.Errorf("failed to get GKE metadata: %v", err)
	}

	return &MetricsExporter{
		client:      client,
		projectPath: fmt.Sprintf("projects/%s", metadata.projectID),
		metadata:    metadata,
	}, nil
}

func (m *MetricsExporter) createTimeSeriesLatency(event *runq_event, containerInfo *ContainerInfo) error {
	now := time.Now()
	req := &monitoringpb.CreateTimeSeriesRequest{
		Name: m.projectPath,
		TimeSeries: []*monitoringpb.TimeSeries{{
			Metric: &metricpb.Metric{
				Type: fmt.Sprintf("%s/runq/latency", metricPrefix),
				Labels: map[string]string{
					"container": containerInfo.Name,
					"pod":       containerInfo.PodName,
					"namespace": containerInfo.Namespace,
				},
			},
			Resource: &monitoredres.MonitoredResource{
				Type: "k8s_container",
				Labels: map[string]string{
					"container_name": containerName,
					"location":       "",
					"cluster_name":   "",
					"namespace_name": "",
					"pod_name":       "",
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
	// Initialize container runtime
	containerRuntime, err := NewContainerRuntime()
	if err != nil {
		log.Fatalf("Failed to initialize container runtime: %v", err)
	}
	defer containerRuntime.client.Close()
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

		// Get container info from cgroup ID
		containerInfo, err := containerRuntime.GetContainerInfo(event.cgroup_id)
		if err != nil {
			// This might be a system process, not in a container
			log.Printf("Failed to get container info: %v", err)
			continue
		}

		// Emit latency metric
		if err := metricsExporter.createTimeSeriesLatency(&event, containerInfo); err != nil {
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

type ContainerInfo struct {
	ID         string
	Name       string
	PodName    string
	Namespace  string
	CgroupPath string
}

type ContainerRuntime struct {
	client      *containerd.Client
	cgroupCache sync.Map
}

func NewContainerRuntime() (*ContainerRuntime, error) {
	client, err := containerd.New("/run/containerd/containerd.sock")
	if err != nil {
		return nil, fmt.Errorf("failed to connect to containerd: %v", err)
	}

	return &ContainerRuntime{
		client: client,
	}, nil
}

func (cr *ContainerRuntime) getCgroupID(cgroupPath string) (uint64, error) {
	f, err := os.Open(filepath.Join("/sys/fs/cgroup", cgroupPath, "cgroup.id"))
	if err != nil {
		return 0, err
	}
	defer f.Close()

	var id uint64
	_, err = fmt.Fscanf(f, "%d", &id)
	return id, err
}

func (cr *ContainerRuntime) updateContainerCache(ctx context.Context) error {
	containers, err := cr.client.Containers(ctx)
	if err != nil {
		return fmt.Errorf("failed to list containers: %v", err)
	}

	for _, container := range containers {
		info, err := container.Info(ctx)
		if err != nil {
			continue
		}

		// Get container labels
		labels := info.Labels
		podName := labels["io.kubernetes.pod.name"]
		namespace := labels["io.kubernetes.pod.namespace"]
		containerName := labels["io.kubernetes.container.name"]

		// Get cgroup path and ID
		task, err := container.Task(ctx, nil)
		if err != nil {
			continue
		}

		cgroupPath, err := task.Cgroup()
		if err != nil {
			continue
		}

		cgroupID, err := cr.getCgroupID(cgroupPath)
		if err != nil {
			continue
		}

		containerInfo := &ContainerInfo{
			ID:         container.ID(),
			Name:       containerName,
			PodName:    podName,
			Namespace:  namespace,
			CgroupPath: cgroupPath,
		}

		cr.cgroupCache.Store(cgroupID, containerInfo)
	}

	return nil
}

func (cr *ContainerRuntime) GetContainerInfo(cgroupID uint64) (*ContainerInfo, error) {
	// Try to get from cache first
	if info, ok := cr.cgroupCache.Load(cgroupID); ok {
		return info.(*ContainerInfo), nil
	}

	// Update cache and try again
	ctx := context.Background()
	if err := cr.updateContainerCache(ctx); err != nil {
		return nil, err
	}

	if info, ok := cr.cgroupCache.Load(cgroupID); ok {
		return info.(*ContainerInfo), nil
	}

	return nil, fmt.Errorf("container not found for cgroup ID: %d", cgroupID)
}
