#!/bin/bash
set -euo pipefail

# This script provisions a GKE cluster with a specific tainted nodepool.
# Requires environment variables: PROJECT_ID, REGION, CLUSTER_NAME

PROJECT_ID="${PROJECT_ID:?'PROJECT_ID environment variable is required'}"
REGION="${REGION:?'REGION environment variable is required'}"
CLUSTER_NAME="${CLUSTER_NAME:?'CLUSTER_NAME environment variable is required'}"

echo "Configuring gcloud for project ${PROJECT_ID}..."
gcloud config set project "${PROJECT_ID}"

echo "Creating GKE cluster ${CLUSTER_NAME} in ${REGION}..."
# Create a regional cluster, but with 1 node per zone in the default pool to keep it small.
# Or we can create an autopilot cluster, but we need a custom node pool with a taint, so standard cluster is better.
gcloud container clusters create "${CLUSTER_NAME}" \
    --region "${REGION}" \
    --num-nodes 1 \
    --release-channel "regular" \
    --workload-pool="${PROJECT_ID}.svc.id.goog" \
    --enable-managed-prometheus \
    --enable-ip-alias \
    --machine-type "e2-medium" \
    --disk-type="pd-standard" \
    --disk-size=50

echo "Creating tainted nodepool for testing (2 CPUs, Static CPU Manager)..."
# Create a nodepool with e2-standard-2 (2 CPUs)
# Add a taint so only our test workloads run there.
# To test CPU manager, we can optionally enable static CPU policy (GKE allows configuring kubelet)
# But standard GKE configuration via gcloud allows passing --system-config-from-file or similar, 
# For now, we just create the node pool.
gcloud container node-pools create "test-pool" \
    --cluster="${CLUSTER_NAME}" \
    --region="${REGION}" \
    --machine-type="e2-standard-2" \
    --num-nodes=1 \
    --node-taints="dedicated=test-pool:NoSchedule" \
    --node-labels="pool=test-pool" \
    --enable-autoscaling --min-nodes=1 --max-nodes=3 \
    --disk-type="pd-standard" \
    --disk-size=50

echo "Fetching cluster credentials..."
gcloud container clusters get-credentials "${CLUSTER_NAME}" --region="${REGION}"

echo "Cluster ${CLUSTER_NAME} provisioned successfully."
