package sysinfo

import "log"

// Collector interface defines the contract for all collectors
type Collector interface {
	Collect() (map[string]interface{}, error)
}

// SystemInfo holds all collectors and gathered information
type SystemInfo struct {
	collectors []Collector
	Unix       interface{} `json:"unix,omitempty"`
	Network    interface{} `json:"network,omitempty"`
	Metadata   interface{} `json:"metadata,omitempty"`
}

// NewSystemInfo creates a new SystemInfo instance with the provided collectors
func NewSystemInfo(collectors ...Collector) *SystemInfo {
	return &SystemInfo{
		collectors: collectors,
	}
}

// CollectAll gathers information from all collectors
func (s *SystemInfo) CollectAll() error {
	for _, collector := range s.collectors {
		info, err := collector.Collect()
		if err != nil {
			// Log the error but continue with other collectors
			log.Printf("Error collecting info: %v", err)
			continue
		}

		// Store the collected information based on collector type
		switch c := collector.(type) {
		case *UnixInfoCollector:
			s.Unix = info
		case *NetworkInfoCollector:
			s.Network = info
		case *MetadataCollector:
			s.Metadata = info
		default:
			log.Printf("Unknown collector type: %T", c)
		}
	}
	return nil
}
