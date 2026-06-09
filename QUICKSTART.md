# Quick Start

Get a signal from idea to dashboard in five steps.

## Install

```bash
git clone https://github.com/stephbeccag/deep-quantitative-research.git
cd deep-quantitative-research
pip install -e ".[dev]"
cp .env.example .env             # add FRED_API_KEY etc.
```

The sibling registry must be at `../datasources/`. Override via `DATASOURCES_PATH` in `.env`.

Healthcheck:

```bash
deep-quant query-datasources --healthcheck
```

## The five-step worked example

We want to know whether Google Trends search interest predicts UK retail sales.

### 1. Formulate the hypothesis

```bash
deep-quant formulate-hypothesis \
  --idea "Search interest predicts UK retail sales" \
  --out experiments/ideas/uk-retail-demand.yaml
```

This produces a YAML with the testable claim, target variable, candidate predictors, expected direction, expected lag, economic mechanism, and falsification criteria.

### 2. Find candidate datasets

```bash
deep-quant find-datasets \
  --hypothesis experiments/ideas/uk-retail-demand.yaml \
  --out experiments/specs/dataset-candidates.yaml
```

Queries the registry for target, predictor, and context datasets. Scores each on hypothesis fit, cadence, point-in-time safety, and access.

### 3. Design the signal

```bash
deep-quant design-signal \
  --target ons-retail-sales-index \
  --predictors google-trends-retail-searches,boe-consumer-credit \
  --out experiments/specs/uk-retail-search-demand-signal.yaml
```

Writes a `SignalSpec`: target field, predictor fields, join keys, cadence policy, feature-grid config, validation plan, expected outputs.

### 4. Run the signal

```bash
deep-quant run-signal \
  --spec experiments/specs/uk-retail-search-demand-signal.yaml
```

Materialises dataset contracts, rolls cadence safely, builds the controlled feature grid, runs the KPI backtest, applies the statistical-validation gate. All artefacts land in `experiments/runs/<run-id>/`.

### 5. Render the dashboard

```bash
deep-quant render-dashboard \
  --run experiments/runs/2026-06-09-uk-retail-search-demand/
```

Opens `dashboard.html` showing the signal-vs-target chart, rolling correlation, feature stability, confidence cap, data quality warnings, and next iteration.

## Run via Claude skill

The same pipeline end-to-end:

```text
/deep-quantitative-research "Does Google Trends interest in GLP-1 drugs predict next-quarter Novo obesity revenue?"
```

Claude walks each stage, asks for confirmation at the hypothesis and dataset gates, and writes the same artefact bundle.

## Troubleshooting

**Registry not found.** Confirm `../datasources/` exists and `DATASOURCES_PATH` matches. `deep-quant query-datasources --healthcheck` will print the resolved path and commit hash.

**FRED data missing.** Set `FRED_API_KEY` in `.env`. Free key at https://fred.stlouisfed.org/docs/api/api_key.html.

**yfinance ticker error.** Some tickers need the exchange suffix (`AZN.L` for AstraZeneca on LSE).

**ClinicalTrials.gov slow.** Public API; retry after a minute or rely on the cache.

**Confidence stuck at low.** Read `validation-report.md` in the run directory. It names exactly which check capped the confidence and what would lift it.
