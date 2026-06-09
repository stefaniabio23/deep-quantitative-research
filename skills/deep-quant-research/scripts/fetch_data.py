"""
Data fetcher for deep-quant-research.

CLI shape:
    python fetch_data.py <source> [source-specific args] --output PATH [--cache-dir DIR] [--no-cache]

Sources: yfinance, fred, famafrench, clinicaltrials, pubmed, opentargets, openfda

Caching: every fetch is fingerprinted by source + sorted args. A hit copies the
cached file to --output without hitting the network. Default cache dir is
.cache/fetch_data under the working directory. --no-cache forces a fresh fetch.

Retry: HTTP fetches retry up to 3 times with exponential backoff (1s, 2s, 4s)
on connection errors, 5xx, and 429.
"""

import argparse
import hashlib
import json
import os
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import pandas as pd
    import numpy as np
    import requests
except ImportError as e:
    print(f"Missing required package: {e}. Run: pip install -r requirements.txt")
    sys.exit(1)


DEFAULT_CACHE_DIR = ".cache/fetch_data"
RETRY_ATTEMPTS = 3
RETRY_BASE_DELAY = 1.0
RETRYABLE_STATUSES = {429, 500, 502, 503, 504}


def _fail(msg: str, code: int = 2) -> None:
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def _validate_date(value: str, name: str) -> str:
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        _fail(f"{name} must be YYYY-MM-DD, got: {value!r}")
    return value


def _validate_date_order(start: str, end: str) -> None:
    if datetime.strptime(start, "%Y-%m-%d") >= datetime.strptime(end, "%Y-%m-%d"):
        _fail(f"--start ({start}) must be before --end ({end})")


def _csv_list(value: str, name: str) -> list[str]:
    items = [v.strip() for v in value.split(",") if v.strip()]
    if not items:
        _fail(f"{name} must be a non-empty comma-separated list")
    return items


def _fingerprint(source: str, payload: dict) -> str:
    blob = json.dumps({"source": source, "payload": payload}, sort_keys=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _cache_paths(cache_dir: str, fp: str, ext: str) -> tuple[Path, Path]:
    base = Path(cache_dir) / fp
    return base.with_suffix(f".{ext}"), base.with_suffix(".meta.json")


def _try_cache_hit(cache_dir: str, fp: str, ext: str, output: str) -> bool:
    data_path, _ = _cache_paths(cache_dir, fp, ext)
    if not data_path.exists():
        return False
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(data_path, output)
    print(f"Cache hit ({fp}). Copied {data_path} -> {output}")
    return True


def _cache_store(cache_dir: str, fp: str, ext: str, output: str, meta: dict) -> None:
    data_path, meta_path = _cache_paths(cache_dir, fp, ext)
    data_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(output, data_path)
    meta_path.write_text(json.dumps({**meta, "fingerprint": fp, "stored_at": datetime.utcnow().isoformat() + "Z"}, indent=2))


def _http_get(url: str, params: dict | None = None, timeout: int = 30) -> requests.Response:
    return _retry_request("GET", url, params=params, timeout=timeout)


def _http_post(url: str, json_body: dict, timeout: int = 30) -> requests.Response:
    return _retry_request("POST", url, json=json_body, timeout=timeout)


def _retry_request(method: str, url: str, **kwargs) -> requests.Response:
    last_err: Exception | None = None
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            resp = requests.request(method, url, **kwargs)
        except (requests.ConnectionError, requests.Timeout) as e:
            last_err = e
            if attempt == RETRY_ATTEMPTS:
                break
            delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
            print(f"  retry {attempt}/{RETRY_ATTEMPTS - 1} after {delay:.0f}s (connection: {e})")
            time.sleep(delay)
            continue

        if resp.status_code in RETRYABLE_STATUSES and attempt < RETRY_ATTEMPTS:
            delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
            print(f"  retry {attempt}/{RETRY_ATTEMPTS - 1} after {delay:.0f}s (HTTP {resp.status_code})")
            time.sleep(delay)
            continue

        return resp

    raise RuntimeError(f"{method} {url} failed after {RETRY_ATTEMPTS} attempts: {last_err}")


def fetch_yfinance(tickers: list[str], start: str, end: str, output: str) -> None:
    try:
        import yfinance as yf
    except ImportError:
        _fail("yfinance not installed. Run: pip install yfinance")

    print(f"Fetching yfinance: {tickers} from {start} to {end}")
    data = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)

    if data.empty:
        _fail(f"yfinance returned no data for {tickers}. Check tickers and date range.")

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(output)
    print(f"Saved {len(data)} rows to {output}")
    print(f"Period: {data.index[0].date()} to {data.index[-1].date()}")


