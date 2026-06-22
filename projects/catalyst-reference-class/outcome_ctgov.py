#!/usr/bin/env python3
"""v2 enrichment, outcome-labeling leg (issue #1): derive a catalyst-level
outcome from ClinicalTrials.gov trial results (API v2, free, no auth).

The FDA leg gives drug-level approval status but cannot adjudicate a specific
catalyst's failure (CRLs aren't published, approval is time/indication
aggregated). The trial-results signal is catalyst-level: did the trial's
PRIMARY outcome hit? CT.gov posts, for completed trials, the primary outcome
measure and its statistical analysis (p-value), which is exactly that.

Outcome rule:
- results posted + primary-outcome p < 0.05  -> success (endpoint met)
- results posted + primary-outcome p >= 0.05 -> failure (endpoint missed)
- no results, status terminated/withdrawn      -> failure (coarse)
- otherwise                                     -> unlabeled

Honest limits: results-posting is sparse and lagged, the primary p-value is
not always structured, and direction is not checked (a significant p in the
wrong direction would read as success). So this auto-labels the subset with
posted results and defers the rest. NCT resolution (drug -> trial) is the
other coverage leak, handled by the AACT/CT.gov search in a later commit.

  --self-test   offline parser check on a canned study (no network)
  (default)     fetch a small demo set of NCTs and print derived outcomes
"""

from __future__ import annotations

import sys
import time

import requests

API = "https://clinicaltrials.gov/api/v2/studies"
FIELDS = (
    "protocolSection.statusModule.overallStatus,"
    "protocolSection.statusModule.whyStopped,"
    "hasResults,resultsSection.outcomeMeasuresModule"
)
# Known catalysts for the live demo (drug, NCT). Outcomes are read live, not
# hardcoded, so the demo shows what the signal actually returns.
DEMO = [
    ("KarXT (Karuna EMERGENT-2)", "NCT04659161"),
    ("zuranolone (Sage MOUNTAIN)", "NCT03672175"),
    ("resmetirom (Madrigal MAESTRO-NASH)", "NCT03900429"),
]


def parse_pvalue(raw) -> float | None:
    """'<0.0001' -> 0.0001; '0.115' -> 0.115; non-numeric -> None."""
    if raw is None:
        return None
    s = str(raw).strip().lstrip("<>=").strip()
    try:
        return float(s)
    except ValueError:
        return None


def parse_ctgov(study: dict) -> dict:
    proto = study.get("protocolSection", {})
    status = proto.get("statusModule", {}).get("overallStatus", "")
    why = proto.get("statusModule", {}).get("whyStopped", "")
    has_results = bool(study.get("hasResults"))
    oms = study.get("resultsSection", {}).get("outcomeMeasuresModule", {}).get("outcomeMeasures", [])
    primary_p = None
    primary_title = ""
    for om in oms:
        if om.get("type") == "PRIMARY":
            primary_title = om.get("title", "")
            for an in om.get("analyses", []):
                p = parse_pvalue(an.get("pValue"))
                if p is not None:
                    primary_p = p
                    break
            break
    return {
        "status": status,
        "why_stopped": why,
        "has_results": has_results,
        "primary_title": primary_title,
        "primary_pvalue": primary_p,
    }


def derive_outcome(parsed: dict) -> str:
    p = parsed.get("primary_pvalue")
    if parsed.get("has_results") and p is not None:
        return "success" if p < 0.05 else "failure"
    if parsed.get("status") in ("TERMINATED", "WITHDRAWN", "SUSPENDED"):
        return "failure"
    return "unlabeled"


def fetch_study(nct: str) -> dict:
    for attempt in range(4):
        try:
            r = requests.get(f"{API}/{nct}", params={"fields": FIELDS}, timeout=30)
        except (requests.Timeout, requests.ConnectionError):
            time.sleep(2 ** attempt)
            continue
        if r.status_code == 429:
            time.sleep(2 ** attempt)
            continue
        if r.status_code != 200:
            return {}
        return r.json()
    return {}


def label_nct(nct: str) -> dict:
    parsed = parse_ctgov(fetch_study(nct))
    return {"nct": nct, "outcome": derive_outcome(parsed), **parsed}


_CANNED = {
    "protocolSection": {"statusModule": {"overallStatus": "COMPLETED"}},
    "hasResults": True,
    "resultsSection": {"outcomeMeasuresModule": {"outcomeMeasures": [
        {"type": "PRIMARY", "title": "Change From Baseline in PANSS",
         "analyses": [{"pValue": "<0.0001", "statisticalMethod": "MMRM"}]},
    ]}},
}
_CANNED_FAIL = {
    "protocolSection": {"statusModule": {"overallStatus": "COMPLETED"}},
    "hasResults": True,
    "resultsSection": {"outcomeMeasuresModule": {"outcomeMeasures": [
        {"type": "PRIMARY", "title": "HAM-D change", "analyses": [{"pValue": "0.115"}]},
    ]}},
}


def _self_test() -> int:
    assert parse_pvalue("<0.0001") == 0.0001
    assert parse_pvalue("0.115") == 0.115
    assert parse_pvalue("n/a") is None
    s = parse_ctgov(_CANNED)
    assert s["primary_pvalue"] == 0.0001 and derive_outcome(s) == "success", s
    f = parse_ctgov(_CANNED_FAIL)
    assert derive_outcome(f) == "failure", f
    assert derive_outcome({"status": "TERMINATED", "has_results": False}) == "failure"
    assert derive_outcome({"status": "RECRUITING", "has_results": False}) == "unlabeled"
    print("self-test OK: CT.gov primary-outcome p-value -> catalyst outcome.")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return _self_test()
    print("Live CT.gov outcome derivation (demo):\n")
    for label, nct in DEMO:
        r = label_nct(nct)
        print(f"  {label} [{nct}]: status={r['status']}, has_results={r['has_results']}, "
              f"primary_p={r['primary_pvalue']} -> OUTCOME = {r['outcome'].upper()}")
        time.sleep(0.3)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
