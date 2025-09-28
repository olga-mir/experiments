#!/bin/bash

set -eoux pipefail

USER_PROMPT="Share some mind-blowing statistic related to running an OSS LLM on a kubernetes cluster"

curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d @- <<EOF
{
    "prompt": "<start_of_turn>user\n${USER_PROMPT}<end_of_turn>\n",
    "temperature": 0.90,
    "top_p": 1.0,
    "max_tokens": 128
}
EOF
