#!/bin/bash

set -eou pipefail

# https://cloud.google.com/secure-web-proxy/docs/overview
# https://cloud.google.com/secure-web-proxy/docs/initial-setup-steps

vpc_name=$CLUSTER_VPC # sourced in env vars
subnet_name=$CLUSTER_SUBNET

# gsa_email="test-vm-swp@${PROJECT_ID}.iam.gserviceaccount.com"
# TODO: sa=""

SCRIPT_DIR=$(dirname "$(realpath "$0")")
TEMPLATES="$SCRIPT_DIR/../manifests-templates"
RENDERED="$SCRIPT_DIR/../manifests-rendered"

export vpc_name subnet_name sa

for template in "$TEMPLATES"/*; do
  filename=$(basename "$template")
  envsubst < "$template" > "$RENDERED/$filename"
done

# gcloud: resource id must consists of no more than 63 characters: lower case letters, digits and hyphens

# 1 Gateway : 1 Policy : N Rules
policy_name=swp-policy
cert_name=swp-cert

set -x

main() {

# Check if an argument is provided
if [ $# -eq 0 ]; then
    echo "No arguments provided"
    show_help
    exit 1
fi

case "$1" in
    enable_apis)
      enable_apis
        ;;
    generate_certs)
      generate_certs
        ;;
    install_policies)
      install_policies
        ;;
    install_rules)
      install_rules
        ;;
    install_proxy)
      install_proxy
        ;;
    all)
      enable_apis
      generate_certs
      install_policies
      install_rules
      install_proxy
        ;;
    cleanup)
      cleanup
        ;;
    -h|--help)
        show_help
        ;;
    *)
        echo "Invalid option: $1"
        show_help
        exit 1
        ;;
esac
}

# Help function to display available options
show_help() {
    echo "Usage: $0 [option]"
    echo "Most common options:"
    echo "  enable_apis"
    echo "  all"
    echo "  cleanup"
    echo "Or any other function defined in this file"
}


# ---------------- Certificates
generate_certs() {
  key_path="$HOME/.swp/key.pem"
  cert_path="$HOME/.swp/cert.pem"
  SWP_HOST_NAME="myswp.example.com"
  days=30
  openssl req -x509 -newkey rsa:2048 \
    -keyout $key_path \
    -out $cert_path -days $days \
    -subj "/CN=$SWP_HOST_NAME" -nodes -addext \
    "subjectAltName=DNS:$SWP_HOST_NAME"

  gcloud certificate-manager certificates create $cert_name \
     --certificate-file=$cert_path \
     --private-key-file=$key_path \
     --location=$GCP_REGION
}


# ---------------- Gateway security policy
install_policies() {
  gcloud network-security gateway-security-policies import $policy_name \
      --source=$RENDERED/policy.yaml \
      --location=$GCP_REGION
}

install_rules() {
    for rule_yaml in $RENDERED/rule-*.yaml; do
        rule_name=$(basename "$rule_yaml" .yaml)
        gcloud network-security gateway-security-policies rules import "$rule_name" \
            --source="$rule_yaml" \
            --location="$GCP_REGION" \
            --gateway-security-policy="$policy_name"
    done
}

# ---------------- Secure Web Proxy
install_proxy() {
  gcloud network-services gateways import swp \
      --source=$RENDERED/gateway.yaml \
      --location=$GCP_REGION
}

enable_apis() {
  gcloud services enable networksecurity.googleapis.com
  gcloud services enable certificatemanager.googleapis.com
  gcloud services enable networkservices.googleapis.com
}

cleanup() {
  rm $RENDERED/*

  echo Deleting resources and disabling the APIs
  gcloud certificate-manager certificates delete $cert_name --location=$GCP_REGION -q
  gcloud network-services gateways delete swp --location=$GCP_REGION -q
  gcloud network-security gateway-security-policies delete $policy_name --location=$GCP_REGION -q

  sleep 250
  gcloud services disable --force networksecurity.googleapis.com
  gcloud services disable --force networkservices.googleapis.com
  gcloud services disable --force certificatemanager.googleapis.com
}

main "$@"


# ---------------- VPC and Subnets
# proxy_subnet_name="${vpc_name}-proxy-only-subnet"
# gcloud compute networks create $vpc_name --subnet-mode=custom
# gcloud compute networks subnets create $subnet_name --range=$primary_range --network=$vpc_name --region=$GCP_REGION
# gcloud compute networks subnets create $proxy_subnet_name --purpose=REGIONAL_MANAGED_PROXY --role=ACTIVE --region=$GCP_REGION --network=$vpc_name --range=$proxy_range

