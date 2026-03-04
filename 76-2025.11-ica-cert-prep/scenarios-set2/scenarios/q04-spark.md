# q04-spark: VirtualService Rule Ordering (Specific Before Catch-All)

## Namespace
`q04-spark`

## Workloads
- **caller**: curlimages/curl (test pod)
- **web-v1**: kong/httpbin with label `version: v1`
- **web-v2**: kong/httpbin with label `version: v2`

## Task

1. A pre-applied VirtualService has incorrect rule ordering (catch-all rule before specific rule)
2. The catch-all sends traffic to `v1`, but the specific rule (header `x-canary: true`) should send to `v2`
3. Fix the VirtualService by reordering rules so the specific match is evaluated first

## Verification

**Request with canary header should go to v2:**
```bash
kubectl exec deploy/caller -n q04-spark -- curl -s -H "x-canary: true" web:8000/get | jq '.headers["X-Canary"]'
```

**Confirm the response comes from v2 (check server response or headers):**
```bash
kubectl exec deploy/caller -n q04-spark -- curl -s -H "x-canary: true" web:8000/uuid | jq .
```

Expected: Canary header requests route to v2. Default requests route to v1.

## Resources to Create
- Namespace: `q04-spark`
- Deployments: `caller`, `web-v1`, `web-v2` with httpbin image
- DestinationRule: web (subsets v1, v2)
- VirtualService: web (with BROKEN rule order - fix it)
