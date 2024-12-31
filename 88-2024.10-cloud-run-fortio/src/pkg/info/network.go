package sysinfo

import (
	"bufio"
	"os"
	"strings"

	"github.com/vishvananda/netlink"
	"golang.org/x/sys/unix"
)

type RouteInfo struct {
	Destination string `json:"destination"`
	Gateway     string `json:"gateway"`
	Interface   string `json:"interface"`
	Protocol    string `json:"protocol"`
}

type NetworkInfoCollector struct{}

func (c *NetworkInfoCollector) Collect() (map[string]interface{}, error) {
	// Get interfaces using netlink
	links, err := netlink.LinkList()
	if err != nil {
		return nil, err
	}

	var defaultGateway string
	var routes []RouteInfo
	var interfaces [string]interface{}

	// Process interfaces
	for _, link := range links {
		addrs, err := netlink.AddrList(link, unix.AF_UNSPEC)
		if err != nil {
			continue
		}

		// Create a map for each interface with its properties
		ifaceInfo := map[string]interface{}{
			"name":       link.Attrs().Name,
			"addresses":  addrs, // Using the netlink.Addr directly
			"macAddress": link.Attrs().HardwareAddr.String(),
		}
		interfaces = append(interfaces, ifaceInfo)
	}

	// Get routing table using netlink
	nlRoutes, err := netlink.RouteList(nil, unix.AF_UNSPEC)
	if err == nil {
		for _, route := range nlRoutes {
			var dst string
			if route.Dst == nil {
				dst = "default"
			} else {
				dst = route.Dst.String()
			}

			// Find default gateway
			if route.Dst == nil && route.Gw != nil {
				defaultGateway = route.Gw.String()
			}

			link, err := netlink.LinkByIndex(route.LinkIndex)
			ifaceName := "unknown"
			if err == nil {
				ifaceName = link.Attrs().Name
			}

			routeInfo := RouteInfo{
				Destination: dst,
				Gateway:     route.Gw.String(),
				Interface:   ifaceName,
				Protocol:    route.Protocol.String(),
			}
			routes = append(routes, routeInfo)
		}
	}

	// Get nameservers from resolv.conf
	var nameservers []string
	if file, err := os.Open("/etc/resolv.conf"); err == nil {
		defer file.Close()
		scanner := bufio.NewScanner(file)
		for scanner.Scan() {
			line := strings.TrimSpace(scanner.Text())
			if strings.HasPrefix(line, "nameserver") {
				fields := strings.Fields(line)
				if len(fields) > 1 {
					nameservers = append(nameservers, fields[1])
				}
			}
		}
	}

	return map[string]interface{}{
		"interfaces":  interfaces,
		"gateway":     defaultGateway,
		"routes":      routes,
		"nameservers": nameservers,
	}, nil
}