def fetch_fred(series: list[str], start: str, output: str) -> None:
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        print("FRED_API_KEY not set, falling back to public CSV endpoint.")
        print("  For higher reliability set FRED_API_KEY (free at fred.stlouisfed.org/docs/api/api_key.html)")
        _fetch_fred_csv(series, start, output)
        return

    base_url = "https://api.stlouisfed.org/fred/series/observations"
    all_series: dict[str, dict] = {}

    for s in series:
        resp = _http_get(base_url, params={
            "series_id": s,
            "api_key": api_key,
            "file_type": "json",
            "observation_start": start,
        })
        resp.raise_for_status()
        data = resp.json()
        if "observations" not in data:
            print(f"  WARNING: no observations for {s}: {data.get('error_message', 'unknown')}")
            continue
        all_series[s] = {
            obs["date"]: float(obs["value"]) if obs["value"] != "." else None
            for obs in data["observations"]
        }
        print(f"  fetched {len(all_series[s])} observations for {s}")
        time.sleep(0.1)

    if not all_series:
        _fail("No FRED series returned data.")

    df = pd.DataFrame(all_series)
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output)
    print(f"Saved FRED data ({len(df)} rows, {len(df.columns)} series) to {output}")


def _fetch_fred_csv(series: list[str], start: str, output: str) -> None:
    all_series: dict[str, pd.Series] = {}
    for s in series:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={s}"
        resp = _http_get(url)
        if resp.status_code != 200:
            print(f"  WARNING: could not fetch {s} (HTTP {resp.status_code})")
            continue
        from io import StringIO
        df = pd.read_csv(StringIO(resp.text), index_col=0, parse_dates=True)
        df = df[df.index >= pd.to_datetime(start)]
        all_series[s] = df.iloc[:, 0]
        print(f"  fetched {len(df)} observations for {s}")
        time.sleep(0.2)

    if not all_series:
        _fail("No FRED series returned data from CSV fallback.")

    combined = pd.DataFrame(all_series)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output)
    print(f"Saved FRED data to {output}")


def fetch_famafrench(dataset: str, output: str) -> None:
    try:
        import pandas_datareader as pdr
    except ImportError:
        _fail("pandas-datareader not installed. Run: pip install pandas-datareader")

    print(f"Fetching Fama-French dataset: {dataset}")
    data = pdr.get_data_famafrench(dataset, start="1926-01-01")

    Path(output).parent.mkdir(parents=True, exist_ok=True)

    if isinstance(data, dict) and any(isinstance(k, int) for k in data.keys()):
        for i, df in data.items():
            if not isinstance(i, int):
                continue
            out_path = output.replace(".csv", f"_table{i}.csv")
            df.to_csv(out_path)
            print(f"  saved table {i} ({len(df)} rows) to {out_path}")
    else:
        df = data[0] if isinstance(data, dict) else data
        df.to_csv(output)
        print(f"Saved {len(df)} rows to {output}")


def fetch_clinicaltrials(
    condition: str,
    output: str,
    intervention: str | None = None,
    phase: int | None = None,
    status: str = "Completed",
    max_results: int = 200,
) -> None:
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    params: dict = {
        "query.cond": condition,
        "filter.overallStatus": status.upper().replace(" ", "_"),
        "pageSize": min(max_results, 1000),
        "format": "json",
        "fields": (
            "NCTId,BriefTitle,OfficialTitle,Condition,InterventionName,"
            "Phase,OverallStatus,StartDate,PrimaryCompletionDate,"
            "CompletionDate,StudyType,EnrollmentCount,PrimaryOutcomeMeasure,"
            "SecondaryOutcomeMeasure,LeadSponsorName,LocationCountry"
        ),
    }
    if intervention:
        params["query.intr"] = intervention

    print(f"Fetching ClinicalTrials.gov: condition={condition!r}"
          + (f", intervention={intervention!r}" if intervention else "")
          + (f", phase={phase}" if phase else ""))

    resp = _http_get(base_url, params=params)
    resp.raise_for_status()
    studies = resp.json().get("studies", [])

    if phase is not None:
        phase_str = f"PHASE{phase}"
        studies = [
            s for s in studies
            if phase_str in str(s.get("protocolSection", {}).get("designModule", {}).get("phases", []))
        ]

    print(f"Retrieved {len(studies)} trials")

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(studies, f, indent=2)
    print(f"Saved to {output}")


