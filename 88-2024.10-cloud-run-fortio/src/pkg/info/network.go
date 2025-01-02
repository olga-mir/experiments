package sysinfo

import (
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

	var interfaces []map[string]interface{}
	for _, link := range links {
		addrs, err := netlink.AddrList(link, unix.AF_UNSPEC)
		if err != nil {
			continue
		}

		ifaceInfo := map[string]interface{}{
			"name":       link.Attrs().Name,
			"macAddress": link.Attrs().HardwareAddr.String(),
			"addresses":  make([]map[string]interface{}, 0, len(addrs)),
		}

		for _, addr := range addrs {
			addrMap := map[string]interface{}{
				"ip":   addr.IP.String(),
				"mask": addr.Mask.String(),
				//"prefixLen": maskToPrefixLen(addr.Mask),
				"scope": addr.Scope,
			}

			if addr.Broadcast != nil {
				addrMap["broadcast"] = addr.Broadcast.String()
			}

			// Label like "ipvlan-eth0"
			if addr.Label != "" {
				addrMap["label"] = addr.Label
			}

			ifaceInfo["addresses"] = append(ifaceInfo["addresses"].([]map[string]interface{}), addrMap)
		}

		interfaces = append(interfaces, ifaceInfo)
	}

	// Get routing table using netlink
	var routes []RouteInfo
	var defaultGateway string
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

	readFileContent := func(path string) ([]string, error) {
		content, err := os.ReadFile(path)
		if err != nil {
			return nil, err
		}
		return strings.Split(strings.TrimSpace(string(content)), "\n"), nil
	}

	resolvConf, _ := readFileContent("/etc/resolv.conf")
	etcHosts, _ := readFileContent("/etc/hosts")
	nsSwitch, _ := readFileContent("/etc/nsswitch.conf")
	containerEnv, _ := readFileContent("/.dockerenv")
	cgroups, _ := readFileContent("/proc/1/cgroup")
	mountInfo, _ := readFileContent("/proc/mounts")
	limits, _ := readFileContent("/proc/self/limits")

	return map[string]interface{}{
		"interfaces": interfaces,
		"gateway":    defaultGateway,
		"routes":     routes,
		"dns": map[string]interface{}{
			"resolv_conf": resolvConf,
			"etc_hosts":   etcHosts,
			"nsswitch":    nsSwitch,
		},
		"system": map[string]interface{}{
			"mounts":       mountInfo,
			"cgroups":      cgroups,
			"limits":       limits,
			"is_container": containerEnv != nil,
		},
	}, nil
}
