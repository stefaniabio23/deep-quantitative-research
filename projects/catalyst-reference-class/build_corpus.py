#!/usr/bin/env python3
"""v2 corpus scale-out (issue #1): auto-build catalyst rows from
ClinicalTrials.gov instead of hand-curating them.

For a condition, pull completed Phase 3 trials that posted results, extract
the experimental drug and the primary-outcome p-value (-> outcome), enrich
MOA / target / modality via Open Targets, and emit catalyst rows in the
corpus schema. This is how the reference-class corpus grows from dozens
toward the trial universe, which is what makes the base rates statistically
real (the live ticker screen showed 34 catalysts cover too few mechanisms).

Honest coverage leaks, measured here:
- drug-name -> ChEMBL join (brands, dosing strings, research codes don't all
  resolve; same constraint the alias layer addresses)
- results-posting + structured-p-value gaps (some trials -> unlabeled)

Output is written to corpus_auto/ and is NOT merged into the curated
catalysts.csv without review; auto-tags need spot-checking first.

  python build_corpus.py <condition> <disease_area> [max_studies]
  python build_corpus.py --self-test
"""

from __future__ import annotations

import csv
import re
import sys
import time
from pathlib import Path

import requests

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from enrich_opentargets import enrich_one, load_aliases  # noqa: E402
from outcome_ctgov import label_nct  # noqa: E402

API = "https://clinicaltrials.gov/api/v2/studies"
OUT_DIR = HERE / "corpus_auto"
SEARCH_FIELDS = (
    "protocolSection.identificationModule.nctId,protocolSection.designModule.phases,"
    "protocolSection.statusModule.overallStatus,protocolSection.armsInterventionsModule.interventions,"
    "hasResults"
)


UNITS = {"mg", "eq", "ml", "mcg", "g", "iv", "po", "qd", "bid", "kg", "mg/kg", "mg/ml", "%", "units"}


def clean_drug(name: str) -> str:
    """Strip dosing tokens but keep research codes that contain digits:
    'PP3M 175 mg eq.' -> 'PP3M'; 'Cariprazine 3 mg' -> 'Cariprazine'.
    A token ends the name only if it is a pure number or a dosing unit, not
    merely because it contains a digit (codes like PP3M / AXS-05 are kept)."""
    name = re.sub(r"\(.*?\)", "", name)
    tokens = []
    for t in name.split():
        if re.fullmatch(r"\d+\.?\d*", t) or t.lower().strip(".") in UNITS:
            break
        tokens.append(t)
    return " ".join(tokens).strip() or name.strip()


def experimental_drugs(study: dict) -> list[str]:
    ivs = study.get("protocolSection", {}).get("armsInterventionsModule", {}).get("interventions", [])
    out = []
    for i in ivs:
        if i.get("type") in ("DRUG", "BIOLOGICAL", "GENETIC"):
            n = i.get("name", "")
            if n and "placebo" not in n.lower():
                out.append(clean_drug(n))
    return out


def search_condition(condition: str, page_size: int = 100) -> list[dict]:
    try:
        r = requests.get(API, params={"query.cond": condition, "aggFilters": "phase:3",
                                       "pageSize": page_size, "fields": SEARCH_FIELDS}, timeout=30)
        return r.json().get("studies", []) if r.status_code == 200 else []
    except (requests.Timeout, requests.ConnectionError):
        return []


def build_corpus(condition: str, disease_area: str, max_studies: int = 25) -> dict:
    aliases = load_aliases()
    studies = [
        s for s in search_condition(condition)
        if s.get("hasResults")
        and "PHASE3" in (s["protocolSection"].get("designModule", {}).get("phases") or [])
        and s["protocolSection"]["statusModule"]["overallStatus"] == "COMPLETED"
    ][:max_studies]

    rows, seen = [], set()
    for s in studies:
        nct = s["protocolSection"]["identificationModule"]["nctId"]
        drugs = experimental_drugs(s)
        if not drugs:
            continue
        drug = drugs[0]
        if drug.lower() in seen:
            continue
        seen.add(drug.lower())
        outcome = label_nct(nct)["outcome"]
        e = enrich_one(drug, aliases)
        rows.append({
            "event_id": f"{drug.lower().replace(' ', '-')}-{nct}",
            "drug": drug, "disease_area": disease_area, "indication": condition,
            "moa": e.get("ot_moa", "") if e.get("resolved") else "",
            "target": e.get("ot_target", "") if e.get("resolved") else "",
            "modality": e.get("ot_modality", "") if e.get("resolved") else "",
            "phase": "ph3", "outcome": outcome, "nct_id": nct,
            "moa_resolved": bool(e.get("resolved")), "source": "ctgov-auto",
        })
        time.sleep(0.4)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fn = OUT_DIR / f"auto-corpus-{condition.replace(' ', '-')}.csv"
    if rows:
        with open(fn, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    n = len(rows)
    moa_ok = sum(r["moa_resolved"] for r in rows)
    labeled = sum(r["outcome"] != "unlabeled" for r in rows)
    print(f"{condition}: {len(studies)} completed-ph3-with-results trials -> {n} unique-drug catalysts")
    print(f"  MOA auto-resolved: {moa_ok}/{n} | outcome auto-labeled: {labeled}/{n}")
    print(f"  wrote {fn}")
    return {"condition": condition, "n": n, "moa_resolved": moa_ok, "labeled": labeled}


def _self_test() -> int:
    assert clean_drug("PP3M 175 mg eq.") == "PP3M", clean_drug("PP3M 175 mg eq.")
    assert clean_drug("Cariprazine") == "Cariprazine"
    assert clean_drug("Aducanumab 10 mg/kg") == "Aducanumab"
    assert clean_drug("AXS-05 45 mg") == "AXS-05", clean_drug("AXS-05 45 mg")
    s = {"protocolSection": {"armsInterventionsModule": {"interventions": [
        {"type": "DRUG", "name": "Cariprazine 3 mg"}, {"type": "DRUG", "name": "Placebo"},
        {"type": "OTHER", "name": "questionnaire"}]}}}
    assert experimental_drugs(s) == ["Cariprazine"], experimental_drugs(s)
    print("self-test OK: drug cleaning + experimental-arm extraction.")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return _self_test()
    if len(argv) < 2:
        raise SystemExit("usage: build_corpus.py <condition> <disease_area> [max_studies]")
    cap = int(argv[2]) if len(argv) > 2 else 25
    build_corpus(argv[0], argv[1], cap)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
