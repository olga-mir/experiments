
# Testing GCP Secure Web Proxy (SWP)

## Goal

Test integration between GKE and SWP.

## Current state

Current example only shows very basic usage of a pod in GKE cluster connecting to outside internet via SWP. It does not include any TLS features, auth, etc

The docs are fairly straight forward for the basic POC: https://cloud.google.com/secure-web-proxy/docs/initial-setup-steps

# Deployment

## Deploy GKE Cluster

Any GKE cluster will do, I'm using this https://github.com/olga-mir/k8s/blob/main/gcp/gcloud/dpv2-create-gke-with-o11y.sh

## Deploy SWP

using script [./scripts/deploy.sh](./scripts/deploy.sh)

## Deploy Test Pod

Test pod is configured to route outgoing connections and it will perform two curl requests - one to allowed destination and one to a url which was not configured on the the SWP. The first request will result in 200, and the second one in 403.

Test pod config, (`10.0.0.9` is the IP of the SWP). Full manifest can be found [here](./pod-test-with-proxy.yaml)
```yaml
  - name: curl-container
    image: curlimages/curl
    env:
      - name: HTTP_PROXY
        value: "http://10.0.0.9:443"
      - name: HTTPS_PROXY
        value: "http://10.0.0.9:443"
      - name: NO_PROXY
        value: "localhost,127.0.0.1"
    command: ["/bin/sh"]
    args: ["-c", "(curl -fvs https://wikipedia.org --proxy-insecure || true) && (curl -fsv https://api.ipify.org || true) && sleep infinity"]
```

# Results

200 for allowed URL

403 for URL which was not whitelisted

This example does not test auth

## Pod logs

In this file [./pod-with-proxy-logs.txt](./pod-with-proxy-logs.txt) or below in expand section.

Snippet of `curl` output for a connection which was not allowed (`10.0.0.9` is my SWP IP address):

```
* Connection #0 to host 10.0.0.9 left intact
* Uses proxy env variable NO_PROXY == 'localhost,127.0.0.1'
* Uses proxy env variable HTTPS_PROXY == 'http://10.0.0.9:443'
*   Trying 10.0.0.9:443...
* Connected to 10.0.0.9 (10.0.0.9) port 443
* CONNECT tunnel: HTTP/1.1 negotiated
* allocate connect buffer
* Establish HTTP proxy tunnel to api.ipify.org:443
> CONNECT api.ipify.org:443 HTTP/1.1
```

<details>
  <summary>Click to see pod's logs</summary>

