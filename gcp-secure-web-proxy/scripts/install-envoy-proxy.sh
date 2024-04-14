#!/bin/bash

set -eoux pipefail

SCRIPT_DIR=$(dirname "$(realpath "$0")")
envoy_config_filepath="$SCRIPT_DIR/envoy-config.yaml"

main() {
  # install_envoy

  write_config_file

  run_envoy
}

run_envoy() {
  envoy -c $envoy_config_filepath --log-level debug
}

install_envoy() {
  # Below instructions are from official envoy site: https://www.envoyproxy.io/docs/envoy/latest/start/install#install-envoy-on-debian-gnu-linux
  # There is also a section on installing Envoy on GCP infra here: https://cloud.google.com/traffic-director/docs/set-up-gce-vms

  sudo apt update
  sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl lsb-release
  curl -sL 'https://deb.dl.getenvoy.io/public/gpg.8115BA8E629CC074.key' | sudo gpg --dearmor -o /usr/share/keyrings/getenvoy-keyring.gpg
  echo a077cb587a1b622e03aa4bf2f3689de14658a9497a9af2c427bba5f4cc3c4723 /usr/share/keyrings/getenvoy-keyring.gpg | sha256sum --check
  echo "deb [arch=amd64 signed-by=/usr/share/keyrings/getenvoy-keyring.gpg] https://deb.dl.getenvoy.io/public/deb/debian $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/getenvoy.list
  sudo apt update
  sudo apt install getenvoy-envoy -y
}


write_config_file() {
# Config
  cat << EOF > $envoy_config_filepath
  static_resources:
    listeners:
    - name: listener_0
      address:
        socket_address:
          address: 0.0.0.0
          port_value: 8888
      filter_chains:
      - filters:
        - name: envoy.filters.network.http_connection_manager
          typed_config:
            "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
            stat_prefix: ingress_http
            access_log:
            - name: envoy.access_loggers.stdout
              typed_config:
                "@type": type.googleapis.com/envoy.extensions.access_loggers.stream.v3.StdoutAccessLog
                log_format:
                  text_format: |
                    "[%START_TIME%] \"%REQ(:METHOD)% %REQ(:PATH)% %PROTOCOL%\" %RESPONSE_CODE% %RESPONSE_FLAGS% %BYTES_RECEIVED% %BYTES_SENT% %DURATION% %RESP(X-ENVOY-UPSTREAM-SERVICE-TIME)%
                    'x-forwarded-for': '%REQ(x-forwarded-for)%', 'user-agent': '%REQ(USER-AGENT)%', 'referer': '%REQ(referer)%', 'authorization': '%REQ(Authorization)%'
                    'request-id': '%REQ(X-REQUEST-ID)%', 'authority': '%REQ(:AUTHORITY)%', 'upstream-host': '%UPSTREAM_HOST%'
                    'response-content-type': '%RESP(CONTENT-TYPE)%', 'response-server': '%RESP(SERVER)%'
                    'all-request-headers': '%REQ(ALL_HEADERS)%', 'all-response-headers': '%RESP(ALL_HEADERS)%'\n"
            codec_type: AUTO
            route_config:
              name: local_route
              virtual_hosts:
              - name: local_service
                domains: ["*"]
                routes:
                - match:
                    prefix: "/"
                  route:
                    cluster: service_google
            http_filters:
            - name: envoy.filters.http.dynamic_forward_proxy
              typed_config:
                "@type": type.googleapis.com/envoy.extensions.filters.http.dynamic_forward_proxy.v3.FilterConfig
                dns_cache_config:
                  name: dynamic_forward_proxy_cache_config
                  dns_lookup_family: V4_ONLY
            - name: envoy.filters.http.router
    clusters:
    - name: service_google
      connect_timeout: 0.25s
      type: LOGICAL_DNS
      # This should be set to the DNS address of the service you are trying to reach
      lb_policy: ROUND_ROBIN
      load_assignment:
        cluster_name: service_google
        endpoints:
        - lb_endpoints:
          - endpoint:
              address:
                socket_address:
                  address: www.googleapis.com
                  port_value: 443
      transport_socket:
        name: envoy.transport_sockets.tls
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.transport_sockets.tls.v3.UpstreamTlsContext
          sni: www.googleapis.com
EOF
}


main "$@"

