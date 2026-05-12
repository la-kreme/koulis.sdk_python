#!/usr/bin/env bash
set -euo pipefail

OPENAPI_URL="${KOULIS_OPENAPI_URL:-https://api.koulis.ai/openapi.json}"
OUTPUT="src/koulis/models/_generated.py"

echo "Regenerating Pydantic models from $OPENAPI_URL"

uv run datamodel-codegen \
  --url "$OPENAPI_URL" \
  --output "$OUTPUT" \
  --target-python-version 3.12 \
  --output-model-type pydantic_v2.BaseModel \
  --use-annotated \
  --use-double-quotes \
  --use-field-description \
  --disable-timestamp \
  --use-standard-collections \
  --field-constraints

echo "Models regenerated at $OUTPUT"