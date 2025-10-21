#!/bin/bash
set -euo pipefail

echo "Installing network diagnostic tools on bastion..."
echo ""

# Update package lists
echo "Updating package lists..."
sudo apt-get update

# Install network tools
echo "Installing dnsutils (nslookup, dig), net-tools, iputils-ping..."
sudo apt-get install -y \
    dnsutils \
    net-tools \
    iputils-ping \
    traceroute \
    jq

echo ""
echo "Installation complete!"
echo ""
echo "Available tools:"
echo "  - nslookup: DNS lookup utility"
echo "  - dig: DNS lookup and debugging"
echo "  - netstat: Network statistics"
echo "  - ping: Network connectivity test"
echo "  - traceroute: Trace network route"
echo "  - jq: JSON processor"
echo ""
