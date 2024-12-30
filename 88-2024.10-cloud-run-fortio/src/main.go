package main

import (
	"flag"
	"log"
	"net/http"

	sysinfo "cr.explore.com/pkg/info"
)

func main() {
	// Command line flags
	port := flag.String("port", "8080", "Port to listen on")
	flag.Parse()

	// Register handlers
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
