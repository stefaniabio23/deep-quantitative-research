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
from pathlib import Path

import requests

HERE = Path(__file__).parent
CORPUS = HERE / "catalysts.csv"
OUT_DIR = HERE / "expected-output"

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
    # resolver scoring: a results-bearing, phase-matched, large, on-date trial
    # outscores a no-results one (which is disqualified).
    good = {"has_results": True, "phases": ["PHASE3"], "enrollment": 1200,
            "completion": "2023-01", "sponsor": "Eli Lilly and Company"}
    assert score_candidate(good, "PHASE3", "Eli Lilly", 2023) > 5, score_candidate(good, "PHASE3", "Eli Lilly", 2023)
    assert score_candidate({"has_results": False}, "PHASE3", "x", 2023) < 0
    print("self-test OK: CT.gov outcome derivation + resolver scoring.")
    return 0


# Indication -> CT.gov condition search term (abbreviations need expanding).
INDICATION_CONDITION = {
    "alzheimers": "alzheimer", "mash": "steatohepatitis", "nash": "steatohepatitis",
    "dmd": "duchenne", "nsclc": "lung cancer", "major_depression": "major depressive disorder",
    "dementia_psychosis": "dementia psychosis", "hemophilia_a": "hemophilia a",
    "hemophilia_b": "hemophilia b", "sma": "spinal muscular atrophy",
    "sickle_cell": "sickle cell", "beta_thalassemia": "thalassemia",
}
SEARCH_FIELDS = (
    "protocolSection.identificationModule.nctId,protocolSection.designModule.phases,"
    "protocolSection.designModule.enrollmentInfo,protocolSection.statusModule.overallStatus,"
    "protocolSection.statusModule.primaryCompletionDateStruct,"
    "protocolSection.sponsorCollaboratorsModule.leadSponsor,hasResults"
)


def search_candidates(drug: str, condition: str) -> list[dict]:
    try:
        r = requests.get(API, params={"query.intr": drug, "query.cond": condition,
                                       "pageSize": 50, "fields": SEARCH_FIELDS}, timeout=30)
        if r.status_code != 200:
            return []
        studies = r.json().get("studies", [])
    except (requests.Timeout, requests.ConnectionError):
        return []
    out = []
    for s in studies:
        p = s.get("protocolSection", {})
        d = p.get("designModule", {})
        out.append({
            "nct": p.get("identificationModule", {}).get("nctId", ""),
            "phases": d.get("phases") or [],
            "enrollment": (d.get("enrollmentInfo") or {}).get("count", 0) or 0,
            "completion": (p.get("statusModule", {}).get("primaryCompletionDateStruct") or {}).get("date", ""),
            "sponsor": (p.get("sponsorCollaboratorsModule", {}).get("leadSponsor") or {}).get("name", ""),
            "has_results": bool(s.get("hasResults")),
        })
    return out


def score_candidate(c: dict, phase: str, company: str, target_year: int | None) -> float:
    """Pure: rank a candidate trial as the pivotal one for a catalyst."""
    s = 0.0
    if not c.get("has_results"):
        return -1.0  # can't label it; disqualify
    if phase and phase.upper().replace("PH", "PHASE") in [p for p in c.get("phases", [])]:
        s += 3
    s += min(c.get("enrollment", 0) / 500.0, 4)  # pivotal trials are large
    cy = c.get("completion", "")[:4]
    if target_year and cy.isdigit():
        s += max(0, 3 - abs(int(cy) - target_year))
    if company and c.get("sponsor"):
        toks = company.lower().replace("/", " ").split()
        if any(t in c["sponsor"].lower() for t in toks if len(t) > 3):
            s += 1
    return s


def resolve_nct(drug: str, indication: str, phase: str, company: str = "",
                target_year: int | None = None) -> tuple[str, float]:
    cond = INDICATION_CONDITION.get(indication, indication)
    cands = search_candidates(drug, cond)
    scored = [(c["nct"], score_candidate(c, phase, company, target_year)) for c in cands]
    scored = [(n, sc) for n, sc in scored if sc >= 0]
    if not scored:
        return ("", 0.0)
    return max(scored, key=lambda x: x[1])


