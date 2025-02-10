package metrics

import (
	"bytes"
	"context"
	"encoding/binary"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"

	monitoring "cloud.google.com/go/monitoring/apiv3/v2"
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

// Types matching the eBPF program
type runq_event struct {
	PrevCgroupID uint64 `align:"prev_cgroup_id"`
	CgroupID     uint64 `align:"cgroup_id"`
	RunqLat      uint64 `align:"runq_lat"`
	Ts           uint64 `align:"ts"`
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

	value, err := ioutil.ReadAll(resp.Body)
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
					"container_name": containerInfo.Name,
					"location":       m.metadata.location,
					"cluster_name":   m.metadata.clusterName,
					"namespace_name": containerInfo.Namespace,
					"pod_name":       containerInfo.PodName,
					"node_name":      m.metadata.nodeName,
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
						DoubleValue: float64(event.RunqLat) / 1000000.0, // Convert to milliseconds
					},
				},
			}},
		}},
	}

	ctx := context.Background()
	return m.client.CreateTimeSeries(ctx, req)
}

func (m *MetricsExporter) createTimeSeriesPreemption(event *runq_event, containerInfo *ContainerInfo, preemptionType string) error {
	now := time.Now()
	req := &monitoringpb.CreateTimeSeriesRequest{
		Name: m.projectPath,
		TimeSeries: []*monitoringpb.TimeSeries{{
			Metric: &metricpb.Metric{
				Type: fmt.Sprintf("%s/sched/switch/out", metricPrefix),
				Labels: map[string]string{
					"container":       containerInfo.Name,
					"pod":             containerInfo.PodName,
					"namespace":       containerInfo.Namespace,
					"preemption_type": preemptionType,
				},
			},
			Resource: &monitoredres.MonitoredResource{
				Type: "k8s_container",
				Labels: map[string]string{
					"container_name": containerInfo.Name,
					"location":       m.metadata.location,
					"cluster_name":   m.metadata.clusterName,
					"namespace_name": containerInfo.Namespace,
					"pod_name":       containerInfo.PodName,
					"node_name":      m.metadata.nodeName,
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

type MetricsExporter struct {
	client      *monitoring.MetricClient
	projectPath string
	metadata    *GKEMetadata
}

// BPF collection related types
type bpfEvents struct {
	events *ringbuf.Reader
}

type ContainerInfo struct {
	Name      string
	PodName   string
	Namespace string
	CgroupID  uint64
}

type ContainerResolver struct {
	// Cache of cgroup ID to container info
	cgroupCache sync.Map
}

func NewContainerResolver() *ContainerResolver {
	return &ContainerResolver{}
}

func (cr *ContainerResolver) GetContainerInfo(cgroupID uint64) (*ContainerInfo, error) {
	// Try cache first
	if info, ok := cr.cgroupCache.Load(cgroupID); ok {
		return info.(*ContainerInfo), nil
	}

	// Get container info from cgroup path
	cgroupPath, err := findCgroupPath(cgroupID)
	if err != nil {
		return nil, err
	}

	// In Kubernetes, the cgroup path follows the pattern:
	// /kubepods/burstable/pod<pod-uid>/<container-id>
	// or /kubepods/pod<pod-uid>/<container-id>
	parts := strings.Split(cgroupPath, "/")
	if len(parts) < 3 {
		return nil, fmt.Errorf("invalid cgroup path: %s", cgroupPath)
	}

	// Read container metadata from the cgroup annotations
	containerInfo := &ContainerInfo{
		CgroupID: cgroupID,
	}

	// Read Kubernetes metadata from cgroup annotations
	if err := cr.readK8sMetadata(cgroupPath, containerInfo); err != nil {
		return nil, err
	}

	// Cache the result
	cr.cgroupCache.Store(cgroupID, containerInfo)
	return containerInfo, nil
}

func findCgroupPath(cgroupID uint64) (string, error) {
	// Use find to locate the cgroup.id file with matching ID
	cmd := exec.Command("find", "/sys/fs/cgroup/kubepods", "-name", "cgroup.id")
	output, err := cmd.Output()
	if err != nil {
		return "", fmt.Errorf("failed to find cgroup path: %v", err)
	}

	// Check each cgroup.id file
	for _, path := range strings.Split(string(output), "\n") {
		if path == "" {
			continue
		}

		id, err := readCgroupID(path)
		if err != nil {
			continue
		}

		if id == cgroupID {
			// Return the cgroup path (parent directory of cgroup.id)
			return filepath.Dir(path), nil
		}
	}

	return "", fmt.Errorf("cgroup ID %d not found", cgroupID)
}

func readCgroupID(path string) (uint64, error) {
	content, err := os.ReadFile(path)
	if err != nil {
		return 0, err
	}

	return strconv.ParseUint(strings.TrimSpace(string(content)), 10, 64)
}

func (cr *ContainerResolver) readK8sMetadata(cgroupPath string, info *ContainerInfo) error {
	// Read kubernetes metadata from annotations in the cgroup filesystem
	annotationsPath := filepath.Join(cgroupPath, "annotations")

	files, err := os.ReadDir(annotationsPath)
	if err != nil {
		return err
	}

	for _, file := range files {
		content, err := os.ReadFile(filepath.Join(annotationsPath, file.Name()))
		if err != nil {
			continue
		}

		switch file.Name() {
		case "io.kubernetes.container.name":
			info.Name = strings.TrimSpace(string(content))
		case "io.kubernetes.pod.name":
			info.PodName = strings.TrimSpace(string(content))
		case "io.kubernetes.pod.namespace":
			info.Namespace = strings.TrimSpace(string(content))
		}
	}

	return nil
}
