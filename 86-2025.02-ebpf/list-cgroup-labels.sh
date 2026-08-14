#!/usr/bin/env bash
# List all Kubernetes pods grouped by Node, alongside their eBPF cgroup format:
# pod/<pod-uid-first-8-chars>/<container-id-first-8-chars>

set -euo pipefail

echo "Fetching pods across all namespaces..."
echo ""

kubectl get pods -A -o json | jq -r '
  .items[] |
  .spec.nodeName as $node |
  .metadata.namespace as $ns |
  .metadata.name as $pod |
  (.metadata.uid | gsub("_"; "-") | .[0:8]) as $shortUid |
  (.status.containerStatuses // [])[] |
  .name as $cName |
  (.containerID // "") as $cIDFull |
  (($cIDFull | sub("^.+://"; "") | sub("^cri-containerd-"; "") | sub("^docker-"; "") | .[0:8])) as $shortCid |
  "Node: \($node)\tNamespace: \($ns)\tPod: \($pod)\tContainer: \($cName)\teBPF Label: pod/\($shortUid)/\($shortCid)"
' | sort | column -t -s $'\t'
