#!/bin/bash
set -euo pipefail

# Validate required environment variables
required_vars=("PROJECT_ID" "ZONE" "SUBNETWORK" "REGION")
for var in "${required_vars[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "Error: $var environment variable is not set"
        exit 1
    fi
done

TEMP_VM="temp-tools-vm"

echo "Creating temporary VM with external IP..."
echo "Project: $PROJECT_ID"
echo "Zone: $ZONE"
echo ""

# Create temporary VM with external IP
gcloud compute instances create "$TEMP_VM" \
    --project="$PROJECT_ID" \
    --zone="$ZONE" \
    --machine-type="e2-micro" \
    --subnet="$SUBNETWORK" \
    --image-family="debian-12" \
    --image-project="debian-cloud" \
    --metadata="enable-oslogin=true" \
    --scopes="cloud-platform" \
    --tags="allow-iap"

echo ""
echo "Waiting for VM to be ready..."
sleep 20

echo "Installing tools on temporary VM..."
gcloud compute ssh "$TEMP_VM" \
    --project="$PROJECT_ID" \
    --zone="$ZONE" \
    --tunnel-through-iap \
    --command='sudo apt-get update && sudo apt-get install -y dnsutils net-tools iputils-ping traceroute jq curl'

echo ""
echo "Creating tools package..."
gcloud compute ssh "$TEMP_VM" \
    --project="$PROJECT_ID" \
    --zone="$ZONE" \
    --tunnel-through-iap \
    --command='
        mkdir -p ~/tools-export/bin ~/tools-export/lib ~/tools-export/lib64

        # Copy binaries
        sudo cp /usr/bin/dig ~/tools-export/bin/
        sudo cp /usr/bin/nslookup ~/tools-export/bin/
        sudo cp /usr/bin/curl ~/tools-export/bin/
        sudo cp /usr/bin/jq ~/tools-export/bin/
        sudo cp /bin/ping ~/tools-export/bin/
        sudo cp /usr/bin/traceroute ~/tools-export/bin/
        sudo cp /bin/netstat ~/tools-export/bin/ 2>/dev/null || sudo cp /usr/bin/netstat ~/tools-export/bin/

        # Make binaries readable
        sudo chmod +r ~/tools-export/bin/*
        sudo chown -R $USER:$USER ~/tools-export/

        # Get all shared library dependencies
        for binary in ~/tools-export/bin/*; do
            ldd "$binary" 2>/dev/null | grep "=>" | awk "{print \$3}" | grep -v "^$" | while read lib; do
                if [ -f "$lib" ]; then
                    sudo cp -n "$lib" ~/tools-export/lib/ 2>/dev/null || true
                fi
            done
        done

        # Copy dynamic linker
        sudo cp /lib64/ld-linux-x86-64.so.2 ~/tools-export/lib64/ 2>/dev/null || true
        sudo cp /lib/x86_64-linux-gnu/ld-*.so.* ~/tools-export/lib/ 2>/dev/null || true

        sudo chown -R $USER:$USER ~/tools-export/

        # Create tarball
        cd ~/tools-export
        tar czf ~/tools.tar.gz bin lib lib64

        echo "Tools package created: ~/tools.tar.gz"
    '

echo ""
echo "Copying tools package from temp VM to local machine..."
LOCAL_TOOLS_DIR="$PWD/bastion-tools"
mkdir -p "$LOCAL_TOOLS_DIR"

gcloud compute scp "$TEMP_VM":~/tools.tar.gz "$LOCAL_TOOLS_DIR/" \
    --project="$PROJECT_ID" \
    --zone="$ZONE" \
    --tunnel-through-iap

echo ""
echo "Extracting tools locally for inspection..."
cd "$LOCAL_TOOLS_DIR"
tar xzf tools.tar.gz

echo ""
echo "Tools extracted to: $LOCAL_TOOLS_DIR"
echo "Available binaries:"
ls -1 "$LOCAL_TOOLS_DIR/bin/"

echo ""
echo "=== SUCCESS ==="
echo "Tools have been extracted to: $LOCAL_TOOLS_DIR"
echo ""
echo "Files:"
echo "  - tools.tar.gz (archive)"
echo "  - bin/ (binaries)"
echo "  - lib/ (libraries)"
echo ""
echo "To delete the temporary VM, run:"
echo "  gcloud compute instances delete $TEMP_VM --project=$PROJECT_ID --zone=$ZONE --quiet"
echo ""
echo "To copy tools to bastion later:"
echo "  gcloud compute scp $LOCAL_TOOLS_DIR/tools.tar.gz bastion:~ --project=$PROJECT_ID --zone=$ZONE --tunnel-through-iap"
echo "  gcloud compute ssh bastion --project=$PROJECT_ID --zone=$ZONE --tunnel-through-iap --command='tar xzf tools.tar.gz && echo \"export PATH=\\\$HOME/bin:\\\$PATH\" >> ~/.bashrc && echo \"export LD_LIBRARY_PATH=\\\$HOME/lib:\\\$LD_LIBRARY_PATH\" >> ~/.bashrc'"
