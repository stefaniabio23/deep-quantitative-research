# Data Sources

## Finance

| Source | What | Access | Notes |
|--------|------|--------|-------|
| yfinance | Price, volume, splits, dividends | `fetch_data.py --source yfinance` | Free; adjusted prices; survivorship bias: only active tickers |
| FRED | 800k+ macro series (CPI, rates, GDP, employment) | `fetch_data.py --source fred` | Free API key required (fred.stlouisfed.org) |
| Fama-French | Factor returns (MKT, SMB, HML, RMW, CMA, MOM) | `fetch_data.py --source famafrench` | Free CSV from mba.tuck.dartmouth.edu |
| SEC EDGAR | 10-K, 10-Q, 8-K filings | WebFetch sec.gov/cgi-bin/browse-edgar | Free; structured XML available |
| Ken French data library | Industry portfolios, sorted portfolios | WebFetch | Free CSV downloads |

## Biotech / Clinical

| Source | What | Access | Notes |
|--------|------|--------|-------|
| ClinicalTrials.gov | Trial registry: phase, status, endpoints, enrollment | `fetch_data.py --source clinicaltrials` | Free; better US coverage than international; Phase 3 > Phase 1/2 |
| PubMed / NCBI | Abstracts, metadata, MeSH terms | `fetch_data.py --source pubmed` | Free; full text requires institutional access |
| openFDA | Drug approvals, adverse events, label text | `fetch_data.py --source openfda` | Free; US only |
| OpenTargets | Gene-disease associations, target tractability | `fetch_data.py --source opentargets` | Free GraphQL API |
| Europe PMC | Open-access literature (strong European coverage) | `fetch_data.py --source europepmc` | Free REST API |
| STRING-DB | Protein interaction networks | WebFetch string-db.org | Free; good for network centrality |

## Known limitations by domain

### Finance
- **yfinance survivorship bias:** Only returns data for tickers that currently exist. Delisted stocks are absent. Flag and document; do not silently ignore.
- **FRED timing:** Some series are revised retroactively. Use vintage data if available for backtests.
- **Earnings transcripts:** Not directly available via free APIs. Use WebSearch + WebFetch from investor relations pages or financial data sites.

### Biotech
- **Publication bias:** PubMed overrepresents positive results. Note in caveats for any literature-based analysis.
- **ClinicalTrials Phase 1/2 coverage:** Weaker than Phase 3. International (non-US) coverage varies significantly.
- **openFDA US-only:** For EU approvals, use EMA's EPAR database (WebFetch ema.europa.eu).
