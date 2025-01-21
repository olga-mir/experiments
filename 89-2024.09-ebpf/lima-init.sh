#!/bin/bash

# Run this script inside Lima instance as a root to setup required tools

# TODO - this script is a temporary measure.
# parts of it need to move to lima config file
# and some parts like task and gcloud can be eliminated

set -eoux pipefail

install -m 0755 -d /etc/apt/keyrings

curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | sudo tee -a /etc/apt/sources.list.d/google-cloud-sdk.list

curl -fsSL "https://download.docker.com/linux/ubuntu/gpg" -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=amd64 signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu oracular stable" > /etc/apt/sources.list.d/docker.list

echo "MARKER1: Running apt-get update"
DEBIAN_FRONTEND=noninteractive apt-get -y -qq update >/dev/null

echo "MARKER2: Installing docker"
# trying any spell under the sun to prevent interactive inputs since they are not possible inside lima
echo 'containerd.io config.toml keep' | sudo debconf-set-selections
echo 'N' | sudo dpkg-divert --local --rename --add /etc/containerd/config.toml
# excluded containerd, but it will be re-installed anyway as a dependency.
DEBIAN_FRONTEND=noninteractive apt-get -y -q -o Dpkg::Options::="--force-confold" install docker-ce docker-ce-cli docker-compose-plugin docker-ce-rootless-extras docker-buildx-plugin

echo "MARKER3: Installing gcloud"
DEBIAN_FRONTEND=noninteractive apt-get -y -q install google-cloud-cli

echo "MARKER4: Docker and gcloud installation complete"

# Install Task
curl -sL https://taskfile.dev/install.sh | sh
install -m 0755 ./bin/task /usr/local/bin/task
rm -rf ./bin
