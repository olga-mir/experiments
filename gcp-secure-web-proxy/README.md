
# GCP Secure Web Proxy (SWP)

## Purpose

Test integration between GKE and SWP.

*In scope*: Exploring `SessionMatcher` and `ApplicationMatcher` capabilities of SWP, in particular tags and Service Accounts
*Out of scope*: Routing, cross-project, cross-vpc. In this scenario GKE, VMs and SWP are all deployed in the same subnet

As of now GKE WLI is not supported in SWP and there is no public information when it might be, latest confirmation from Google staff in googlecommunity dated Feb 2024. [Post](https://www.googlecloudcommunity.com/gc/General-Misc-Q-A/How-do-Secure-Web-Proxy-rules-filter-requests-sent-by-containers/m-p/615769#M1189)


## Deployment

Deployment scripts located in [./scripts](./scripts) directory.

Deploy and configure Secure Web Proxy, enable required APIs if not enabled:
```
% ./scripts/deploy.sh all
```

Deploy (Spot) VMs, including [mitmproxy](https://github.com/mitmproxy/mitmproxy) for deepdive:
```
% ./scripts/deploy-test-vms.sh
```

Cleanup, including disabling APIs to avoid accidental charges:
```
% ./scripts/deploy.sh cleanup
```

GKE cluster. Any GKE cluster with WLI will do, I'm using a cluster from other project: https://github.com/olga-mir/k8s/blob/main/gcp/gcloud/dpv2-create-gke-with-o11y.sh


## Useful Commands And Understanding Logs

Test that this process is linked correctly to the intended credentials. Two commands achieve the same but via different tools.
```
% curl -X GET -H "Authorization: Bearer $(gcloud auth print-access-token)" https://storage.googleapis.com/storage/v1/b/<BUCKET>/o
% gcloud storage ls gs://<BUCKET> --verbosity=debug
```

Check what Service Account is associated to the caller process:
```
% curl -H "Metadata-Flavor: Google" "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email"
```

Get token info:
```
% TOKEN=$(gcloud auth print-access-token)
% curl "https://www.googleapis.com/oauth2/v3/tokeninfo?access_token=$TOKEN"
```

Send HTTP requests via proxy.

In a pod this can be configured directly in the manifest:
```yaml
  containers:
  - name: test
    image: google/cloud-sdk:slim
    env:
      - name: HTTP_PROXY
        value: "http://10.0.0.9:443"
      - name: HTTPS_PROXY
        value: "http://10.0.0.9:443"
      - name: NO_PROXY
        value: "localhost,127.0.0.1,metadata.google.internal,.googleapis.com,accounts.google.com"
```

In curl use `-x` flag to specify proxy:
```
```



## VM Test

See in [test-swp-with-vm-sa.md](./test-swp-with-vm-sa.md)

## GKE

Required k8s manifests can be found in [./k8s-manifests](./k8s-manifests)

* limited / admin - Limited means there is either no corresponding GSA or it is not granted any priviledges and does not have any rules configured in SWP.
* ksa2gsa / federated - WLI in GKE can be achieved in one of two ways - Federated or explicit GSA and linking of KSA to that GSA via annotation on KSA resource. The former is a more lightweight and conveninent way, but not every GCP service supports it, it also lacks VPCSC support and is not supported in SWP either. For more info https://cloud.google.com/kubernetes-engine/docs/concepts/workload-identity. Therefore in this exercise we'll explore only non-federated aproach with explicit GSA, all related resources will be named 'ksa2gsa' to indicate this type of WLI.


### No Auth

In this file [.logs/pod-with-proxy-logs.txt](./logs/pod-with-proxy-logs.txt) or below in expand section. In this test we have only one rule which allows connection to wikipedia.org for anybody.
```
sessionMatcher: host() == 'wikipedia.org'
```

From above logs, allowed connection (to wikipedia.org):

```
* Uses proxy env variable HTTPS_PROXY == 'http://10.0.0.9:443'
*   Trying 10.0.0.9:443...
* Connected to 10.0.0.9 (10.0.0.9) port 443
* CONNECT tunnel: HTTP/1.1 negotiated
> Host: wikipedia.org:443
>
< HTTP/1.1 200 OK

< HTTP/2 301
< server: mw-web.codfw.main-6cf7d57b97-qwdss
< location: https://www.wikipedia.org/
< content-length: 234
...
{ [234 bytes data]
```

Snippets of logs showing connection denied by proxy (because there was no rule allowing the URL):

```
* Connection #0 to host 10.0.0.9 left intact
* Uses proxy env variable HTTPS_PROXY == 'http://10.0.0.9:443'
*   Trying 10.0.0.9:443...
* Connected to 10.0.0.9 (10.0.0.9) port 443
* CONNECT tunnel: HTTP/1.1 negotiated

> CONNECT api.ipify.org:443 HTTP/1.1
> Host: api.ipify.org:443
>
< HTTP/1.1 403 Forbidden
<
* The requested URL returned error: 403
* Closing connection
```

### Federated Workload Identity (WLI)

There is nothing to test in context of SWP, because there is no explicit GSA and there is no way to use principals in SWP CEL.

This can be used to explore the federated WLI feature of GKE. Deploy k8s mainfests and grant permissions to a test role:

```bash
% ./scripts/deploy.sh test_federated_wli
```

### WLI with KSA to GSA Mapping

Deploy k8s mainfests, create GSA and link the Service accounts

```bash
% ./scripts/deploy.sh test_wli
```

Create the pods and test that WLI has been setup correctly inside the pod:
```
% k apply -f pod-limited-sa-ksa2gsa.yaml
% k apply -f pod-priv-sa-ksa2gsa.yaml
```

Inside the pod check the WLI email and test that a bucket can be accessed (the perms were assigned in deploy script):
```
% k exec -it pod-priv-sa-ksa2gsa -- /bin/bash
root@pod-priv-sa-ksa2gsa:/#  curl -X GET -H "Authorization: Bearer $(gcloud auth print-access-token)" https://storage.googleapis.com/storage/v1/b/<BUCKET>/o
{
  "kind": "storage#objects"
}
root@pod-priv-sa-ksa2gsa:/# curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email
demo-app-priv-sa-ksa2gsa@PROJECT_ID_REDACTED.iam.gserviceaccount.comroot@pod-priv-sa-ksa2gsa:/#
```

The GKE WLI is not expected to work at this stage, but some testing still. I've run the curl test when the SWP had only one rule
```
host() == 'wikipedia.org' && source.matchServiceAccount('demo-app-priv-sa-ksa2gsa@PROJECT_ID_REDACTED.iam.gserviceaccount.com')
```
And it was indeed dined by proxy, even though the WLI test described above was working successfully.

Adding a non-auth rule at lower priority and retrying the curl request confirms that auth rule is tested but didn't match and gateway access logs confirm that no-auth rule was matched and connection allowed:

```
root@pod-priv-sa-ksa2gsa:/# curl -fsv --proxy $HTTP_PROXY http://wikipedia.org
* Uses proxy env variable NO_PROXY == 'localhost,127.0.0.1,metadata.google.internal,.googleapis.com,accounts.google.com'
*   Trying 10.0.0.9:443...
* Connected to 10.0.0.9 (10.0.0.9) port 443 (#0)
> GET http://wikipedia.org/ HTTP/1.1
> Host: wikipedia.org
>
< HTTP/1.1 301 Moved Permanently
< content-length: 0
< location: https://wikipedia.org/
< server: HAProxy
< date: Sun, 07 Apr 2024 03:59:09 GMT
```

Rules at the SWP at this test:

```
% gcloud network-security gateway-security-policies rules list  --gateway-security-policy swp-policy --location=$GCP_REGION
NAME
rule-300-no-auth
rule-200-with-auth
%
% gcloud network-security gateway-security-policies rules export rule-300-no-auth --gateway-security-policy swp-policy --location=$GCP_REGION | yq '.priority, .sessionMatcher'
300
host() == 'wikipedia.org'
% gcloud network-security gateway-security-policies rules export rule-200-with-auth --gateway-security-policy swp-policy --location=$GCP_REGION | yq '.priority, .sessionMatcher'
200
host() == 'wikipedia.org' && source.matchServiceAccount('demo-app-priv-sa-ksa2gsa@PROJECT_ID_REDACTED.iam.gserviceaccount.com')
```

Access logs `networkservices.googleapis.com/Gateway`:
```
action: "ALLOWED"
name: "projects/PROJECT_NUMBER_REDACTED>/locations/australia-southeast1/gatewaySecurityPolicies/swp-policy/rules/rule-300-no-auth"
```

Testing the same SA from VM (creating VM as in section above and giving it the same GSA as in the GKE test pod), the connection succeeded by the auth rule:
```
action: "ALLOWED"
name: "projects/PROJECT_NUMBER_REDACTED>/locations/australia-southeast1/gatewaySecurityPolicies/swp-policy/rules/rule-200-with-auth"
```

<details>
  <summary>Connection logs on VM</summary>

```
olga@test-vm-swp-with-sa:~$ curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email
demo-app-priv-sa-ksa2gsa@PROJECT_ID_REDACTED.iam.gserviceaccount.comolga@test-vm-swp-with-sa:~$
olga@test-vm-swp-with-sa:~$ curl -vfs --proxy http://10.0.0.9:443  wikipedia.org
*   Trying 10.0.0.9:443...
* Connected to 10.0.0.9 (10.0.0.9) port 443 (#0)
> GET http://wikipedia.org/ HTTP/1.1
> Host: wikipedia.org
> User-Agent: curl/7.74.0
> Accept: */*
> Proxy-Connection: Keep-Alive
>
* Mark bundle as not supporting multiuse
< HTTP/1.1 301 Moved Permanently
< content-length: 0
< location: https://wikipedia.org/
< server: HAProxy
< x-cache: cp5024 int
< x-cache-status: int-tls
< date: Sun, 07 Apr 2024 04:15:55 GMT
<
* Connection #0 to host 10.0.0.9 left intact
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

TODO - replace with Taskfile
Use "cleanup": [scripts/deploy.sh](./scripts/deploy.sh)

```bash
$ ./scripts/deploy.sh cleanup
```

Reference:

* [CEL](https://cloud.google.com/secure-web-proxy/docs/cel-matcher-language-reference#available-attributes-in-sessionmatcher-and-applicationmatcher)
* [Official doc for SWP installation](https://cloud.google.com/secure-web-proxy/docs/initial-setup-steps)

