# Test SWP SessionMatcher with Service Account

Deploy 2 test VMs - one with a Service Account and one without: [./scripts/deploy-test-vms.sh](./scripts/deploy-test-vms.sh)

Deploy SWP using [./scripts/deploy.sh](./scripts/deploy.sh)

## View SWP Rule

SWP IP address and rule config:

```
% gcloud network-services gateways describe test-swp --location=$GCP_REGION | yq .addresses,.gatewaySecurityPolicy
- 10.0.0.9
projects/PROJECT_ID_REDACTED/locations/australia-southeast1/gatewaySecurityPolicies/with-sa-policy
%
% gcloud network-security gateway-security-policies rules export allow-wikipedia-org --gateway-security-policy with-sa-policy  --location=$GCP_REGION
basicProfile: ALLOW
description: Allow wikipedia for specific service account
enabled: true
name: projects/PROJECT_ID_REDACTED/locations/australia-southeast1/gatewaySecurityPolicies/with-sa-policy/rules/allow-wikipedia-org
priority: 1
sessionMatcher: host() == 'wikipedia.org' && source.matchServiceAccount('test-vm-swp@PROJECT_ID_REDACTED.iam.gserviceaccount.com')
```

## Test on a VM With SA Allowed in SWP

```
% gcloud compute ssh test-vm-swp-with-sa --zone australia-southeast1-a
Linux test-vm-swp-with-sa 5.10.0-28-cloud-amd64 #1 SMP Debian 5.10.209-2 (2024-01-31) x86_64
.... < warning omitted >
olga@test-vm-swp-with-sa:~$ export HTTPS_PROXY=http://10.0.0.9:443
olga@test-vm-swp-with-sa:~$ export HTTP_PROXY=http://10.0.0.9:443
olga@test-vm-swp-with-sa:~$ curl -H "Metadata-Flavor: Google" "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email"
test-vm-swp@<PROJECT_ID_REDACTED>.iam.gserviceaccount.comolga@test-vm-swp-with-sa:~$
olga@test-vm-swp-with-sa:~$ curl -fvs -o /dev/null https://wikipedia.org
* Uses proxy env variable HTTPS_PROXY == 'http://10.0.0.9:443'
*   Trying 10.0.0.9:443...
* Connected to 10.0.0.9 (10.0.0.9) port 443 (#0)
* allocate connect buffer!
* Establish HTTP proxy tunnel to wikipedia.org:443
> CONNECT wikipedia.org:443 HTTP/1.1
> Host: wikipedia.org:443
> User-Agent: curl/7.74.0
> Proxy-Connection: Keep-Alive
>
< HTTP/1.1 200 OK
< date: Thu, 04 Apr 2024 10:14:30 GMT
<
* Proxy replied 200 to CONNECT request
* CONNECT phase completed!

..... < omitted handshake >

< HTTP/2 301

..... < omitted headers >

{ [234 bytes data]
* Connection #0 to host 10.0.0.9 left intact
olga@test-vm-swp-with-sa:~$
```

## Test on a VM Without SA

```
% gcloud compute ssh test-vm-swp-no-sa --zone australia-southeast1-a
Linux test-vm-swp-no-sa 5.10.0-28-cloud-amd64 #1 SMP Debian 5.10.209-2 (2024-01-31) x86_64
.... < warning omitted >
olga@test-vm-swp-no-sa:~$
olga@test-vm-swp-no-sa:~$ curl -H "Metadata-Flavor: Google" "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email"
<PROJECT_NUMBER_REDACTED>-compute@developer.gserviceaccount.comolga@test-vm-swp-no-sa:~$
olga@test-vm-swp-no-sa:~$ export HTTPS_PROXY=http://10.0.0.9:443
olga@test-vm-swp-no-sa:~$ export HTTP_PROXY=http://10.0.0.9:443
olga@test-vm-swp-no-sa:~$
olga@test-vm-swp-no-sa:~$ curl -fvs -o /dev/null https://wikipedia.org
* Uses proxy env variable HTTPS_PROXY == 'http://10.0.0.9:443'
*   Trying 10.0.0.9:443...
* Connected to 10.0.0.9 (10.0.0.9) port 443 (#0)
* allocate connect buffer!
* Establish HTTP proxy tunnel to wikipedia.org:443
> CONNECT wikipedia.org:443 HTTP/1.1
> Host: wikipedia.org:443
> User-Agent: curl/7.74.0
> Proxy-Connection: Keep-Alive
>
< HTTP/1.1 403 Forbidden
< content-length: 13
< content-type: text/plain
< date: Thu, 04 Apr 2024 10:20:14 GMT
< connection: close
<
* The requested URL returned error: 403
* CONNECT phase completed!
* Closing connection 0
```