def fetch_pubmed(query: str, output: str, n: int = 100) -> None:
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    print(f"Searching PubMed: {query!r} (n={n})")
    search_resp = _http_get(f"{base_url}esearch.fcgi", params={
        "db": "pubmed", "term": query, "retmax": n, "retmode": "json", "sort": "relevance",
    })
    search_resp.raise_for_status()
    ids = search_resp.json().get("esearchresult", {}).get("idlist", [])

    if not ids:
        print("No results found")
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w") as f:
            json.dump([], f)
        return

    print(f"Found {len(ids)} articles, fetching summaries...")

    time.sleep(0.34)
    summary_resp = _http_get(f"{base_url}esummary.fcgi", params={
        "db": "pubmed", "id": ",".join(ids), "retmode": "json",
    }, timeout=60)
    summary_resp.raise_for_status()
    summaries = summary_resp.json().get("result", {})

    results = []
    for pmid in ids:
        summary = summaries.get(pmid, {})
        results.append({
            "pmid": pmid,
            "title": summary.get("title", ""),
            "authors": [a.get("name", "") for a in summary.get("authors", [])],
            "journal": summary.get("fulljournalname", ""),
            "pub_date": summary.get("pubdate", ""),
            "doi": next((id_obj.get("value", "") for id_obj in summary.get("articleids", [])
                         if id_obj.get("idtype") == "doi"), ""),
            "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
        })

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved {len(results)} records to {output}")


def fetch_opentargets(target_id: str, output: str) -> None:
    query = """
    query TargetAssociations($ensemblId: String!) {
      target(ensemblId: $ensemblId) {
        id
        approvedName
        approvedSymbol
        associatedDiseases {
          count
          rows {
            disease { id name }
            score
            datatypeScores { componentId score }
          }
        }
      }
    }
    """
    url = "https://api.platform.opentargets.org/api/v4/graphql"
    resp = _http_post(url, json_body={"query": query, "variables": {"ensemblId": target_id}})
    resp.raise_for_status()
    data = resp.json()

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(data, f, indent=2)

    target = data.get("data", {}).get("target", {})
    n_diseases = target.get("associatedDiseases", {}).get("count", 0)
    print(f"OpenTargets: {target.get('approvedSymbol', target_id)}, {n_diseases} associated diseases")
    print(f"Saved to {output}")


def fetch_openfda(query: str, endpoint: str, output: str, limit: int = 100) -> None:
    endpoints = {
        "drug_approvals": "https://api.fda.gov/drug/drugsfda.json",
        "adverse_events": "https://api.fda.gov/drug/event.json",
        "drug_label": "https://api.fda.gov/drug/label.json",
    }
    url = endpoints[endpoint]

    print(f"Fetching openFDA: {endpoint}, query={query!r}")
    resp = _http_get(url, params={"search": query, "limit": limit})

    if resp.status_code == 404:
        print(f"No results found for query: {query}")
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        with open(output, "w") as f:
            json.dump([], f)
        return

    resp.raise_for_status()
    results = resp.json().get("results", [])
    print(f"Retrieved {len(results)} records")

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved to {output}")