def resolve_and_validate(corpus_path: Path = CORPUS, out_dir: Path = OUT_DIR) -> dict:
    """Auto-resolve each curated-NCT catalyst from scratch (drug+indication+
    phase+sponsor+date), label the resolved trial, and check outcome agreement
    vs hand. The 9 curated NCTs are the ground truth: the meaningful metric is
    whether the resolver+labeler produce the right OUTCOME, not the exact NCT
    (multiple valid pivotal trials exist per drug)."""
    import csv
    rows = [r for r in csv.DictReader(open(corpus_path)) if r.get("nct_id", "").strip()]
    out, agree, exact = [], 0, 0
    for c in rows:
        ty = int(c["catalyst_date"][:4]) if c.get("catalyst_date", "")[:4].isdigit() else None
        nct, score = resolve_nct(c["drug"], c["indication"], c["phase"], c["company"], ty)
        auto = label_nct(nct)["outcome"] if nct else "unresolved"
        match = auto == c["outcome"]
        agree += match
        exact += (nct == c["nct_id"])
        out.append({"drug": c["drug"], "curated_nct": c["nct_id"], "resolved_nct": nct,
                    "auto_outcome": auto, "hand_outcome": c["outcome"], "outcome_match": match})
        time.sleep(0.3)
    n = len(rows)
    L = ["# Drug -> NCT auto-resolver validation", ""]
    L.append(f"Run on the {n} curated-NCT catalysts (ground truth).")
    L.append("")
    L.append(f"- **Outcome agreement** (resolver+labeler vs hand): **{agree}/{n}**.")
    L.append(f"- Exact pivotal-NCT recovery: {exact}/{n} (strict; multiple valid trials exist per drug).")
    L.append("")
    L.append("| Drug | curated NCT | resolved NCT | auto | hand | outcome match |")
    L.append("|---|---|---|---|---|---|")
    for o in out:
        L.append(f"| {o['drug']} | {o['curated_nct']} | {o['resolved_nct'] or '(none)'} | {o['auto_outcome']} | {o['hand_outcome']} | {o['outcome_match']} |")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ctgov-resolver-validation.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return {"n": n, "agree": agree, "exact": exact}


def label_corpus(corpus_path: Path = CORPUS, out_dir: Path = OUT_DIR) -> dict:
    """Auto-label outcome for every corpus catalyst that has a curated nct_id,
    and compare to the hand outcome. Validates the trial-results labeler at the
    corpus level. nct_id is curated (verified pivotal trial) because naive
    drug->NCT search is too noisy to resolve the pivotal trial automatically."""
    import csv
    rows = list(csv.DictReader(open(corpus_path)))
    out, agree, divergent = [], 0, []
    n_nct = 0
    for c in rows:
        nct = c.get("nct_id", "").strip()
        if not nct:
            continue
        n_nct += 1
        r = label_nct(nct)
        auto, hand = r["outcome"], c["outcome"]
        status = "match" if auto == hand else ("unlabeled" if auto == "unlabeled" else "divergent")
        if status == "match":
            agree += 1
        elif status == "divergent":
            divergent.append((c["drug"], nct, auto, hand))
        out.append({"event_id": c["event_id"], "drug": c["drug"], "nct_id": nct,
                    "primary_pvalue": r["primary_pvalue"], "auto_outcome": auto,
                    "hand_outcome": hand, "status": status})
        time.sleep(0.3)
    labeled = [o for o in out if o["status"] != "unlabeled"]
    L = ["# CT.gov corpus outcome auto-labeling", ""]
    L.append(f"- Catalysts with a curated NCT: {n_nct}/{len(rows)}.")
    L.append(f"- Auto-labeled (clean p-value signal): {len(labeled)}/{n_nct}.")
    L.append(f"- Auto-outcome matches hand: **{agree}/{len(labeled)}**.")
    if divergent:
        L.append("")
        L.append("Divergent (trial outcome != hand/regulatory outcome, a real distinction):")
        for drug, nct, auto, hand in divergent:
            L.append(f"- {drug} [{nct}]: trial={auto}, hand={hand}")
    L.append("")
    L.append("| Drug | NCT | primary p | auto | hand | status |")
    L.append("|---|---|---:|---|---|---|")
    for o in out:
        L.append(f"| {o['drug']} | {o['nct_id']} | {o['primary_pvalue']} | {o['auto_outcome']} | {o['hand_outcome']} | {o['status']} |")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ctgov-outcome-labeling.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))
    return {"n_nct": n_nct, "labeled": len(labeled), "agree": agree}


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return _self_test()
    if "--corpus" in argv:
        label_corpus()
        return 0
    if "--resolve" in argv:
        resolve_and_validate()
        return 0
    print("Live CT.gov outcome derivation (demo):\n")
    for label, nct in DEMO:
        r = label_nct(nct)
        print(f"  {label} [{nct}]: status={r['status']}, has_results={r['has_results']}, "
              f"primary_p={r['primary_pvalue']} -> OUTCOME = {r['outcome'].upper()}")
        time.sleep(0.3)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
