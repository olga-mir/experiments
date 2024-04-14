# Purpose

Currently SWP `SessionMatcher` is not supported with GKE WLI: [Post](https://www.googlecloudcommunity.com/gc/General-Misc-Q-A/How-do-Secure-Web-Proxy-rules-filter-requests-sent-by-containers/m-p/615769#M1189)

Having proved before that the same GSA (as pod's WLI SA) is working with SWP indicates that there is a difference between VM and GKE WLI auth mechanisms and I wanted to dig deeper into these differences. There is a hint in the post linked above:

> For GKE service account are managed slightly different.  For VMs service-account information is derided from the Andromeda unique identifier (AEID), for GKE the container/app needs to query the metadata service to receive a token (JWT) which is provided in the HTTP header.

Getting hands dirty to understand this a bit better and see it in action.

TL;DR - tokens from Pod and VM with the same GSA have different structure and content, but they have the same client ID. The above quote implies VM doesn't send JWT token in HTTP header, while pod sends JWT in a header. My setup is incomplete but I haven't seen that (yet).

## Exploring HTTP Requests From The Receiving End

There is magic applied to a packet along its way to leaving node/VM's network interface. In order to get a better picture of the final packet I deployed lightweight proxy `mitmproxy`. It is quick and easy to setup without TLS, but it is necessary for full-fledged demo interacting with goolgeapis.

In its current state it looks like a curl request with explicit Authorization header and without it - http requests look identical in terms of headers whether it comes from the pod or a VM. Note that when using GKE WLI or VM with associated GCP SA, it is this header is not required.

Below logs from `mitmproxy` show dumps of 2 requests - from a VM and from a GKE pod, both tied to the same GSA, as will be shown in the section below. Note the Authorization header, it is been trancated to remove token payload, but it shows they are different (don't mind the 401 this part isn't done yet, but we do see the incoming request which is all I care about at this step)

<details>
  <summary>Logs from mitmproxy</summary>

```bash

user@mitmproxy:~$ ./mitmdump -s headers-masked.py
[05:37:07.080] Loading script headers-masked.py
[05:37:07.082] HTTP(S) proxy listening at *:8080.
[05:37:22.610][10.180.2.6:50040] client connect
[05:37:22.618][10.180.2.6:50040] server connect storage.googleapis.com:443 (172.217.24.59:443)
New request:
Method: GET
URL: https://storage.googleapis.com/storage/v1/b/BUCKET/o
Headers:
user-agent: curl/7.88.1
accept: */*
authorization: Bearer ya29....96k1U
10.180.2.6:50040: GET https://storage.googleapis.com/storage/v1/b/BUCKET/o HTTP/2.0
      << HTTP/2.0 401 Unauthorized 285b
[05:37:22.669][10.180.2.6:50040] client disconnect
[05:37:22.670][10.180.2.6:50040] server disconnect storage.googleapis.com:443 (172.217.24.59:443)
[05:37:27.089][10.0.0.47:40032] client connect
[05:37:27.094][10.0.0.47:40032] server connect storage.googleapis.com:443 (172.217.24.59:443)
New request:
Method: GET
URL: https://storage.googleapis.com/storage/v1/b/BUCKET/o
Headers:
user-agent: curl/7.74.0
accept: */*
authorization: Bearer ya29....Y9f90
10.0.0.47:40032: GET https://storage.googleapis.com/storage/v1/b/BUCKET/o HTTP/2.0
     << HTTP/2.0 401 Unauthorized 285b

```

</details>

## Exploring Tokens

Tokens have a bit different structure and look a bit different but they are linked to the same Client ID. In bellow snippets `azp` and `aud` have been redacted but they are exactly the same.

From within a pod with `demo-app-admin-sa-ksa2gsa` associated with it:

```
root@pod-priv-sa-ksa2gsa:/# TOKEN=$(gcloud auth print-access-token)
root@pod-priv-sa-ksa2gsa:/# curl "https://www.googleapis.com/oauth2/v3/tokeninfo?access_token=$TOKEN"
{
  "azp": "<REDACTED>",
  "aud": "<REDACTED>",
  "scope": "https://www.googleapis.com/auth/userinfo.email https://www.googleapis.com/auth/cloud-platform",
  "exp": "1713074322",
  "expires_in": "3558",
  "email": "demo-app-admin-sa-ksa2gsa@PROJECT_ID_REDACTED.iam.gserviceaccount.com",
  "email_verified": "true",
  "access_type": "online"
}
```

On a VM associated with exactly the same GSA as the pod above `demo-app-admin-sa-ksa2gsa`, token structure is a bit different.
This test shows that the the GSA is configured correctly to give access to the bucket (it is not important at this step though). This test will also work with gcloud as well as curl without the Authorization header.

```
user@demo-app-admin-sa-ksa2gsa-with-sa:~$ curl -X GET -H "Authorization: Bearer $(gcloud auth print-access-token)" https://storage.googleapis.com/storage/v1/b/$BUCKET/o
{
  "kind": "storage#objects"
}
user@demo-app-admin-sa-ksa2gsa-with-sa:~$ TOKEN=$(gcloud auth print-access-token)
user@demo-app-admin-sa-ksa2gsa-with-sa:~$ curl "https://www.googleapis.com/oauth2/v3/tokeninfo?access_token=$TOKEN"
{
  "azp": "<REDACTED>",
  "aud": "<REDACTED>",
  "scope": "https://www.googleapis.com/auth/cloud-platform",
  "exp": "1713073535",
  "expires_in": "3363",
  "access_type": "online"
}
```