def _add_common_args(sp: argparse.ArgumentParser) -> None:
    sp.add_argument("--output", required=True, help="Output file path")
    sp.add_argument("--cache-dir", default=DEFAULT_CACHE_DIR,
                    help=f"Local cache directory (default: {DEFAULT_CACHE_DIR})")
    sp.add_argument("--no-cache", action="store_true",
                    help="Bypass cache (always fetch fresh)")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fetch_data.py",
        description="Data fetcher for deep-quant-research. Pick a source as the first positional.",
    )
    sub = parser.add_subparsers(dest="source", required=True, metavar="source")

    p_yf = sub.add_parser("yfinance", help="Equity prices (yfinance)")
    p_yf.add_argument("--tickers", required=True, help="Comma-separated ticker list, e.g. AAPL,MSFT")
    p_yf.add_argument("--start", default="2015-01-01", help="Start date YYYY-MM-DD")
    p_yf.add_argument("--end", default=datetime.today().strftime("%Y-%m-%d"), help="End date YYYY-MM-DD")
    _add_common_args(p_yf)

    p_fred = sub.add_parser("fred", help="FRED macro series")
    p_fred.add_argument("--series", required=True, help="Comma-separated FRED series IDs, e.g. CPIAUCSL,FEDFUNDS")
    p_fred.add_argument("--start", default="2000-01-01", help="Start date YYYY-MM-DD")
    _add_common_args(p_fred)

    p_ff = sub.add_parser("famafrench", help="Fama-French factor returns")
    p_ff.add_argument("--dataset", required=True, help="Fama-French dataset name, e.g. F-F_Research_Data_5_Factors_2x3")
    _add_common_args(p_ff)

    p_ct = sub.add_parser("clinicaltrials", help="ClinicalTrials.gov registry")
    p_ct.add_argument("--condition", required=True, help="Condition keyword, e.g. NSCLC")
    p_ct.add_argument("--intervention", help="Intervention keyword")
    p_ct.add_argument("--phase", type=int, choices=[1, 2, 3, 4], help="Trial phase")
    p_ct.add_argument("--status", default="Completed", help="Trial status (default: Completed)")
    p_ct.add_argument("--max-results", type=int, default=200, dest="max_results",
                      help="Page size (default: 200, max: 1000)")
    _add_common_args(p_ct)

    p_pm = sub.add_parser("pubmed", help="PubMed literature")
    p_pm.add_argument("--query", required=True, help="Search query")
    p_pm.add_argument("--n", type=int, default=100, help="Number of results (default: 100)")
    _add_common_args(p_pm)

    p_ot = sub.add_parser("opentargets", help="OpenTargets gene-disease associations")
    p_ot.add_argument("--target", required=True, help="Ensembl gene ID, e.g. ENSG00000133703")
    _add_common_args(p_ot)

    p_fda = sub.add_parser("openfda", help="openFDA drug data")
    p_fda.add_argument("--query", required=True, help="Search query")
    p_fda.add_argument("--endpoint", default="drug_approvals",
                       choices=["drug_approvals", "adverse_events", "drug_label"],
                       help="openFDA endpoint (default: drug_approvals)")
    p_fda.add_argument("--limit", type=int, default=100, help="Result limit (default: 100)")
    _add_common_args(p_fda)

    return parser


def main() -> None:
    args = _build_parser().parse_args()
    source = args.source

    if source == "yfinance":
        _validate_date(args.start, "--start")
        _validate_date(args.end, "--end")
        _validate_date_order(args.start, args.end)
        tickers = _csv_list(args.tickers, "--tickers")
        payload = {"tickers": sorted(tickers), "start": args.start, "end": args.end}
        ext = "csv"
        runner = lambda: fetch_yfinance(tickers, args.start, args.end, args.output)
    elif source == "fred":
        _validate_date(args.start, "--start")
        series = _csv_list(args.series, "--series")
        payload = {"series": sorted(series), "start": args.start}
        ext = "csv"
        runner = lambda: fetch_fred(series, args.start, args.output)
    elif source == "famafrench":
        payload = {"dataset": args.dataset}
        ext = "csv"
        runner = lambda: fetch_famafrench(args.dataset, args.output)
    elif source == "clinicaltrials":
        payload = {
            "condition": args.condition, "intervention": args.intervention,
            "phase": args.phase, "status": args.status, "max_results": args.max_results,
        }
        ext = "json"
        runner = lambda: fetch_clinicaltrials(
            args.condition, args.output, args.intervention, args.phase, args.status, args.max_results,
        )
    elif source == "pubmed":
        payload = {"query": args.query, "n": args.n}
        ext = "json"
        runner = lambda: fetch_pubmed(args.query, args.output, args.n)
    elif source == "opentargets":
        payload = {"target": args.target}
        ext = "json"
        runner = lambda: fetch_opentargets(args.target, args.output)
    elif source == "openfda":
        payload = {"query": args.query, "endpoint": args.endpoint, "limit": args.limit}
        ext = "json"
        runner = lambda: fetch_openfda(args.query, args.endpoint, args.output, args.limit)
    else:
        _fail(f"Unknown source: {source}")

    fp = _fingerprint(source, payload)

    if not args.no_cache and _try_cache_hit(args.cache_dir, fp, ext, args.output):
        return

    runner()

    if not args.no_cache:
        _cache_store(args.cache_dir, fp, ext, args.output, {"source": source, "payload": payload})


if __name__ == "__main__":
    main()
