# Cloud Run Exploration Tools

This project contains tools and services for exploring and understanding Google Cloud Run better. It provides various utilities for testing, monitoring, and experimenting with Cloud Run services.

## Prerequisites

- Go 1.21 or later
- Task (taskfile) - Install from https://taskfile.dev
- Google Cloud SDK
- Docker
- Access to a Google Cloud Project

## Available Services

### cloudrun-info
A diagnostic service that provides detailed information about the Cloud Run environment. It exposes:
- Environment variables
- Network configuration
- System information
- File contents (/etc/hosts, resolv.conf)
- Expanded as needed
- eBPF ... when and if :D

## Common Tasks

`task help` to see all available operations

## Project Structure

- `/src` - Source code for all services
- `/scripts` - Deployment and utility scripts
- `/tests` - Test scripts
- `/docs` - Project documentation

```

├── Taskfile.yaml
├── scripts
│   ├── deploy-bastion.sh
│   └── deploy.sh
├── src
│   ├── Dockerfile
│   ├── go.mod
│   ├── main.go
│   └── pkg
│       └── info
│           └── info.go
├─── docs/  # docs and some output snippets that provide insights into Cloud Run environment
│    └── ...
└── tests
    └── basic.sh
```

## License

Root repo: https://github.com/olga-mir/experiments/blob/main/LICENSE

