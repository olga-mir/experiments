package sysinfo

import (
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"time"
)

type MetadataCollector struct {
	Client  *http.Client
	baseURL string
}

func NewMetadataCollector() *MetadataCollector {
	return &MetadataCollector{
		Client: &http.Client{
			Timeout: 5 * time.Second,
		},
		baseURL: "http://169.254.169.254",
	}
}

func (c *MetadataCollector) Collect() (map[string]interface{}, error) {
	if c.Client == nil {
		c.Client = &http.Client{
			Timeout: 5 * time.Second,
		}
	}

	// Create request for the recursive endpoint
	req, err := http.NewRequest("GET", c.baseURL+"/computeMetadata/v1/?recursive=true", nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create metadata request: %w", err)
	}

	// Add required header
	req.Header.Add("Metadata-Flavor", "Google")

	// Make the request
	resp, err := c.Client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to query metadata server: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("metadata server returned status %d", resp.StatusCode)
	}

	// Read body
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read metadata response: %w", err)
	}

	// Parse JSON into a map without predefined structure
	var result map[string]interface{}
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to parse metadata response: %w", err)
	}

	// Also try to get the internal IP specifically
	internalIPReq, err := http.NewRequest("GET", c.baseURL+"/computeMetadata/v1/instance/network-interfaces/0/ip", nil)
	if err == nil {
		internalIPReq.Header.Add("Metadata-Flavor", "Google")
		if internalIPResp, err := c.Client.Do(internalIPReq); err == nil {
			defer internalIPResp.Body.Close()
			if internalIPResp.StatusCode == http.StatusOK {
				if ipBytes, err := io.ReadAll(internalIPResp.Body); err == nil {
					result["internal_ip"] = string(ipBytes)
				}
			}
		}
	}

	// Try to get the VPC network name
	networkReq, err := http.NewRequest("GET", c.baseURL+"/computeMetadata/v1/instance/network-interfaces/0/network", nil)
	if err == nil {
		networkReq.Header.Add("Metadata-Flavor", "Google")
		if networkResp, err := c.Client.Do(networkReq); err == nil {
			defer networkResp.Body.Close()
			if networkResp.StatusCode == http.StatusOK {
				if networkBytes, err := io.ReadAll(networkResp.Body); err == nil {
					result["vpc_network"] = string(networkBytes)
				}
			}
		}
	}

	// Try to get the subnet name
	subnetReq, err := http.NewRequest("GET", c.baseURL+"/computeMetadata/v1/instance/network-interfaces/0/subnet", nil)
	if err == nil {
		subnetReq.Header.Add("Metadata-Flavor", "Google")
		if subnetResp, err := c.Client.Do(subnetReq); err == nil {
			defer subnetResp.Body.Close()
			if subnetResp.StatusCode == http.StatusOK {
				if subnetBytes, err := io.ReadAll(subnetResp.Body); err == nil {
					result["vpc_subnet"] = string(subnetBytes)
				}
			}
		}
	}

	return map[string]interface{}{
		"metadata": result,
	}, nil
}
