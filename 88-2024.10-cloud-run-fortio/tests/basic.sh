#!/bin/bash
set -eou pipefail

# From fortio container logs:
# "msg":"REST API on /fortio/rest/run, /fortio/rest/status, /fortio/rest/stop, /fortio/rest/dns"
# "msg":"Debug endpoint on /debug, Additional Echo on /debug/echo/, Flags on /fortio/flags, and Metrics on /debug/metrics"

export SERVICE_URL=$(gcloud run services describe fortio-test --region=$REGION --format='value(status.url)')
export TOKEN=$(gcloud auth print-identity-token)

OUTPUT_DIR="test-results"
mkdir -p $OUTPUT_DIR

#curl -s -H "Authorization: Bearer $TOKEN" $SERVICE_URL/fortio/env > $OUTPUT_DIR/out-env.html
#curl -s -H "Authorization: Bearer $TOKEN" $SERVICE_URL/fortio/debug > $OUTPUT_DIR/out-debug

curl -s -H "Authorization: Bearer $TOKEN" $SERVICE_URL/fortio/flags > $OUTPUT_DIR/out-flags.json

curl -s -H "Authorization: Bearer $TOKEN" $SERVICE_URL/fortio/rest/status > $OUTPUT_DIR/out-status.json
curl -s -H "Authorization: Bearer $TOKEN" $SERVICE_URL/fortio/rest/dns?host=google.com > $OUTPUT_DIR/out-dns.json

exit 0

curl -s -X POST -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
        "url": "'"$SERVICE_URL"'/fortio/echo",
        "qps": "10",
        "t": "5s",
        "c": "2",
        "labels": "test-from-bastion"
    }' \
    $SERVICE_URL/fortio/rest/run > $OUTPUT_DIR/out-run.json

sleep 6

# Get the results
curl -s -H "Authorization: Bearer $TOKEN" $SERVICE_URL/fortio/rest/status > $OUTPUT_DIR/out-status-after.json

curl -s -H "Authorization: Bearer $TOKEN" $SERVICE_URL/fortio/echo?size=1024 > $OUTPUT_DIR/out-echo-1k
curl -s -H "Authorization: Bearer $TOKEN" $SERVICE_URL/fortio/echo?delay=100ms > $OUTPUT_DIR/out-echo-delay

# Get Prometheus metrics
curl -s -H "Authorization: Bearer $TOKEN" $SERVICE_URL/fortio/debug/vars > $OUTPUT_DIR/out-metrics.json

# Parse and display some meaningful info from the results
echo "=== Test Results Summary ==="
echo "Load test results:"
jq '.DurationHistogram.Count, .DurationHistogram.Avg' $OUTPUT_DIR/out-run.json

echo "Server metrics:"
jq '.cmdline, .memstats.Alloc' $OUTPUT_DIR/out-metrics.json

# - Change QPS: "qps": "100"
# - Longer duration: "t": "30s"
# - More concurrent connections: "c": "20"
# - Add payload: "payload": "somedata"
# - Add custom headers: "headers": {"X-My-Header": "value"}
