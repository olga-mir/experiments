# q06-ember: DestinationRule Subsets + Load Balancer Policy

## Namespace
`q06-ember`

## Workloads
- **tester**: curlimages/curl (test pod)
- **my-app-v1**: kong/httpbin with label `version: v1`
- **my-app-v2**: kong/httpbin with label `version: v2`

## Task

1. Create a **DestinationRule** for `my-app` with:
   - Two subsets: `v1` (label `version: v1`) and `v2` (label `version: v2`)
   - LoadBalancer policy set to `ROUND_ROBIN`
2. Create a **VirtualService** that routes all traffic to subset `v1` only
3. Verify all requests reach only `v1`

## Verification

**Run requests and confirm all go to v1:**
```bash
for i in $(seq 1 5); do
  kubectl exec deploy/tester -n q06-ember -- curl -s my-app:8000/uuid | jq '.uuid'
done
```

Expected: All responses are from the same `my-app-v1` pod.

## Resources to Create
- Namespace: `q06-ember`
- Deployments: `tester`, `my-app-v1`, `my-app-v2` with httpbin image
- DestinationRule: my-app (subsets v1, v2 with ROUND_ROBIN LB)
- VirtualService: my-app (routes to v1 only)
