 #!/bin/bash

MITMPROXY_VERSION="10.2.4"

curl https://downloads.mitmproxy.org/${MITMPROXY_VERSION}/mitmproxy-${MITMPROXY_VERSION}-linux-x86_64.tar.gz -o mitmproxy-${MITMPROXY_VERSION}-linux-x86_64.tar.gz
 
tar -xvzf mitmproxy-${MITMPROXY_VERSION}-linux-x86_64.tar.gz -C $(pwd)

