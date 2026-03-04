# q05-drift: Traffic Shifting Weighted Canary

## Namespace
`q05-drift`

## Workloads
- **client**: curlimages/curl (test pod)
- **store-v1**: kong/httpbin with label `version: v1`
- **store-v2**: kong/httpbin with label `version: v2`

## Task

1. Create a **DestinationRule** for `store` with subsets `v1` and `v2`
2. Create a **VirtualService** that distributes traffic:
   - 80% to `store-v1`
   - 20% to `store-v2`
3. Verify the weighted distribution by running multiple requests

## Verification

**Run 10 requests and count distribution:**
```bash
for i in $(seq 1 10); do
  kubectl exec deploy/client -n q05-drift -- curl -s store:8000/headers | jq -r '.host'
done | sort | uniq -c
```

Expected: Roughly 8 requests to v1 and 2 requests to v2.

## Resources to Create
- Namespace: `q05-drift`
- Deployments: `client`, `store-v1`, `store-v2` with httpbin image
- DestinationRule: store (subsets v1, v2)
- VirtualService: store (weighted routing 80/20)
