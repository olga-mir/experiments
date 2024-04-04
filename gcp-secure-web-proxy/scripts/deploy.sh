#!/bin/bash

set -eoux pipefail

# https://cloud.google.com/secure-web-proxy/docs/overview
# https://cloud.google.com/secure-web-proxy/docs/initial-setup-steps

# resource name should start with a letter and can only have lowercase letters, numbers, hyphens and at most 63 characters
# experiment_name="basic"
experiment_name="with-sa"

vpc_name=$CLUSTER_VPC # sourced in env vars
subnet_name=$CLUSTER_SUBNET

gsa_email="test-vm-swp@${PROJECT_ID}.iam.gserviceaccount.com"

TEMPLATES="../manifests-templates"
RENDERED="../manifests-rendered"

export experiment_name vpc_name subnet_name gsa_email

for template in "$TEMPLATES"/*; do
  filename=$(basename "$template")
  envsubst < "$template" > "$RENDERED/$filename"
done

policy_name=${experiment_name}-policy

policy_yaml=$RENDERED/${experiment_name}-policy.yaml
rule_yaml=$RENDERED/${experiment_name}-rule.yaml
gateway_yaml=$RENDERED/${experiment_name}-gateway.yaml

main() {

# Check if an argument is provided
if [ $# -eq 0 ]; then
    echo "No arguments provided"
    show_help
    exit 1
fi

case "$1" in
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
      generate_certs
      install_policies
      install_rules
      install_proxy
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


# ---------------- Certificates
generate_certs() {
  key_path="$HOME/.swp/key.pem"
  cert_path="$HOME/.swp/cert.pem"
  cert_name="${experiment_name}-cert"
  SWP_HOST_NAME="myswp.example.com"
  days=30
  # openssl req -x509 -newkey rsa:2048 \
  #   -keyout $key_path \
  #   -out $cert_path -days $days \
  #   -subj "/CN=$SWP_HOST_NAME" -nodes -addext \
  #   "subjectAltName=DNS:$SWP_HOST_NAME"

  # gcloud certificate-manager certificates create $cert_name \
  #    --certificate-file=$cert_path \
  #    --private-key-file=$key_path \
  #    --location=$GCP_REGION

  gcloud certificate-manager certificates create $cert_name --location=$GCP_REGION --private-key-file=$key_path --certificate-file=$cert_path
}


# ---------------- Gateway security policy
install_policies() {
  gcloud network-security gateway-security-policies import $policy_name \
      --source=$policy_yaml \
      --location=$GCP_REGION
}

install_rules() {
  gcloud network-security gateway-security-policies rules import allow-wikipedia-org \
      --source=$rule_yaml \
      --location=$GCP_REGION \
      --gateway-security-policy=$policy_name
}


# ---------------- THE PROXY ITSELF :party: --------------
install_proxy() {
  gcloud network-services gateways import test-swp \
      --source=$gateway_yaml \
      --location=$GCP_REGION
}

main "$@"

# ---------------- VPC and Subnets

# proxy_subnet_name="${vpc_name}-proxy-only-subnet"
# gcloud compute networks create $vpc_name --subnet-mode=custom
# gcloud compute networks subnets create $subnet_name --range=$primary_range --network=$vpc_name --region=$GCP_REGION
# gcloud compute networks subnets create $proxy_subnet_name --purpose=REGIONAL_MANAGED_PROXY --role=ACTIVE --region=$GCP_REGION --network=$vpc_name --range=$proxy_range

