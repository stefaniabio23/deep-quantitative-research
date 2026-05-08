"""
Data fetching script for deep-quant-research.
Supports: yfinance, FRED, Fama-French, ClinicalTrials.gov, PubMed, OpenTargets, openFDA.
"""

import argparse
import json
import os
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


def fetch_yfinance(tickers: list[str], start: str, end: str, output: str) -> None:
    try:
        import yfinance as yf
    except ImportError:
        print("yfinance not installed. Run: pip install yfinance")
        sys.exit(1)

    print(f"Fetching yfinance data: {tickers} from {start} to {end}")
    data = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)

    if data.empty:
        print(f"WARNING: No data returned for {tickers}. Check tickers and date range.")
        sys.exit(1)

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(output)
    print(f"Saved {len(data)} rows to {output}")
    print(f"Period: {data.index[0].date()} to {data.index[-1].date()}")
    print(f"Columns: {list(data.columns)}")


def fetch_fred(series: list[str], start: str, output: str) -> None:
    api_key = os.environ.get("FRED_API_KEY")
    if not api_key:
        print("FRED_API_KEY not set. Get a free key at fred.stlouisfed.org/docs/api/api_key.html")
        print("Set with: export FRED_API_KEY=your_key_here")
        print("Attempting to fetch CSV directly from FRED as fallback...")
        _fetch_fred_csv(series, start, output)
        return

    base_url = "https://api.stlouisfed.org/fred/series/observations"
    all_series = {}

    for s in series:
        params = {
            "series_id": s,
            "api_key": api_key,
            "file_type": "json",
            "observation_start": start,
        }
        resp = requests.get(base_url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if "observations" not in data:
            print(f"WARNING: No data for series {s}: {data.get('error_message', 'unknown error')}")
            continue

        observations = data["observations"]
        values = {
            obs["date"]: float(obs["value"]) if obs["value"] != "." else None
            for obs in observations
        }
        all_series[s] = values
        print(f"Fetched {len(values)} observations for {s}")
        time.sleep(0.1)

    df = pd.DataFrame(all_series)
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output)
    print(f"Saved FRED data ({len(df)} rows, {len(df.columns)} series) to {output}")


def _fetch_fred_csv(series: list[str], start: str, output: str) -> None:
    all_series = {}
    for s in series:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={s}"
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            print(f"WARNING: Could not fetch {s} from FRED CSV endpoint")
            continue
        from io import StringIO
        df = pd.read_csv(StringIO(resp.text), index_col=0, parse_dates=True)
        df = df[df.index >= pd.to_datetime(start)]
        all_series[s] = df.iloc[:, 0]
        print(f"Fetched {len(df)} observations for {s}")
        time.sleep(0.2)

    combined = pd.DataFrame(all_series)
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(output)
    print(f"Saved FRED data to {output}")


def fetch_famafrench(dataset: str, output: str) -> None:
    try:
        import pandas_datareader as pdr
    except ImportError:
        print("pandas-datareader not installed. Run: pip install pandas-datareader")
        sys.exit(1)

    print(f"Fetching Fama-French dataset: {dataset}")
    data = pdr.get_data_famafrench(dataset, start="1926-01-01")

    Path(output).parent.mkdir(parents=True, exist_ok=True)

    if isinstance(data, tuple):
        for i, df in enumerate(data):
            out_path = output.replace(".csv", f"_table{i}.csv")
            df.to_csv(out_path)
            print(f"Saved table {i} ({len(df)} rows) to {out_path}")
    else:
        data.to_csv(output)
        print(f"Saved {len(data)} rows to {output}")


