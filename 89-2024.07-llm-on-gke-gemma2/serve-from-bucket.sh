#!/bin/bash

set -eoux pipefail

## MODEL_PATH=""
BUCKET_NAME="llm-models-369"
BUCKET_PATH="${BUCKET_NAME}/gemma-2b-it/gemma-2b-it/"

# upload model to bucket
# gsutil cp -r $MODEL_PATH gs://$BUCKET_PATH

# Federated WLI

ns_sa_name="ai-apps"

# gcloud iam service-accounts create $ns_sa_name --project=$PROJECT_ID
# gsutil iam ch serviceAccount:${ns_sa_name}@${PROJECT_ID}.iam.gserviceaccount.com:roles/storage.objectViewer gs://$BUCKET_NAME

kubectl annotate ns ai-apps iam.gke.io/gcp-service-account=ai-apps@${PROJECT_ID}.iam.gserviceaccount.com



# apiVersion: v1
# kind: Namespace
# metadata:
#   name: your-namespace
#   annotations:
#     iam.gke.io/gcp-service-account: namespace-default-gsa@PROJECT_ID.iam.gserviceaccount.com

# change app:
# spec:
#   template:
#     spec:
#       containers:
#       - name: model-container
#         image: your-image
#         volumeMounts:
#         - name: model-data
#           mountPath: /path/to/model
#       volumes:
#       - name: model-data
#         emptyDir: {}
#       initContainers:
#       - name: init-model
#         image: google/cloud-sdk
#         command: ["gsutil", "cp", "gs://your-model-bucket/model-file", "/path/to/model/model-file"]
#         volumeMounts:
#         - name: model-data
#           mountPath: /path/to/model
# 
