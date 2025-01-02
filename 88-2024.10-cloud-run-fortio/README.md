# Cloud Run Exploration

This folder contains tools to better understand how Cloud Run works. It consists of 2 main parts - `info` service and `fortio` service.
Info service is a golang app which reads a bunch of system information and returns it as a json to the caller.
Fortio is a helper service used to invoke Cloud Run apps and observe different behaviours.

## Observations

View output collected from inside a CloudRun service in [./docs/cloudrun-info-dump.json](./docs/cloudrun-info-dump.json)



## Common Tasks

`task help` to see all available operations

`task deploy-info` to build image, setup IAM and deploy `info` serevice Cloud Run


## License

Root repo: https://github.com/olga-mir/experiments/blob/main/LICENSE