def fetch_clinicaltrials(
    condition: str,
    output: str,
    intervention: str = None,
    phase: int = None,
    status: str = "Completed",
    max_results: int = 200,
) -> None:
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
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

    print(f"Fetching ClinicalTrials.gov: condition='{condition}'" +
          (f", intervention='{intervention}'" if intervention else "") +
          (f", phase={phase}" if phase else ""))

    resp = requests.get(base_url, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    studies = data.get("studies", [])

    if phase is not None:
        phase_str = f"PHASE{phase}"
        studies = [
            s for s in studies
            if phase_str in str(s.get("protocolSection", {})
                                .get("designModule", {})
                                .get("phases", []))
        ]

    print(f"Retrieved {len(studies)} trials")

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(studies, f, indent=2)
    print(f"Saved to {output}")


def fetch_pubmed(query: str, output: str, n: int = 100) -> None:
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"

    search_params = {
        "db": "pubmed",
        "term": query,
        "retmax": n,
        "retmode": "json",
        "sort": "relevance",
    }
    print(f"Searching PubMed: '{query}' (n={n})")
    search_resp = requests.get(f"{base_url}esearch.fcgi", params=search_params, timeout=30)
    search_resp.raise_for_status()
    search_data = search_resp.json()

    ids = search_data.get("esearchresult", {}).get("idlist", [])
    if not ids:
        print("No results found")
        return

    print(f"Found {len(ids)} articles. Fetching abstracts...")

    fetch_params = {
        "db": "pubmed",
        "id": ",".join(ids),
        "retmode": "json",
        "rettype": "abstract",
    }
    time.sleep(0.34)
    fetch_resp = requests.get(f"{base_url}efetch.fcgi", params=fetch_params, timeout=60)

    summary_params = {
        "db": "pubmed",
        "id": ",".join(ids),
        "retmode": "json",
    }
    time.sleep(0.34)
    summary_resp = requests.get(f"{base_url}esummary.fcgi", params=summary_params, timeout=60)
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
    resp = requests.post(
        url,
        json={"query": query, "variables": {"ensemblId": target_id}},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(data, f, indent=2)

    target = data.get("data", {}).get("target", {})
    n_diseases = target.get("associatedDiseases", {}).get("count", 0)
    print(f"OpenTargets: {target.get('approvedSymbol', target_id)} — {n_diseases} associated diseases")
    print(f"Saved to {output}")


def fetch_openfda(query: str, endpoint: str, output: str, limit: int = 100) -> None:
    endpoints = {
        "drug_approvals": "https://api.fda.gov/drug/drugsfda.json",
        "adverse_events": "https://api.fda.gov/drug/event.json",
        "drug_label": "https://api.fda.gov/drug/label.json",
    }
    url = endpoints.get(endpoint, endpoints["drug_approvals"])
    params = {"search": query, "limit": limit}

    print(f"Fetching openFDA: {endpoint} — '{query}'")
    resp = requests.get(url, params=params, timeout=30)

    if resp.status_code == 404:
        print(f"No results found for query: {query}")
        return

    resp.raise_for_status()
    data = resp.json()
    results = data.get("results", [])
    print(f"Retrieved {len(results)} records")

    Path(output).parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Saved to {output}")


def main():
    parser = argparse.ArgumentParser(description="Data fetcher for deep-quant-research")
    parser.add_argument("--source", required=True,
                        choices=["yfinance", "fred", "famafrench", "clinicaltrials",
                                 "pubmed", "opentargets", "openfda"],
                        help="Data source")
    parser.add_argument("--output", required=True, help="Output file path")

    # yfinance
    parser.add_argument("--tickers", help="Comma-separated ticker list (yfinance)")
    parser.add_argument("--start", default="2015-01-01", help="Start date YYYY-MM-DD")
    parser.add_argument("--end", default=datetime.today().strftime("%Y-%m-%d"), help="End date")

    # FRED
    parser.add_argument("--series", help="Comma-separated FRED series IDs")

    # Fama-French
    parser.add_argument("--dataset", help="Fama-French dataset name")

    # ClinicalTrials
    parser.add_argument("--condition", help="ClinicalTrials.gov condition")
    parser.add_argument("--intervention", help="ClinicalTrials.gov intervention")
    parser.add_argument("--phase", type=int, help="Trial phase (2, 3, etc.)")
    parser.add_argument("--status", default="Completed", help="Trial status")

    # PubMed
    parser.add_argument("--query", help="Search query (PubMed or openFDA)")
    parser.add_argument("--n", type=int, default=100, help="Number of results")

    # OpenTargets
    parser.add_argument("--target", help="Ensembl gene ID (OpenTargets)")

    # openFDA
    parser.add_argument("--endpoint", default="drug_approvals",
                        choices=["drug_approvals", "adverse_events", "drug_label"],
                        help="openFDA endpoint")

    args = parser.parse_args()

    if args.source == "yfinance":
        tickers = [t.strip() for t in args.tickers.split(",")]
        fetch_yfinance(tickers, args.start, args.end, args.output)
    elif args.source == "fred":
        series = [s.strip() for s in args.series.split(",")]
        fetch_fred(series, args.start, args.output)
    elif args.source == "famafrench":
        fetch_famafrench(args.dataset, args.output)
    elif args.source == "clinicaltrials":
        fetch_clinicaltrials(args.condition, args.output, args.intervention,
                             args.phase, args.status, args.n)
    elif args.source == "pubmed":
        fetch_pubmed(args.query, args.output, args.n)
    elif args.source == "opentargets":
        fetch_opentargets(args.target, args.output)
    elif args.source == "openfda":
        fetch_openfda(args.query, args.endpoint, args.output, args.n)


if __name__ == "__main__":
    main()