```bash
* Uses proxy env variable NO_PROXY == 'localhost,127.0.0.1'
* Uses proxy env variable HTTPS_PROXY == 'http://10.0.0.9:443'
*   Trying 10.0.0.9:443...
* Connected to 10.0.0.9 (10.0.0.9) port 443
* CONNECT tunnel: HTTP/1.1 negotiated
* allocate connect buffer
* Establish HTTP proxy tunnel to wikipedia.org:443
> CONNECT wikipedia.org:443 HTTP/1.1
> Host: wikipedia.org:443
> User-Agent: curl/8.7.1
> Proxy-Connection: Keep-Alive
>
< HTTP/1.1 200 OK
< date: Tue, 02 Apr 2024 10:32:38 GMT
<
* CONNECT phase completed
* CONNECT tunnel established, response 200
* ALPN: curl offers h2,http/1.1
} [5 bytes data]
* TLSv1.3 (OUT), TLS handshake, Client hello (1):
} [512 bytes data]
*  CAfile: /cacert.pem
*  CApath: /etc/ssl/certs
{ [5 bytes data]
* TLSv1.3 (IN), TLS handshake, Server hello (2):
{ [122 bytes data]
* TLSv1.3 (IN), TLS handshake, Encrypted Extensions (8):
{ [19 bytes data]
* TLSv1.3 (IN), TLS handshake, Certificate (11):
{ [3196 bytes data]
* TLSv1.3 (IN), TLS handshake, CERT verify (15):
{ [78 bytes data]
* TLSv1.3 (IN), TLS handshake, Finished (20):
{ [52 bytes data]
* TLSv1.3 (OUT), TLS change cipher, Change cipher spec (1):
} [1 bytes data]
* TLSv1.3 (OUT), TLS handshake, Finished (20):
} [52 bytes data]
* SSL connection using TLSv1.3 / TLS_AES_256_GCM_SHA384 / X25519 / id-ecPublicKey
* ALPN: server accepted h2
* Server certificate:
*  subject: C=US; ST=California; L=San Francisco; O=Wikimedia Foundation, Inc.; CN=*.wikipedia.org
*  start date: Oct 18 00:00:00 2023 GMT
*  expire date: Oct 16 23:59:59 2024 GMT
*  subjectAltName: host "wikipedia.org" matched cert's "wikipedia.org"
*  issuer: C=US; O=DigiCert Inc; CN=DigiCert TLS Hybrid ECC SHA384 2020 CA1
*  SSL certificate verify ok.
*   Certificate level 0: Public key type EC/prime256v1 (256/128 Bits/secBits), signed using ecdsa-with-SHA384
*   Certificate level 1: Public key type EC/secp384r1 (384/192 Bits/secBits), signed using sha384WithRSAEncryption
*   Certificate level 2: Public key type RSA (2048/112 Bits/secBits), signed using sha1WithRSAEncryption
} [5 bytes data]
* using HTTP/2
* [HTTP/2] [1] OPENED stream for https://wikipedia.org/
* [HTTP/2] [1] [:method: GET]
* [HTTP/2] [1] [:scheme: https]
* [HTTP/2] [1] [:authority: wikipedia.org]
* [HTTP/2] [1] [:path: /]
* [HTTP/2] [1] [user-agent: curl/8.7.1]
* [HTTP/2] [1] [accept: */*]
} [5 bytes data]
> GET / HTTP/2
> Host: wikipedia.org
> User-Agent: curl/8.7.1
> Accept: */*
>
* Request completely sent off
{ [5 bytes data]
* TLSv1.3 (IN), TLS handshake, Newsession Ticket (4):
{ [249 bytes data]
* TLSv1.3 (IN), TLS handshake, Newsession Ticket (4):
{ [249 bytes data]
* old SSL session ID is stale, removing
{ [5 bytes data]
<!DOCTYPE HTML PUBLIC "-//IETF//DTD HTML 2.0//EN">
<html><head>
<title>301 Moved Permanently</title>
</head><body>
<h1>Moved Permanently</h1>
<p>The document has moved <a href="https://www.wikipedia.org/">here</a>.</p>
</body></html>
< HTTP/2 301
< date: Mon, 01 Apr 2024 20:06:52 GMT
< server: mw-web.codfw.main-6cf7d57b97-qwdss
< location: https://www.wikipedia.org/
< content-length: 234
< content-type: text/html; charset=iso-8859-1
< vary: X-Forwarded-Proto
< age: 51946
< x-cache: cp5018 miss, cp5018 hit/129061
< x-cache-status: hit-front
< server-timing: cache;desc="hit-front", host;desc="cp5018"
< strict-transport-security: max-age=106384710; includeSubDomains; preload
< report-to: { "group": "wm_nel", "max_age": 604800, "endpoints": [{ "url": "https://intake-logging.wikimedia.org/v1/events?stream=w3c.reportingapi.network_error&schema_uri=/w3c/reportingapi/network_error/1.0.0" }] }
< nel: { "report_to": "wm_nel", "max_age": 604800, "failure_fraction": 0.05, "success_fraction": 0.0}
< set-cookie: WMF-Last-Access=02-Apr-2024;Path=/;HttpOnly;secure;Expires=Sat, 04 May 2024 00:00:00 GMT
< set-cookie: WMF-Last-Access-Global=02-Apr-2024;Path=/;Domain=.wikipedia.org;HttpOnly;secure;Expires=Sat, 04 May 2024 00:00:00 GMT
< x-client-ip: 34.40.134.122
< set-cookie: GeoIP=AU:NSW:Sydney:-33.87:151.20:v4; Path=/; secure; Domain=.wikipedia.org
< set-cookie: NetworkProbeLimit=0.001;Path=/;Secure;Max-Age=3600
<
{ [234 bytes data]
* Connection #0 to host 10.0.0.9 left intact
* Uses proxy env variable NO_PROXY == 'localhost,127.0.0.1'
* Uses proxy env variable HTTPS_PROXY == 'http://10.0.0.9:443'
*   Trying 10.0.0.9:443...
* Connected to 10.0.0.9 (10.0.0.9) port 443
* CONNECT tunnel: HTTP/1.1 negotiated
* allocate connect buffer
* Establish HTTP proxy tunnel to api.ipify.org:443
> CONNECT api.ipify.org:443 HTTP/1.1
> Host: api.ipify.org:443
> User-Agent: curl/8.7.1
> Proxy-Connection: Keep-Alive
>
< HTTP/1.1 403 Forbidden
< content-length: 13
< content-type: text/plain
< date: Tue, 02 Apr 2024 10:32:39 GMT
< connection: close
<
* The requested URL returned error: 403
* Closing connection
```

