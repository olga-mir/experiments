{
  "ingress": "INGRESS_TRAFFIC_INTERNAL_ONLY",
  "template": {
    "serviceAccount": "${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com",
    "executionEnvironment": "EXECUTION_ENVIRONMENT_GEN2",
    "maxInstanceRequestConcurrency": 80,
    "timeout": "300s",
    "scaling": {
      "maxInstanceCount": 10
    },
    "vpcAccess": {
      "networkInterfaces": [
        {
          "network": "${VPC_URI}",
          "subnetwork": "${SUBNET_URI}",
          "tags": [
            "cloudrun-service",
            "allow-egress",
            "env-staging"
          ]
        }
      ]
    },
    "containers": [
      {
        "image": "fortio/fortio",
        "ports": [
          {
            "containerPort": 8080
          }
        ],
        "resources": {
          "limits": {
            "cpu": "1",
            "memory": "512Mi"
          }
        },
        "startupProbe": {
          "timeoutSeconds": 240,
          "periodSeconds": 240,
          "failureThreshold": 1,
          "tcpSocket": {
            "port": 8080
          }
        }
      }
    ]
  },
  "traffic": [
    {
      "type": "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST",
      "percent": 100,
      "tag": "src-fortio"
    },
    {
      "type": "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST",
      "percent": 0,
      "tag": "all-cloudruns"
    }
  ]
}
