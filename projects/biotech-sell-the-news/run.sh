#!/usr/bin/env bash
# Sell-the-news event study. Fetches prices (yfinance) and news (GDELT) for the
# tickers in data/events_seed.csv, then runs the cross-sectional analysis.
# Network-bound; no API key required (both sources are free). Populate
# data/events_seed.csv with real catalysts before the result means anything.

set -euo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ ! -d "$DIR/data/prices" ]; then
  echo "Fetching prices (yfinance)..."
  python3 "$DIR/data/fetch_prices.py"
fi
if [ ! -d "$DIR/data/news" ]; then
  echo "Fetching news (GDELT)..."
  python3 "$DIR/data/fetch_gdelt.py"
fi

python3 "$DIR/run_sell_the_news.py" --out "$DIR/expected-output"
echo
echo "Done. See $DIR/expected-output/sell-the-news-summary.md"
