
export VPC_NAME="main-vpc"

gcloud compute networks create $VPC_NAME --subnet-mode=custom
gcloud compute networks subnets create apps-dev \
    --network=$VPC_NAME \
    --range=10.10.0.0/20 \
    --region=australia-southeast1

gcloud compute networks subnets create apps-prod \
    --network=$VPC_NAME \
    --range=10.10.16.0/20 \
    --region=australia-southeast1

