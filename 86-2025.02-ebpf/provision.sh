#!/bin/bash
set -euo pipefail

# This script provisions a GKE cluster with a specific tainted nodepool.
# Requires environment variables: PROJECT_ID, ZONE, CLUSTER_NAME

PROJECT_ID="${PROJECT_ID:?'PROJECT_ID environment variable is required'}"
ZONE="${ZONE:?'ZONE environment variable is required'}"
CLUSTER_NAME="${CLUSTER_NAME:?'CLUSTER_NAME environment variable is required'}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Configuring gcloud for project ${PROJECT_ID}..."
gcloud config set project "${PROJECT_ID}"

echo "Creating GKE cluster ${CLUSTER_NAME} in ${ZONE}..."
# Create a zonal cluster.
gcloud container clusters create "${CLUSTER_NAME}" \
    --zone "${ZONE}" \
    --num-nodes 1 \
    --release-channel "regular" \
    --workload-pool="${PROJECT_ID}.svc.id.goog" \
    --enable-managed-prometheus \
    --enable-ip-alias \
    --machine-type "e2-medium" \
    --disk-type="pd-standard" \
    --disk-size=50

echo "Creating tainted nodepool for testing (2 vCPU, static CPU Manager)..."
# e2-standard-2 (2 vCPU). Taint + label so only our test workloads land here.
# --system-config-from-file turns on kubelet cpuManagerPolicy: static, which lets
# the ballast DaemonSet (k8s/ballast.yaml) claim one exclusive core per node and
# confine the noisy-neighbour experiment to the remaining shared CPU.
gcloud container node-pools create "test-pool" \
    --cluster="${CLUSTER_NAME}" \
    --zone="${ZONE}" \
    --machine-type="e2-standard-2" \
    --num-nodes=1 \
    --node-taints="dedicated=noisy-node:NoSchedule" \
    --node-labels="workload=noisy-node" \
    --system-config-from-file="${SCRIPT_DIR}/gke-node-system-config.yaml" \
    --enable-autoscaling --min-nodes=1 --max-nodes=3 \
    --disk-type="pd-standard" \
    --disk-size=50

echo "Fetching cluster credentials..."
gcloud container clusters get-credentials "${CLUSTER_NAME}" --zone="${ZONE}"

echo "Cluster ${CLUSTER_NAME} provisioned successfully."
echo "Next: kubectl apply -f k8s/ballast.yaml   # pins 1 core per node via static CPU Manager"
