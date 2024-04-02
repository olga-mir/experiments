#!/bin/bash

set -eoux pipefail

# https://cloud.google.com/secure-web-proxy/docs/overview
# https://cloud.google.com/secure-web-proxy/docs/initial-setup-steps

experiment_name="00-basic"

vpc_name=$CLUSTER_VPC # sourced in env vars
subnet_name=$CLUSTER_SUBNET

proxy_subnet_name="${vpc_name}-proxy-only-subnet"
proxy_range="172.16.0.0/26"

TEMPLATES="../manifests-templates"
RENDERED="../manifests-rendered"

export experiment_name

for template in "$TEMPLATES"/*; do
  filename=$(basename "$template")
  envsubst < "$template" > "$RENDERED/$filename"
done

policy_name=${experiment_name}-policy

policy_yaml=$RENDERED/${experiment_name}-policy.yaml
rule_yaml=$RENDERED/${experiment_name}-rule.yaml
gateway_yaml=$RENDERED/${experiment_name}-gateway.yaml


# ---------------- VPC and Subnets

# gcloud compute networks create $vpc_name --subnet-mode=custom
# gcloud compute networks subnets create $subnet_name --range=$primary_range --network=$vpc_name --region=$GCP_REGION

gcloud compute networks subnets create $proxy_subnet_name --purpose=REGIONAL_MANAGED_PROXY --role=ACTIVE --region=$GCP_REGION --network=$vpc_name --range=$proxy_range


# ---------------- Certificates

key_path="$HOME/.swp/key.pem"
cert_path="$HOME/.swp/cert.pem"
cert_name="${name}-cert"
SWP_HOST_NAME="myswp.example.com"

# openssl req -x509 -newkey rsa:2048 \
#   -keyout $key_path \
#   -out $cert_path -days 14 \
#   -subj "/CN=$SWP_HOST_NAME" -nodes -addext \
#   "subjectAltName=DNS:$SWP_HOST_NAME"
#
# gcloud certificate-manager certificates create $cert_name \
#    --certificate-file=$cert_path \
#    --private-key-file=$key_path \
#    --location=$GCP_REGION

gcloud certificate-manager certificates create $cert_name --location=$GCP_REGION --private-key-file=$key_path --certificate-file=$cert_path


# ---------------- Gateway security policy

gcloud network-security gateway-security-policies import $policy_name \
    --source=$policy_yaml \
    --location=$GCP_REGION

gcloud network-security gateway-security-policies rules import allow-wikipedia-org \
    --source=$rule_yaml \
    --location=$GCP_REGION \
    --gateway-security-policy=$policy_name


# ---------------- THE PROXY ITSELF :party: --------------

gcloud network-services gateways import test-swp \
    --source=$gateway_yaml \
    --location=$GCP_REGION
