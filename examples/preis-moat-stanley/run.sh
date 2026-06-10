#!/usr/bin/env bash
# Replicate the Preis-Moat-Stanley 2013 result and run a 13-year
# out-of-sample extension with the pipeline's multiple-testing machinery.

set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -f "$DIR/data/target.csv" ] || [ ! -f "$DIR/data/predictor_debt.csv" ]; then
  echo "Data not found. Running fetcher (network-bound; may take a few minutes)..."
  python3 "$DIR/data/fetch_data.py"
fi

deep-quant run-signal \
  --spec "$DIR/signal-spec.yaml" \
  --target-csv "$DIR/data/target.csv" \
  --predictor-csv "google-trends=$DIR/data/predictor_debt.csv" \
  --run-dir "$DIR/expected-output"

echo
echo "Done. See $DIR/expected-output/signal-card.md for the verdict."
