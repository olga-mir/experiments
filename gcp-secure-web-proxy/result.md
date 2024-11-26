# From pod

```terminal
root@pod-priv-sa-ksa2gsa:/# curl -X GET -H "Authorization: Bearer $(gcloud auth print-access-token)" https://storage.googleapis.com/storage/v1/b/swp-test-bucket/o
{
  "kind": "storage#objects"
}

root@pod-priv-sa-ksa2gsa:/# curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email
demo-app-admin-sa-ksa2gsa@PROJECT_ID_REDACTED.iam.gserviceaccount.comroot@pod-priv-sa-ksa2gsa:/#

root@pod-priv-sa-ksa2gsa:/# curl -vfs -H "Authorization: Bearer $(gcloud auth print-access-token)"  https://httpbin.org/get
* Uses proxy env variable NO_PROXY == 'localhost,127.0.0.1,metadata.google.internal,.googleapis.com,accounts.google.com'
* Uses proxy env variable HTTPS_PROXY == 'http://10.0.0.9:443'
*   Trying 10.0.0.9:443...
* Connected to 10.0.0.9 (10.0.0.9) port 443 (#0)
* allocate connect buffer
* Establish HTTP proxy tunnel to httpbin.org:443
> CONNECT httpbin.org:443 HTTP/1.1
> Host: httpbin.org:443
> User-Agent: curl/7.88.1
> Proxy-Connection: Keep-Alive
>
< HTTP/1.1 403 Forbidden
< date: Tue, 09 Apr 2024 10:37:29 GMT
< connection: close
<
* The requested URL returned error: 403
* Closing connection 0
```


# From VM
Using the same SA from a VM - allowed by auth rule:

```terminal
olga@demo-app-admin-sa-ksa2gsa-with-sa:~$ curl -s -H "Metadata-Flavor: Google" http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/email
demo-app-admin-sa-ksa2gsa@model-myth-375500.iam.gserviceaccount.comolga@demo-app-admin-sa-ksa2gsa-with-sa:~$

olga@demo-app-admin-sa-ksa2gsa-with-sa:~$ HTTP_PROXY=10.0.0.9:443 && curl -vfs http://httpbin.org/get
*   Trying 18.214.231.104:80...
* Connected to httpbin.org (18.214.231.104) port 80 (#0)
> GET /get HTTP/1.1
> Host: httpbin.org
> User-Agent: curl/7.74.0
> Accept: */*
>
* Mark bundle as not supporting multiuse
< HTTP/1.1 200 OK
< Date: Tue, 09 Apr 2024 10:46:31 GMT
< Content-Type: application/json
< Content-Length: 254
< Connection: keep-alive
< Server: gunicorn/19.9.0
< Access-Control-Allow-Origin: *
< Access-Control-Allow-Credentials: true
<
{
  "args": {},
  "headers": {
    "Accept": "*/*",
    "Host": "httpbin.org",
    "User-Agent": "curl/7.74.0",
    "X-Amzn-Trace-Id": "Root=1-66151c86-48299c7c3dfe2eb360686d61"
  },
  "origin": "35.197.187.32",
  "url": "http://httpbin.org/get"
}
* Connection #0 to host httpbin.org left intact
```
