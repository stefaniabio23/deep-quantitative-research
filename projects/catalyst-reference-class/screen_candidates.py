#!/usr/bin/env python3
"""Screen live biotech tickers through the full pipeline end to end:
ticker -> lead drug -> Open Targets MOA enrichment -> reference-class
base-rate thesis.

ticker->drug is a curated input (candidates.csv); there is no free
ticker->pipeline join, so the lead asset is human-supplied (verified from
filings/press). This is a real-world stress test: it shows the enrichment
works on live names, and reveals where the curated corpus is too thin to
form a base rate (most names), which is the empirical case for the v2
scale-out. A reference class needs a mechanistic core match (MOA / target /
indication) against the corpus; situational tags alone do not qualify.
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from enrich_opentargets import enrich_one, load_aliases  # noqa: E402
from run_reference_class import load_corpus, retrieve, base_rates  # noqa: E402

OUT_DIR = HERE / "expected-output"


def screen() -> None:
    corpus = load_corpus()
    aliases = load_aliases()
    cands = list(csv.DictReader(open(HERE / "candidates.csv")))
    rows = []
    for c in cands:
        if c["disease_area"] == "device":
            rows.append({**c, "ot_moa": "(not a drug)", "n": 0, "base_rate": "", "confidence": "out-of-scope"})
            continue
        e = enrich_one(c["drug"], aliases)
        q = {"disease_area": c["disease_area"], "indication": c["indication"],
             "moa": c["moa"], "target": c.get("target", ""), "modality": c["modality"]}
        an = retrieve(corpus, q)
        br = base_rates(an) if len(an) else {"n": 0, "confidence": "none"}
        rows.append({
            **c,
            "ot_moa": e.get("ot_moa", "") if e.get("resolved") else "(unresolved)",
            "n": br["n"],
            "base_rate": f"{br.get('p_success', 0):.0%}" if br["n"] else "",
            "confidence": br["confidence"],
            "analogues": ", ".join(an.head(3)["drug"].tolist()) if br["n"] else "",
        })

    with_class = [r for r in rows if r["n"]]
    L = ["# Live ticker screen through the reference-class pipeline", ""]
    L.append(f"Screened {len(rows)} tickers. Enrichment is live (Open Targets); "
             f"the reference class is matched against the {len(corpus)}-catalyst curated corpus.")
    L.append("")
    L.append(f"- **{len(with_class)}/{len(rows)} produced a reference-class base rate.** "
             "The rest have no mechanistic analogue in the curated corpus yet, the "
             "coverage gap that the v2 scale-out closes.")
    L.append("")
    L.append("| Ticker | Drug | MOA (verified) | OT MOA (auto) | Ref class n | Base rate | Confidence | Read |")
    L.append("|---|---|---|---|---:|---:|---|---|")
    for r in rows:
        read = (f"analogues: {r['analogues']}" if r["n"] else
                ("device, out of scope" if r["confidence"] == "out-of-scope" else "no class in corpus yet"))
        L.append(f"| {r['ticker']} | {r['drug']} | {r['moa']} | {r['ot_moa']} | "
                 f"{r['n'] or ''} | {r['base_rate']} | {r['confidence']} | {read} |")
    L += ["", "## Theses (where a reference class exists)", ""]
    for r in with_class:
        L.append(f"- **{r['ticker']} ({r['drug']}, {r['indication']})**: reference class of "
                 f"{r['n']} ({r['confidence']} confidence), base rate {r['base_rate']} success. "
                 f"Closest analogues: {r['analogues']}. Caveat: matched on "
                 f"{'MOA/modality' if r['moa'] in corpus['moa'].values else 'indication'}, "
                 "verify the class is mechanistically apt before relying on it.")
    L += ["", "## Honest limits", ""]
    L.append("- ticker->drug is curated (no free ticker->pipeline source); only the lead asset is screened.")
    L.append("- A 34-catalyst corpus covers few mechanisms, so most live names return no class. This is the "
             "expected result and the case for v2 (auto-enrich the full trial universe).")
    L.append("- Indication-only matches (e.g. an obesity drug pulling GLP-1 analogues) can be mechanistically "
             "wrong; the read flags the match basis.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "candidate-screen.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    screen()
