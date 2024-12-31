package sysinfo

import (
	"bytes"
	"fmt"

	"golang.org/x/sys/unix"
)

type UnixInfoCollector struct{}

func (c *UnixInfoCollector) Collect() (map[string]interface{}, error) {
	u := unix.Utsname{}
	if err := unix.Uname(&u); err != nil {
		return nil, fmt.Errorf("uname error: %w", err)
	}

	info := map[string]interface{}{
		"os":      string(bytes.Trim(u.Sysname[:], "\x00")),
		"release": string(bytes.Trim(u.Release[:], "\x00")),
		"version": string(bytes.Trim(u.Version[:], "\x00")),
		"machine": string(bytes.Trim(u.Machine[:], "\x00")),
	}

	return info, nil
}
