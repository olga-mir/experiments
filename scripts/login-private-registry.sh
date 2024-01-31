#/bin/bash

# Login on desktop:
# aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

NAMESPACE=${1-test}

kubectl create secret docker-registry ecr-login -n $NAMESPACE \
  --docker-server=$ECR_REGISTRY \
  --docker-password=$(aws ecr get-login-password) \
  --docker-username=AWS 
