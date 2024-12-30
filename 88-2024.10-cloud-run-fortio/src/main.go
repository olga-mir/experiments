package main

import (
	"flag"
	"fmt"
	"log"
	"net/http"
	"os"

	"cloud.google.com/go/profiler"
	sysinfo "cr.explore.com/pkg/info"
)

func main() {
	setupCloudProfiler()

	port := flag.String("port", "8080", "Port to listen on")
	flag.Parse()

	http.HandleFunc("/", handleRoot)
	http.HandleFunc("/info", sysinfo.HandleRequestInfo)

	log.Printf("Starting server on port %s", *port)
	if err := http.ListenAndServe(":"+*port, nil); err != nil {
		log.Fatal(err)
	}
}

func handleRoot(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path != "/" {
		http.NotFound(w, r)
		return
	}
	w.Write([]byte("Cloud Run Explorer\n\nAvailable endpoints:\n/info - Get Cloud Run environment information"))
}

func setupCloudProfiler() {
	_, isSet := os.LookupEnv("PROJECT_ID")
	if !isSet {
		fmt.Printf("PROJECT_ID environment variable not set - when not running in GCP Profiler will not work")
		return
	}

	// Start profiler https://cloud.google.com/profiler/docs/profiling-go#gke
	cfg := profiler.Config{
		Service:        "demooperator",
		ServiceVersion: Commit,
		DebugLogging:   true,
	}

	if err := profiler.Start(cfg); err != nil {
		fmt.Errorf("Unable to start Profiler", err)
	} else {
		fmt.Println("Started Profiler")
	}
}
