package sysinfo

import (
	"bytes"
	"fmt"
	"os"
	"strings"

	"golang.org/x/sys/unix"
)

type UnixInfoCollector struct{}

func (c *UnixInfoCollector) Collect() (map[string]interface{}, error) {
	u := unix.Utsname{}
	if err := unix.Uname(&u); err != nil {
		return nil, fmt.Errorf("uname error: %w", err)
	}
	osInfo := map[string]interface{}{
		"name":    string(bytes.Trim(u.Sysname[:], "\x00")),
		"release": string(bytes.Trim(u.Release[:], "\x00")),
		"version": string(bytes.Trim(u.Version[:], "\x00")),
		"machine": string(bytes.Trim(u.Machine[:], "\x00")),
	}

	envVars, err := c.GetEnvVars()
	if err != nil {
		return nil, err
	}

	info := map[string]interface{}{
		"os":  osInfo,
		"env": envVars,
	}

	return info, nil
}

func (c *UnixInfoCollector) GetEnvVars() (map[string]string, error) {
	env := make(map[string]string)
	for _, e := range os.Environ() {
		if i := strings.Index(e, "="); i >= 0 {
			env[e[:i]] = e[i+1:]
		}
	}
	return env, nil
}
