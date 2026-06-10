#!/usr/bin/env bash
# Run the null-control demo. The data has no real lead-lag relationship; the
# pipeline should produce a documented null with confidence capped at low.

set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

python3 "$DIR/data/generate.py"

deep-quant run-signal \
  --spec "$DIR/signal-spec.yaml" \
  --target-csv "$DIR/data/target.csv" \
  --predictor-csv "aact=$DIR/data/predictor.csv" \
  --run-dir "$DIR/expected-output"

echo
echo "Done. See $DIR/expected-output/signal-card.md for the rendered result."
echo "Expected verdict: confidence cap = low, no signal recovered."