</details>



## SWP Access Logs Validation

Navigate to Logs Explorer and use filter:
```
resource.type="networkservices.googleapis.com/Gateway"
```

<details>
  <summary>Click to see example of ALLOWED connection request</summary>

```json
{
  "insertId": "xat9d0el4cll",
  "jsonPayload": {
    "@type": "type.googleapis.com/google.cloud.loadbalancing.type.LoadBalancerLogEntry",
    "enforcedGatewaySecurityPolicy": {
      "hostname": "wikipedia.org:443",
      "matchedRules": [
        {
          "action": "ALLOWED",
          "name": "projects/<REDACTED_PROJ_NUMBER>/locations/australia-southeast1/gatewaySecurityPolicies/basic-policy/rules/allow-wikipedia-org"
        }
      ]
    }
  },
  "httpRequest": {
    "requestMethod": "CONNECT",
    "requestSize": "916",
    "status": 200,
    "responseSize": "5505",
    "userAgent": "curl/8.7.1",
    "remoteIp": "10.224.1.34:56440",
    "serverIp": "103.102.166.224:443",
    "latency": "0.299312s",
    "protocol": "HTTP/1.1"
  },
  "resource": {
    "type": "networkservices.googleapis.com/Gateway",
    "labels": {
      "network_name": "projects/<REDACTED_PROJ_ID>/global/networks/cluster-vpc",
      "gateway_type": "SECURE_WEB_GATEWAY",
      "location": "australia-southeast1",
      "resource_container": "",
      "gateway_name": "test-swp"
    }
  },
  "timestamp": "2024-04-02T10:29:22.647294Z",
  "severity": "INFO",
  "logName": "projects/<REDACTED_PROJ_ID>/logs/networkservices.googleapis.com%2Fgateway_requests",
  "receiveTimestamp": "2024-04-02T10:29:24.457601984Z"
}
```
</details>


<details>
  <summary>Click to see example of DENIED connection request:</summary>

```json
{
  "insertId": "kjb29yeezhm4",
  "jsonPayload": {
    "@type": "type.googleapis.com/google.cloud.loadbalancing.type.LoadBalancerLogEntry",
    "enforcedGatewaySecurityPolicy": {
      "matchedRules": [
        {
          "name": "default_denied",
          "action": "DENIED"
        }
      ],
      "hostname": "api.ipify.org:443"
    }
  },
  "httpRequest": {
    "requestMethod": "CONNECT",
    "requestSize": "117",
    "status": 403,
    "responseSize": "141",
    "userAgent": "curl/8.7.1",
    "remoteIp": "10.224.1.35:53280",
    "latency": "0.002822s",
    "protocol": "HTTP/1.1"
  },
  "resource": {
    "type": "networkservices.googleapis.com/Gateway",
    "labels": {
      "network_name": "projects/<REDACTED_PROJ_ID>/global/networks/cluster-vpc",
      "location": "australia-southeast1",
      "gateway_type": "SECURE_WEB_GATEWAY",
      "resource_container": "",
      "gateway_name": "test-swp"
    }
  },
  "timestamp": "2024-04-02T10:32:39.285888Z",
  "severity": "WARNING",
  "logName": "projects/<REDACTED_PROJ_ID>/logs/networkservices.googleapis.com%2Fgateway_requests",
  "receiveTimestamp": "2024-04-02T10:32:46.535541039Z"
}
```

</details>

# Cleanup

[scripts/disable-apis.sh](./scripts/disable-apis.sh)
