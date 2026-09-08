#!/bin/bash
set -euo pipefail

# This script provisions a GKE cluster with a specific tainted nodepool.
# Requires environment variables: PROJECT_ID, ZONE, CLUSTER_NAME

PROJECT_ID="${PROJECT_ID:?'PROJECT_ID environment variable is required'}"
ZONE="${ZONE:?'ZONE environment variable is required'}"
CLUSTER_NAME="${CLUSTER_NAME:?'CLUSTER_NAME environment variable is required'}"

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

echo "Creating tainted nodepool for testing (2 CPUs, Static CPU Manager)..."
# Create a nodepool with e2-standard-2 (2 CPUs)
# Add a taint so only our test workloads run there.
gcloud container node-pools create "test-pool" \
    --cluster="${CLUSTER_NAME}" \
    --zone="${ZONE}" \
    --machine-type="e2-standard-2" \
    --num-nodes=1 \
    --node-taints="dedicated=noisy-node:NoSchedule" \
    --node-labels="workload=noisy-node" \
    --enable-autoscaling --min-nodes=1 --max-nodes=3 \
    --disk-type="pd-standard" \
    --disk-size=50

echo "Fetching cluster credentials..."
gcloud container clusters get-credentials "${CLUSTER_NAME}" --zone="${ZONE}"

echo "Cluster ${CLUSTER_NAME} provisioned successfully."
