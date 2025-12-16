# Introduction

Experimenting with Cloudflare.

For now this README is just a scratchpad

# Learning

`cloudflared` is strictly for the Infrastructure (Tunnel/Connector). `wrangler` is the CLI for the Application (Workers, KV, R2).

```
$ wrangler login

$ wrangler kv namespace create ROUTING_TABLE
```

 ```json
 {
  "kv_namespaces": [
    {
      "binding": "ROUTING_TABLE",
      "id": "<id>"
    }
  ]
}
```

# Misc

Verify token

```
curl "https://api.cloudflare.com/client/v4/accounts/<account>/tokens/verify" -H "Authorization: Bearer <bearer-token>"
```

Run load using `fortio`

```
$ fortio load -c 32 -qps 1000 -t 5m -jitter -labels "Ambient_Mesh_Baseline" http://api.head-in-the-cloudz.com/productpage
 ```
