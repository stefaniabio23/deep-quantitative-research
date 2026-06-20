#!/usr/bin/env bash
# Reconstruct real-time US macro data from ALFRED vintages and test whether
# first revisions carry directional momentum (stage 1). Network-bound: needs
# a free FRED_API_KEY in the environment or repo-root .env.

set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

need_fetch=false
for sid in PAYEMS RSAFS INDPRO; do
  [ -f "$DIR/data/${sid}_vintages.csv" ] || need_fetch=true
done

if [ "$need_fetch" = true ]; then
  echo "Vintage data not found. Fetching from ALFRED (needs FRED_API_KEY)..."
  python3 "$DIR/data/fetch_alfred.py"
fi

python3 "$DIR/run_revision_momentum.py" --out "$DIR/expected-output"

echo
echo "Done. See $DIR/expected-output/stage1-summary.md for the verdict."
