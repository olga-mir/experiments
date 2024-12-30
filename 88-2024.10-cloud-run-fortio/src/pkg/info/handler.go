package sysinfo

import (
	"encoding/json"
	"log"
	"net/http"
	"time"
)

/*
// Handler handles the system info HTTP requests
type Handler struct {
	collectors []Collector
}

// NewHandler creates a new system info handler
func NewHandler(collectors ...Collector) *Handler {
	return &Handler{
		collectors: collectors,
	}
}
*/

// handleRequestInfo implements the http.Handler interface
func HandleRequestInfo(w http.ResponseWriter, r *http.Request) {
	sysInfo := NewSystemInfo(
		&UnixInfoCollector{},
		&NetworkInfoCollector{},
		NewMetadataCollector(1*time.Minute))

	// Collect all information
	if err := sysInfo.CollectAll(); err != nil {
		http.Error(w, "Failed to collect system info", http.StatusInternalServerError)
		log.Printf("Error collecting system info: %v", err)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	if err := json.NewEncoder(w).Encode(sysInfo); err != nil {
		http.Error(w, "Failed to encode response", http.StatusInternalServerError)
		log.Printf("Error encoding response: %v", err)
		return
	}
}