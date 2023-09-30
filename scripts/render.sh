#!/bin/bash

REPO_ROOT=$(git rev-parse --show-toplevel)
TEMPLATE_SUFFIX="tmpl"
RENDER_SUFFIX="rendered" # exclude from committing in .gitignore

for f in $(find $REPO_ROOT -name "*tmpl.yaml"); do
  rendered_filename="${f/$TEMPLATE_SUFFIX.yaml/$RENDER_SUFFIX.yaml}"
  envsubst < $f > $rendered_filename
  echo $rendered_filename
done
