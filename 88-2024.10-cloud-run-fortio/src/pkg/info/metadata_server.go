package sysinfo

import (
	"bytes"
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

	req, err := http.NewRequest("GET", c.baseURL+"/computeMetadata/v1/?recursive=true", nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create metadata request: %w", err)
	}

	req.Header.Add("Metadata-Flavor", "Google")
	resp, err := c.Client.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to query metadata server: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("metadata server returned status %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read metadata response: %w", err)
	}

	var result map[string]interface{}
	if err := json.Unmarshal(body, &result); err != nil {
		return nil, fmt.Errorf("failed to parse metadata response: %w", err)
	}

	var prettyJSON bytes.Buffer
	if err := json.Indent(&prettyJSON, body, "", "    "); err != nil {
		fmt.Printf("Failed to format JSON: %v\n", err)
	} else {
		fmt.Println(prettyJSON.String())
	}

	// Metadata endpoint does not provide any information on interfaces
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

	return map[string]interface{}{
		"metadata": result,
	}, nil
}
