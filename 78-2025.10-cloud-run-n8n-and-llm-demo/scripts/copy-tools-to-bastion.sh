#!/bin/bash
set -euo pipefail

# Validate required environment variables
required_vars=("PROJECT_ID" "ZONE")
for var in "${required_vars[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "Error: $var environment variable is not set"
        exit 1
    fi
done

TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo "Extracting Linux tools from Debian container..."
echo "Temp directory: $TEMP_DIR"
echo ""

# Create a Dockerfile to extract the tools
cat > "$TEMP_DIR/Dockerfile" <<'EOF'
FROM debian:12-slim

RUN apt-get update && apt-get install -y \
    dnsutils \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Create a directory to collect binaries and their dependencies
RUN mkdir -p /export/bin /export/lib /export/lib64

# Copy binaries
RUN cp /usr/bin/dig /export/bin/ && \
    cp /usr/bin/nslookup /export/bin/ && \
    cp /usr/bin/curl /export/bin/ && \
    cp /usr/bin/jq /export/bin/

# Copy required shared libraries
RUN ldd /usr/bin/dig | grep "=>" | awk '{print $3}' | grep -v "^$" | xargs -I '{}' cp -v '{}' /export/lib/ 2>/dev/null || true
RUN ldd /usr/bin/curl | grep "=>" | awk '{print $3}' | grep -v "^$" | xargs -I '{}' cp -v '{}' /export/lib/ 2>/dev/null || true
RUN ldd /usr/bin/jq | grep "=>" | awk '{print $3}' | grep -v "^$" | xargs -I '{}' cp -v '{}' /export/lib/ 2>/dev/null || true

# Copy the dynamic linker
RUN cp /lib64/ld-linux-x86-64.so.2 /export/lib64/ 2>/dev/null || true
RUN cp /lib/x86_64-linux-gnu/ld-linux-x86-64.so.2 /export/lib/ 2>/dev/null || true

EOF

echo "Building container to extract tools..."
docker build -t bastion-tools "$TEMP_DIR" -q

echo "Extracting binaries from container..."
CONTAINER_ID=$(docker create bastion-tools)
docker cp "$CONTAINER_ID:/export/." "$TEMP_DIR/tools/"
docker rm "$CONTAINER_ID" > /dev/null

echo "Creating archive..."
cd "$TEMP_DIR/tools"
tar czf "$TEMP_DIR/bastion-tools.tar.gz" bin lib lib64 2>/dev/null || tar czf "$TEMP_DIR/bastion-tools.tar.gz" bin lib

echo "Copying tools to bastion..."
gcloud compute scp "$TEMP_DIR/bastion-tools.tar.gz" bastion:~ \
    --project="$PROJECT_ID" \
    --zone="$ZONE" \
    --tunnel-through-iap

echo "Extracting tools on bastion..."
gcloud compute ssh bastion --project="$PROJECT_ID" --zone="$ZONE" --tunnel-through-iap --command="
    mkdir -p ~/tools
    tar xzf ~/bastion-tools.tar.gz -C ~/tools
    echo 'export PATH=\$HOME/tools/bin:\$PATH' >> ~/.bashrc
    echo 'export LD_LIBRARY_PATH=\$HOME/tools/lib:\$LD_LIBRARY_PATH' >> ~/.bashrc
    rm ~/bastion-tools.tar.gz
    echo ''
    echo 'Tools installed! Run: source ~/.bashrc'
    echo 'Or logout and login again.'
    echo ''
    echo 'Available tools:'
    ls -1 ~/tools/bin/
"

echo ""
echo "Done! Tools copied to bastion:~/tools/"
echo ""
echo "On bastion, run: source ~/.bashrc"
echo "Then test with: dig google.com"
