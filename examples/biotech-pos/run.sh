#!/usr/bin/env bash
# Run the biotech-pos worked demo end-to-end.
#
# Idempotent: regenerates synthetic CSVs from a fixed seed, then runs
# deep-quant run-signal into expected-output/. Safe to rerun.

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
