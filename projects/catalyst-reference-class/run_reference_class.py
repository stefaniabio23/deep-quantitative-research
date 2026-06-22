#!/usr/bin/env python3
"""Catalyst reference-class engine.

Given a biotech catalyst (a drug in a disease area with a mechanism and a
situation), find its historical analogues and read the base-rate outcome
distribution off that reference class. This is the outside view: instead of
forecasting one drug from its own story, forecast it from what happened to
the class of drugs like it.

The engine is source-agnostic; it runs on any corpus (catalysts.csv) with
the tag columns, whether those tags were hand-curated (v1) or auto-derived
from AACT + Open Targets + FDA (v2).

What it does:
- retrieve(query): score and rank analogues by disease area, MOA, target,
  modality, phase, and shared situational tags.
- base_rates(analogues): outcome distribution (success / mixed / failure)
  with a confidence label capped by class size.
- thesis(query): a readable reference-class read for one situation, by
  explicit query or by exemplar (--like <event_id>).
- backtest (leave-one-out): for every event, predict its outcome from its
  analogues (itself excluded) and measure calibration. This validates the
  reference-class method, not a single call.

Usage:
  python run_reference_class.py                       # base rates + backtest + examples
  python run_reference_class.py --like aducanumab-2021
  python run_reference_class.py --disease cns --moa "anti-amyloid mAb"
  python run_reference_class.py --backtest
  python run_reference_class.py --self-test
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).parent
CORPUS = HERE / "catalysts.csv"
OUT_DIR = HERE / "expected-output"

SUCCESS_VALUE = {"success": 1.0, "mixed": 0.5, "failure": 0.0}
# Scoring weights for analogue similarity.
W_DISEASE, W_INDICATION, W_MOA, W_TARGET, W_MODALITY, W_PHASE, W_TAG = 2, 2, 4, 3, 1, 1, 1
MIN_ANALOGUE_SCORE = 2     # below this, not an analogue
LOO_MIN_SCORE = 4          # a leave-one-out reference class needs real similarity
LOO_MIN_N = 2


def _tagset(s) -> set[str]:
    if not isinstance(s, str) or not s.strip():
        return set()
    return {t.strip() for t in s.split(";") if t.strip()}


def load_corpus(path: Path = CORPUS) -> pd.DataFrame:
    df = pd.read_csv(path).fillna({"tags": "", "note": ""})
    for col in ("disease_area", "indication", "moa", "target", "modality", "phase", "outcome"):
        df[col] = df[col].astype(str).str.strip()
    return df


def _score(query: dict, row) -> tuple[int, bool]:
    """Return (similarity score, is_core_match). A core match means the
    analogue shares the mechanism (MOA or target) or the indication; without
    one, shared situational tags alone do not make something an analogue."""
    s = 0
    core = False
    if query.get("disease_area") and query["disease_area"] == row["disease_area"]:
        s += W_DISEASE
    if query.get("indication") and query["indication"] == row["indication"]:
        s += W_INDICATION
        core = True
    if query.get("moa") and query["moa"].lower() == str(row["moa"]).lower():
        s += W_MOA
        core = True
    elif query.get("target") and query["target"] == row["target"]:
        s += W_TARGET
        core = True
    if query.get("modality") and query["modality"] == row["modality"]:
        s += W_MODALITY
    if query.get("phase") and query["phase"] == row["phase"]:
        s += W_PHASE
    s += len(_tagset(query.get("tags", "")) & _tagset(row["tags"])) * W_TAG
    return s, core


def retrieve(
    corpus: pd.DataFrame, query: dict, *, exclude_id=None,
    min_score=MIN_ANALOGUE_SCORE, require_core=True,
) -> pd.DataFrame:
    rows = corpus[corpus["event_id"] != exclude_id].copy()
    scored = rows.apply(lambda r: _score(query, r), axis=1)
    rows["score"] = [s for s, _ in scored]
    rows["core"] = [c for _, c in scored]
    keep = rows["score"] >= min_score
    if require_core:
        keep &= rows["core"]
    return rows[keep].sort_values("score", ascending=False)


def base_rates(analogues: pd.DataFrame) -> dict:
    n = len(analogues)
    if n == 0:
        return {"n": 0, "confidence": "none"}
    vals = analogues["outcome"].map(SUCCESS_VALUE).fillna(0.5)
    out = {
        "n": n,
        "p_success": float((analogues["outcome"] == "success").mean()),
        "p_mixed": float((analogues["outcome"] == "mixed").mean()),
        "p_failure": float((analogues["outcome"] == "failure").mean()),
        "weighted_success_rate": float(vals.mean()),
    }
    out["confidence"] = (
        "insufficient" if n < 3 else "low" if n < 5 else "medium" if n < 8 else "high"
    )
    return out


def query_from_row(row) -> dict:
    return {
        "disease_area": row["disease_area"],
        "indication": row["indication"],
        "moa": row["moa"],
        "target": row["target"],
        "modality": row["modality"],
        "phase": row["phase"],
        "tags": row["tags"],
    }


def thesis(corpus: pd.DataFrame, query: dict, *, exclude_id=None, title="") -> str:
    an = retrieve(corpus, query, exclude_id=exclude_id)
    r = base_rates(an)
    L = [f"### {title or 'Reference-class thesis'}", ""]
    desc = ", ".join(f"{k}={v}" for k, v in query.items() if v and k != "tags")
    L.append(f"Query: {desc}")
    if query.get("tags"):
        L.append(f"Situation tags: {query['tags']}")
    L.append("")
    if r["n"] == 0:
        L.append("No analogues found in the corpus. No base rate can be formed.")
        return "\n".join(L) + "\n"
    L.append(
        f"Reference class: **{r['n']} analogues** "
        f"(confidence: **{r['confidence']}**)."
    )
    L.append(
        f"Base rate: **{r['p_success']:.0%} success**, {r['p_mixed']:.0%} mixed, "
        f"{r['p_failure']:.0%} failure. Weighted success score "
        f"**{r['weighted_success_rate']:.2f}**."
    )
    if r["confidence"] in ("insufficient", "low"):
        L.append(
            "_Caution: small reference class. Treat the base rate as a weak "
            "prior, not a probability._"
        )
    L.append("")
    L.append("Closest analogues:")
    L.append("")
    L.append("| Drug | Company | Indication | MOA | Outcome | Score |")
    L.append("|---|---|---|---|---|---:|")
    for _, a in an.head(8).iterrows():
        L.append(
            f"| {a['drug']} | {a['ticker']} | {a['indication']} | {a['moa']} "
            f"| {a['outcome']} | {int(a['score'])} |"
        )
    return "\n".join(L) + "\n"


def class_base_rates(corpus: pd.DataFrame) -> pd.DataFrame:
    """Base rate per (disease_area, moa) class with at least 2 members."""
    rows = []
    for (da, moa), g in corpus.groupby(["disease_area", "moa"]):
        if len(g) < 2:
            continue
        r = base_rates(g)
        rows.append(
            {
                "disease_area": da,
                "moa": moa,
                "n": r["n"],
                "p_success": round(r["p_success"], 3),
                "weighted_success_rate": round(r["weighted_success_rate"], 3),
                "confidence": r["confidence"],
            }
        )
    return pd.DataFrame(rows).sort_values(["disease_area", "n"], ascending=[True, False])


def leave_one_out(corpus: pd.DataFrame) -> dict:
    """For each event with a clear outcome, predict it from its analogues and
    measure calibration. Validates the reference-class method itself."""
    preds, actuals, ids = [], [], []
    for _, row in corpus.iterrows():
        if row["outcome"] not in ("success", "failure"):
            continue
        an = retrieve(corpus, query_from_row(row), exclude_id=row["event_id"], min_score=LOO_MIN_SCORE)
        if len(an) < LOO_MIN_N:
            continue
        preds.append(base_rates(an)["weighted_success_rate"])
        actuals.append(SUCCESS_VALUE[row["outcome"]])
        ids.append(row["event_id"])
    if not preds:
        return {"n": 0}
    preds, actuals = np.array(preds), np.array(actuals)
    succ = preds[actuals == 1.0]
    fail = preds[actuals == 0.0]
    acc = float(np.mean((preds >= 0.5) == (actuals == 1.0)))
    brier = float(np.mean((preds - actuals) ** 2))
    return {
        "n": len(preds),
        "mean_pred_when_success": float(succ.mean()) if len(succ) else float("nan"),
        "mean_pred_when_failure": float(fail.mean()) if len(fail) else float("nan"),
        "separation": (float(succ.mean()) - float(fail.mean())) if len(succ) and len(fail) else float("nan"),
        "accuracy_at_0.5": acc,
        "brier_score": brier,
        "ids": ids,
        "preds": preds.tolist(),
        "actuals": actuals.tolist(),
    }


def run(corpus_path: Path, out_dir: Path) -> dict:
    corpus = load_corpus(corpus_path)
    classes = class_base_rates(corpus)
    loo = leave_one_out(corpus)

    out_dir.mkdir(parents=True, exist_ok=True)
    classes.to_csv(out_dir / "class-base-rates.csv", index=False)
    if loo.get("n"):
        pd.DataFrame({"event_id": loo["ids"], "predicted": loo["preds"], "actual": loo["actuals"]}).to_csv(
            out_dir / "loo-calibration.csv", index=False
        )

    L = ["# Catalyst reference-class engine, v1 (curated corpus)", ""]
    L.append(f"Corpus: {len(corpus)} catalysts across {corpus['disease_area'].nunique()} disease areas.")
    L.append("")
    L.append("## Base rate by reference class (disease x MOA, n >= 2)")
    L.append("")
    L.append("| Disease | MOA | n | P(success) | Weighted | Confidence |")
    L.append("|---|---|---:|---:|---:|---|")
    for _, c in classes.iterrows():
        L.append(
            f"| {c['disease_area']} | {c['moa']} | {int(c['n'])} | {c['p_success']:.0%} "
            f"| {c['weighted_success_rate']:.2f} | {c['confidence']} |"
        )
    if loo.get("n"):
        L += ["", "## Leave-one-out calibration (does the method work?)", ""]
        L.append(f"- Predicted {loo['n']} events from their reference classes.")
        L.append(
            f"- Mean predicted success when the event actually **succeeded**: "
            f"**{loo['mean_pred_when_success']:.2f}**; when it actually **failed**: "
            f"**{loo['mean_pred_when_failure']:.2f}** (separation "
            f"{loo['separation']:+.2f})."
        )
        L.append(f"- Accuracy at 0.5 threshold: **{loo['accuracy_at_0.5']:.0%}**; Brier score {loo['brier_score']:.3f}.")
        L.append("")
        L.append(
            "Positive separation means events the engine rated likely-success "
            "did succeed more often than those it rated likely-failure: the "
            "reference-class base rate carries real signal."
        )
    # Example theses.
    L += ["", "## Example theses", ""]
    for eid in ("aducanumab-2021", "efruxifermin-2023"):
        if (corpus["event_id"] == eid).any():
            row = corpus[corpus["event_id"] == eid].iloc[0]
            L.append(
                thesis(corpus, query_from_row(row), exclude_id=eid,
                       title=f"If {row['drug']} ({row['indication']}) were upcoming")
            )
    summary = "\n".join(L) + "\n"
    (out_dir / "reference-class-summary.md").write_text(summary)
    print(summary)
    return {"classes": classes, "loo": loo}


def _self_test() -> int:
    """Synthetic corpus: two MOA classes with planted base rates; confirm the
    engine recovers them and that leave-one-out separates success from fail."""
    rng = np.random.default_rng(3)
    rows = []
    for i in range(12):  # class A: 75% success
        rows.append(dict(event_id=f"A{i}", drug=f"a{i}", company="x", ticker="X",
                         disease_area="da", indication="ind_a", moa="moa_a", target="t_a",
                         modality="mab", phase="ph3",
                         outcome="success" if i % 4 != 0 else "failure", tags="", note=""))
    for i in range(12):  # class B: 25% success
        rows.append(dict(event_id=f"B{i}", drug=f"b{i}", company="y", ticker="Y",
                         disease_area="db", indication="ind_b", moa="moa_b", target="t_b",
                         modality="small_molecule", phase="ph3",
                         outcome="success" if i % 4 == 0 else "failure", tags="", note=""))
    corpus = pd.DataFrame(rows)

    ra = base_rates(retrieve(corpus, {"disease_area": "da", "moa": "moa_a"}))
    rb = base_rates(retrieve(corpus, {"disease_area": "db", "moa": "moa_b"}))
    assert ra["p_success"] > 0.6, ra
    assert rb["p_success"] < 0.4, rb
    assert ra["confidence"] == "high"

    loo = leave_one_out(corpus)
    assert loo["n"] >= 16, loo["n"]
    assert loo["separation"] > 0.1, loo["separation"]
    print("self-test OK: planted class base rates recovered, LOO separates success from failure.")
    return 0


def main(argv: list[str]) -> int:
    if "--self-test" in argv:
        return _self_test()
    corpus = load_corpus()
    if "--like" in argv:
        eid = argv[argv.index("--like") + 1]
        if not (corpus["event_id"] == eid).any():
            raise SystemExit(f"unknown event_id {eid!r}")
        row = corpus[corpus["event_id"] == eid].iloc[0]
        print(thesis(corpus, query_from_row(row), exclude_id=eid,
                     title=f"If {row['drug']} were upcoming"))
        return 0
    if any(a in argv for a in ("--disease", "--moa", "--indication", "--target")):
        q = {}
        for key in ("disease", "moa", "indication", "target", "modality", "phase", "tags"):
            flag = f"--{key}"
            if flag in argv:
                q["disease_area" if key == "disease" else key] = argv[argv.index(flag) + 1]
        print(thesis(corpus, q, title="Reference-class thesis"))
        return 0
    if "--backtest" in argv:
        loo = leave_one_out(corpus)
        print(f"LOO: n={loo.get('n')}, separation={loo.get('separation'):+.2f}, "
              f"accuracy={loo.get('accuracy_at_0.5'):.0%}, brier={loo.get('brier_score'):.3f}")
        return 0
    run(CORPUS, OUT_DIR)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
