#!/bin/bash

NUM_NODES=$1
GROUP_SIZE=10

TEMPLATE_FILE="kwok-node-template.yaml"
OUTPUT_DIR="kwok-nodes"
mkdir -p $OUTPUT_DIR

if [ -z "$NUM_NODES" ]; then
  echo "Usage: $0 <number_of_nodes>"
  exit 1
fi

for ((i = 0; i < NUM_NODES; i++)); do
  GROUP_INDEX=$((i / GROUP_SIZE))
  OUTPUT_FILE="$OUTPUT_DIR/kwok-nodes-group-$GROUP_INDEX.yaml"

  if ((i % GROUP_SIZE == 0)); then
    echo "Creating new group file: $OUTPUT_FILE"
    echo "# Group $GROUP_INDEX of KWOK Nodes" > $OUTPUT_FILE
  fi

  sed "s/\$INDEX/$i/g" $TEMPLATE_FILE >> $OUTPUT_FILE
  echo "---" >> $OUTPUT_FILE

  echo "Added kwok-node-$i to $OUTPUT_FILE"
done

echo "Generated $NUM_NODES KWOK Nodes in groups of $GROUP_SIZE in $OUTPUT_DIR"

# cue doesn't work
# for i in $(seq 0 $((NUM_NODES - 1))); do
#   cue eval -t index=$i kwok-node.cue -o yaml > kwok-node-$i.yaml
#   kubectl apply -f kwok-node-$i.yaml
# done
