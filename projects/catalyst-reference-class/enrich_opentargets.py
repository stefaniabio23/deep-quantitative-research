#!/usr/bin/env python3
"""v2 enrichment (issue #1): auto-derive MOA / target / modality / disease for
a catalyst from its drug name, via the Open Targets GraphQL API.

This is the first leg of replacing the hand-curated corpus tags with
ontology-derived ones. Open Targets (free, no auth) covers the hardest tag,
mechanism of action, plus target, modality (drugType), and indications. The
binding constraint, flagged on issue #1, is the drug-name -> ChEMBL-molecule
join: research codes and combination drugs will not resolve, and that
coverage leak is measured here rather than hidden.

Modes:
  --self-test   offline parser check on a canned response (no network)
  --validate    enrich every drug in catalysts.csv, compare to the hand tags,
                write enriched-corpus.csv + a coverage report (live)
  (default = --validate)

Outcome labeling (approved vs CRL) and the AACT trial/disease/situation join
are the next legs; this leg proves the MOA/target spine and quantifies the
name-join coverage.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pandas as pd
import requests

HERE = Path(__file__).parent
CORPUS = HERE / "catalysts.csv"
ALIASES = HERE / "drug_aliases.csv"
OUT_DIR = HERE / "expected-output"
OT_API = "https://api.platform.opentargets.org/api/v4/graphql"

SEARCH_Q = "query($q:String!){search(queryString:$q,entityNames:[\"drug\"]){hits{id name entity}}}"
DRUG_Q = (
    "query($id:String!){drug(chemblId:$id){id name drugType "
    "mechanismsOfAction{rows{mechanismOfAction actionType targets{approvedSymbol}}} "
    "indications{rows{disease{name}}}}}"
)

# Open Targets drugType -> the corpus modality vocabulary.
MODALITY_MAP = {
    "Antibody": "mab",
    "Small molecule": "small_molecule",
    "Oligonucleotide": "antisense",
    "Gene therapy": "gene_therapy",
    "Cell therapy": "gene_therapy",
    "Protein": "peptide",
    "Enzyme": "peptide",
}


def _gql(query: str, variables: dict) -> dict:
    for attempt in range(5):
        try:
            r = requests.post(OT_API, json={"query": query, "variables": variables}, timeout=30)
        except (requests.Timeout, requests.ConnectionError):
            time.sleep(2 ** attempt)
            continue
        if r.status_code == 429:
            time.sleep(2 ** attempt)
            continue
        if r.status_code != 200:
            return {}
        return r.json().get("data", {}) or {}
    return {}


def resolve_chembl(name: str) -> str | None:
    data = _gql(SEARCH_Q, {"q": name})
    hits = (data.get("search") or {}).get("hits", [])
    for h in hits:
        if h.get("entity") == "drug":
            return h["id"]
    return None


def fetch_drug(chembl_id: str) -> dict:
    return (_gql(DRUG_Q, {"id": chembl_id}) or {}).get("drug") or {}


def parse_drug(drug: dict) -> dict:
    """Pure: extract MOA / target / modality / indications from a drug record."""
    if not drug:
        return {}
    rows = (drug.get("mechanismsOfAction") or {}).get("rows", [])
    moa = rows[0]["mechanismOfAction"] if rows else ""
    action = rows[0].get("actionType", "") if rows else ""
    target = ""
    for row in rows:
        for t in row.get("targets", []):
            if t.get("approvedSymbol"):
                target = t["approvedSymbol"]
                break
        if target:
            break
    drug_type = drug.get("drugType", "") or ""
    inds = [r["disease"]["name"] for r in (drug.get("indications") or {}).get("rows", [])]
    return {
        "ot_name": drug.get("name", ""),
        "ot_moa": moa,
        "ot_action": action,
        "ot_target": target,
        "ot_modality": MODALITY_MAP.get(drug_type, drug_type.lower().replace(" ", "_")),
        "ot_drug_type": drug_type,
        "ot_indications": "; ".join(inds[:4]),
    }


def load_aliases(path: Path = ALIASES) -> dict:
    """corpus_name (lower) -> {resolve_as, manual_moa, manual_target, manual_modality}."""
    if not path.exists():
        return {}
    df = pd.read_csv(path).fillna("")
    return {str(r["corpus_name"]).lower(): r.to_dict() for _, r in df.iterrows()}


def enrich_one(name: str, aliases: dict | None = None) -> dict:
    aliases = aliases or {}
    # 1. direct name resolution
    cid = resolve_chembl(name)
    if cid:
        return {"resolved": True, "path": "direct", "chembl_id": cid, **parse_drug(fetch_drug(cid))}
    a = aliases.get(name.lower())
    if a:
        # 2. synonym / INN re-resolution (e.g. KarXT -> xanomeline)
        if a.get("resolve_as"):
            cid = resolve_chembl(a["resolve_as"])
            if cid:
                return {"resolved": True, "path": "alias", "alias_used": a["resolve_as"],
                        "chembl_id": cid, **parse_drug(fetch_drug(cid))}
        # 3. manual override for compounds not in ChEMBL (e.g. VK2735)
        if a.get("manual_moa"):
            return {"resolved": True, "path": "manual", "chembl_id": "",
                    "ot_name": "", "ot_moa": a["manual_moa"], "ot_action": "",
                    "ot_target": a.get("manual_target", ""),
                    "ot_modality": a.get("manual_modality", ""),
                    "ot_drug_type": "", "ot_indications": ""}
    return {"resolved": False, "path": "unresolved"}


def validate(corpus_path: Path, out_dir: Path) -> dict:
    corpus = pd.read_csv(corpus_path).fillna("")
    aliases = load_aliases()
    rows = []
    for _, c in corpus.iterrows():
        e = enrich_one(str(c["drug"]), aliases)
        rows.append(
            {
                "event_id": c["event_id"],
                "drug": c["drug"],
                "resolved": e.get("resolved", False),
                "path": e.get("path", "unresolved"),
                "chembl_id": e.get("chembl_id", ""),
                "hand_moa": c["moa"],
                "ot_moa": e.get("ot_moa", ""),
                "hand_target": c["target"],
                "ot_target": e.get("ot_target", ""),
                "hand_modality": c["modality"],
                "ot_modality": e.get("ot_modality", ""),
                "ot_indications": e.get("ot_indications", ""),
            }
        )
        time.sleep(0.3)  # be polite to the API
    df = pd.DataFrame(rows)
    n, res = len(df), int(df["resolved"].sum())
    by_path = df["path"].value_counts().to_dict()
    modality_agree = int(((df["resolved"]) & (df["hand_modality"] == df["ot_modality"])).sum())

    out_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_dir / "enriched-corpus.csv", index=False)

    L = ["# Open Targets enrichment coverage (v2 leg 1, with alias layer)", ""]
    L.append(f"- Tagged: **{res}/{n}** ({res/n:.0%}).")
    L.append(
        f"- By path: direct (Open Targets) {by_path.get('direct', 0)}, "
        f"alias / INN re-resolve {by_path.get('alias', 0)}, "
        f"manual (not in ChEMBL) {by_path.get('manual', 0)}, "
        f"unresolved {by_path.get('unresolved', 0)}."
    )
    L.append(f"- Modality auto-match vs hand tag (of resolved): {modality_agree}/{res}.")
    L.append("")
    if by_path.get("unresolved", 0):
        L.append("Still unresolved:")
        L.append("")
        for _, r in df[~df["resolved"]].iterrows():
            L.append(f"- {r['drug']} ({r['event_id']})")
        L.append("")
    L.append("Resolved, hand vs Open Targets (for inspection):")
    L.append("")
    L.append("| Drug | hand MOA | OT MOA | hand target | OT target | hand mod | OT mod |")
    L.append("|---|---|---|---|---|---|---|")
    for _, r in df[df["resolved"]].iterrows():
        L.append(
            f"| {r['drug']} | {r['hand_moa']} | {r['ot_moa']} | {r['hand_target']} "
            f"| {r['ot_target']} | {r['hand_modality']} | {r['ot_modality']} |"
        )
    (out_dir / "enrichment-coverage.md").write_text("\n".join(L) + "\n")
    print("\n".join(L[:12]))
    print(f"\nwrote {out_dir/'enriched-corpus.csv'} and {out_dir/'enrichment-coverage.md'}")
    return {"n": n, "resolved": res}


# Canned Open Targets response for the offline parser self-test.
_CANNED = {
    "id": "CHEMBL3833321",
    "name": "LECANEMAB",
    "drugType": "Antibody",
    "mechanismsOfAction": {"rows": [
        {"mechanismOfAction": "Amyloid-beta A4 protein inhibitor",
         "actionType": "INHIBITOR", "targets": [{"approvedSymbol": "APP"}]}
    ]},
    "indications": {"rows": [
        {"disease": {"name": "Cognitive impairment"}},
        {"disease": {"name": "Alzheimer disease"}},
    ]},
}


def _self_test() -> int:
    p = parse_drug(_CANNED)
    assert p["ot_modality"] == "mab", p["ot_modality"]
    assert "Amyloid" in p["ot_moa"], p["ot_moa"]
    assert p["ot_target"] == "APP", p["ot_target"]
    assert "Alzheimer disease" in p["ot_indications"], p["ot_indications"]
    assert parse_drug({}) == {}
    print("self-test OK: Open Targets drug record parsed (MOA/target/modality/indications).")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return _self_test()
    validate(CORPUS, OUT_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
