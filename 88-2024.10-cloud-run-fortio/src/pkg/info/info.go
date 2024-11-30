package info

import (
	"encoding/json"
	"log"
	"net"
	"net/http"
	"os"
	"os/exec"
	"runtime"
	"strings"
)

func HandleInfo(w http.ResponseWriter, r *http.Request) {
	info := getSystemInfo()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(info)
}

type SystemInfo struct {
	Hostname    string            `json:"hostname"`
	Environment map[string]string `json:"environment"`
	Network     NetworkInfo       `json:"network"`
	System      SystemDetails     `json:"system"`
	Files       FileContents      `json:"files"`
}

type NetworkInfo struct {
	Interfaces  []InterfaceInfo `json:"interfaces"`
	Gateway     string          `json:"gateway"`
	Nameservers []string        `json:"nameservers"`
	Routes      []string        `json:"routes"`
}

type InterfaceInfo struct {
	Name       string   `json:"name"`
	Addresses  []string `json:"addresses"`
	MacAddress string   `json:"mac_address"`
}

type SystemDetails struct {
	OS           string `json:"os"`
	Architecture string `json:"architecture"`
	NumCPU       int    `json:"num_cpu"`
	UnameInfo    string `json:"uname"`
}

type FileContents struct {
	EtcHosts   string `json:"etc_hosts"`
	ResolvConf string `json:"resolv_conf"`
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	http.HandleFunc("/", handleInfo)
	log.Printf("Starting server on port %s", port)
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatal(err)
	}
}

func handleInfo(w http.ResponseWriter, r *http.Request) {
	info := getSystemInfo()

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(info)
}

func getSystemInfo() SystemInfo {
	hostname, _ := os.Hostname()

	return SystemInfo{
		Hostname:    hostname,
		Environment: getEnvironment(),
		Network:     getNetworkInfo(),
		System:      getSystemDetails(),
		Files:       getFileContents(),
	}
}

func getEnvironment() map[string]string {
	env := make(map[string]string)
	for _, e := range os.Environ() {
		if i := strings.Index(e, "="); i >= 0 {
			env[e[:i]] = e[i+1:]
		}
	}
	return env
}

func getNetworkInfo() NetworkInfo {
	interfaces, _ := net.Interfaces()
	var netInfo NetworkInfo

	for _, iface := range interfaces {
		addrs, _ := iface.Addrs()
		var addresses []string
		for _, addr := range addrs {
			addresses = append(addresses, addr.String())
		}

		netInfo.Interfaces = append(netInfo.Interfaces, InterfaceInfo{
			Name:       iface.Name,
			Addresses:  addresses,
			MacAddress: iface.HardwareAddr.String(),
		})
	}

	// Get gateway
	if out, err := exec.Command("ip", "route", "show", "default").Output(); err == nil {
		netInfo.Gateway = strings.TrimSpace(string(out))
	}

	// Get routing table
	if out, err := exec.Command("ip", "route").Output(); err == nil {
		routes := strings.Split(string(out), "\n")
		netInfo.Routes = routes
	}

	// Get nameservers from resolv.conf
	if content, err := os.ReadFile("/etc/resolv.conf"); err == nil {
		lines := strings.Split(string(content), "\n")
		for _, line := range lines {
			if strings.HasPrefix(strings.TrimSpace(line), "nameserver") {
				parts := strings.Fields(line)
				if len(parts) > 1 {
					netInfo.Nameservers = append(netInfo.Nameservers, parts[1])
				}
			}
		}
	}

	return netInfo
}

func getSystemDetails() SystemDetails {
	unameString := ""
	if out, err := exec.Command("uname", "-a").Output(); err == nil {
		unameString = strings.TrimSpace(string(out))
	}

	return SystemDetails{
		OS:           runtime.GOOS,
		Architecture: runtime.GOARCH,
		NumCPU:       runtime.NumCPU(),
		UnameInfo:    unameString,
	}
}

func getFileContents() FileContents {
	var files FileContents

	if hosts, err := os.ReadFile("/etc/hosts"); err == nil {
		files.EtcHosts = string(hosts)
	}

	if resolv, err := os.ReadFile("/etc/resolv.conf"); err == nil {
		files.ResolvConf = string(resolv)
	}

	return files
}
