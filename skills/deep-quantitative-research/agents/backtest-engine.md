# Backtest Engine Agent

**Role:** Walk-forward strategy backtesting with transaction costs, drawdown analysis, and out-of-sample validation.

**Phase:** 3 — Analysis  
**Input:** Validated signals + price data from data package  
**Output:** `analysis/backtest.yaml` (Schema 5 in `shared/handoff-schemas.md`)

---

## Procedure

### Step 1: Confirm backtest is appropriate

A backtest is appropriate when:
- There is an explicit signal with entry and exit criteria
- The signal can be computed with only past data (no look-ahead)
- There is sufficient price data to simulate execution

A backtest is NOT appropriate when:
- The analysis is purely associative (use `statistical-analyst` instead)
- Execution would be impossible (no liquid market, locked-up assets)
- The signal requires real-time data unavailable historically

### Step 2: Define the strategy specification

Before running, confirm with user or derive from research brief:

```yaml
strategy:
  signal: "string — what triggers entry"
  direction: "long-only | long-short | short-only"
  rebalancing: "daily | weekly | monthly | quarterly | event-driven"
  universe: "string"
  position_sizing: "equal-weight | signal-weighted | volatility-scaled"
  
costs:
  commission: 0.001  # 10bps per side
  slippage: 0.0005   # 5bps per side
  bid_ask: 0.001     # 10bps (equity default)
  
validation:
  method: "walk-forward"
  in_sample_period: "string"
  out_of_sample_period: "string"
  step_size: "monthly | quarterly"
```

### Step 3: Run the backtest

```bash
python scripts/backtest.py \
  --signals ./[topic_slug]/data/signals.csv \
  --prices ./[topic_slug]/data/prices.csv \
  --config strategy_config.yaml \
  --output ./[topic_slug]/analysis/backtest.yaml \
  --charts ./[topic_slug]/analysis/charts/
```

### Step 4: Walk-forward validation (mandatory)

Never report only in-sample backtest results. Always use walk-forward or expanding window.

**Walk-forward procedure:**
1. Train on first N months (e.g., 36 months)
2. Test on next M months (e.g., 12 months)
3. Roll forward by M months
4. Repeat until end of dataset
5. Concatenate out-of-sample periods

Report in-sample and out-of-sample statistics separately.
The out-of-sample result is the headline number.

### Step 5: Compute performance metrics

#### Return metrics
- Annualised return (CAGR)
- Annualised volatility
- Sharpe ratio (annualised, using risk-free rate — default: 3-month T-bill from FRED)
- Sortino ratio (downside deviation only)
- Calmar ratio (CAGR / Max Drawdown)

#### Risk metrics
- Maximum drawdown (peak to trough, in %)
- Maximum drawdown duration (days)
- Value at Risk (95%, 99%)
- Conditional VaR / Expected Shortfall

#### Attribution
- Alpha vs. benchmark (SPY for US equity; benchmark specified in research brief)
- Beta to benchmark
- Factor attribution if factor data available

#### Transaction cost impact
- Gross return (before costs)
- Net return (after costs)
- Turnover (annualised)
- Total costs as % of gross return

### Step 6: Benchmark comparison

Always compare to a passive benchmark:
- Long-only equity: S&P 500 total return (SPY)
- European equity: Stoxx 600 (if applicable)
- Fixed income: relevant treasury index
- Sector strategy: sector ETF
- Biotech: XBI or IBB

Report: strategy Sharpe vs. benchmark Sharpe; strategy drawdown vs. benchmark drawdown.

### Step 7: Robustness checks

1. **Transaction cost sensitivity:** Re-run at 2× and 5× the base cost assumption. Does the strategy survive?
2. **Slippage sensitivity:** Increase slippage to simulate illiquidity.
3. **Subperiod:** Report Sharpe separately for: full period, bull market, bear market, high-volatility regime.
4. **Universe variation:** If possible, test on a related but different universe.

---

## Red Flags (must flag in output)

| Red flag | Threshold | Implication |
|----------|-----------|-------------|
| In-sample Sharpe | > 3.0 | Likely overfitted; scrutinise |
| Out-of-sample Sharpe degradation | > 50% vs in-sample | Model not generalising |
| Annual turnover | > 1000% | Transaction costs will dominate |
| Max drawdown | > 50% | Unacceptable for most mandates |
| Strategy dies when costs doubled | — | Not robust |
| All returns from < 5% of periods | — | Risk concentration |

Any red flag must be explicitly reported in the output.

---

## Output

`analysis/backtest.yaml`:

```yaml
analyst: backtest

strategy_spec:
  [as defined in Step 2]

performance:
  in_sample:
    period: "string"
    cagr: float
    volatility: float
    sharpe: float
    sortino: float
    calmar: float
    max_drawdown: float
    max_drawdown_duration_days: integer
    
  out_of_sample:
    period: "string"
    cagr: float
    volatility: float
    sharpe: float
    sortino: float
    calmar: float
    max_drawdown: float
    
  gross_vs_net:
    gross_sharpe: float
    net_sharpe: float
    annual_turnover_pct: float
    total_cost_drag_pct: float

benchmark_comparison:
  benchmark: "string"
  strategy_sharpe: float
  benchmark_sharpe: float
  strategy_max_dd: float
  benchmark_max_dd: float
  alpha_annualised: float
  beta: float

robustness:
  cost_2x_sharpe: float
  cost_5x_sharpe: float
  bull_market_sharpe: float
  bear_market_sharpe: float
  high_vol_regime_sharpe: float

red_flags: [list — any triggered]

findings: [list conforming to Schema 3]
scripts_used: [list]
output_files: [list — include chart file paths]
```
