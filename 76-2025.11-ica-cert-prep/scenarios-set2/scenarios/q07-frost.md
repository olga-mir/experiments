# q07-frost: Traffic Mirroring

## Namespace
`q07-frost`

## Workloads
- **client**: curlimages/curl (test pod)
- **backend-v1**: kong/httpbin with label `version: v1`
- **backend-v2**: kong/httpbin with label `version: v2`

## Task

1. Create a **DestinationRule** for `backend` with subsets `v1` and `v2`
2. Create a **VirtualService** that:
   - Routes all production traffic to `backend-v1`
   - Mirrors traffic to `backend-v2` (shadow traffic)
3. Verify that requests hit v1 and are also mirrored to v2

## Verification

**Send a request from client to backend:**
```bash
kubectl exec deploy/client -n q07-frost -- curl -s backend:8000/get | jq '.url'
```

**Check backend-v2 logs for the mirrored request:**
```bash
kubectl logs -n q07-frost deploy/backend-v2 --tail=20 | grep GET
```

Expected: Client gets response from v1, but v2 logs show the mirrored request.

## Resources to Create
- Namespace: `q07-frost`
- Deployments: `client`, `backend-v1`, `backend-v2` with httpbin image
- DestinationRule: backend (subsets v1, v2)
- VirtualService: backend (routes to v1 with mirror to v2)
