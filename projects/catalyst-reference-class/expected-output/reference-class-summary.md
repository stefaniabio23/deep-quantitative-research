# Catalyst reference-class engine, v1 (curated corpus)

Corpus: 34 catalysts across 4 disease areas.

## Base rate by reference class (disease x MOA, n >= 2)

| Disease | MOA | n | P(success) | Weighted | Confidence |
|---|---|---:|---:|---:|---|
| cns | anti-amyloid mAb | 7 | 43% | 0.43 | medium |
| metabolic | fgf21 analog | 2 | 50% | 0.75 | insufficient |
| metabolic | gip/glp-1 dual agonist | 2 | 100% | 1.00 | insufficient |
| oncology | kras g12c inhibitor | 2 | 100% | 1.00 | insufficient |
| rare | aav gene therapy | 4 | 75% | 0.75 | low |
| rare | exon-skipping antisense | 3 | 100% | 1.00 | low |

## Leave-one-out calibration (does the method work?)

- Predicted 21 events from their reference classes.
- Mean predicted success when the event actually **succeeded**: **0.76**; when it actually **failed**: **0.60** (separation +0.16).
- Accuracy at 0.5 threshold: **62%**; Brier score 0.179.

Positive separation means events the engine rated likely-success did succeed more often than those it rated likely-failure: the reference-class base rate carries real signal.

## Example theses

### If aducanumab (alzheimers) were upcoming

Query: disease_area=cns, indication=alzheimers, moa=anti-amyloid mAb, target=amyloid-beta, modality=mab, phase=pdufa
Situation tags: accelerated_approval;surrogate_endpoint;adcom;first_in_class;controversial

Reference class: **6 analogues** (confidence: **medium**).
Base rate: **33% success**, 0% mixed, 67% failure. Weighted success score **0.33**.

Closest analogues:

| Drug | Company | Indication | MOA | Outcome | Score |
|---|---|---|---|---|---:|
| lecanemab | BIIB | alzheimers | anti-amyloid mAb | success | 11 |
| donanemab | LLY | alzheimers | anti-amyloid mAb | success | 11 |
| gantenerumab | RHHBY | alzheimers | anti-amyloid mAb | failure | 9 |
| solanezumab | LLY | alzheimers | anti-amyloid mAb | failure | 9 |
| crenezumab | RHHBY | alzheimers | anti-amyloid mAb | failure | 9 |
| bapineuzumab | PFE | alzheimers | anti-amyloid mAb | failure | 9 |

### If efruxifermin (mash) were upcoming

Query: disease_area=metabolic, indication=mash, moa=fgf21 analog, target=FGF21, modality=peptide, phase=ph2
Situation tags: surrogate_endpoint

Reference class: **2 analogues** (confidence: **insufficient**).
Base rate: **100% success**, 0% mixed, 0% failure. Weighted success score **1.00**.
_Caution: small reference class. Treat the base rate as a weak prior, not a probability._

Closest analogues:

| Drug | Company | Indication | MOA | Outcome | Score |
|---|---|---|---|---|---:|
| pegozafermin | ETNB | mash | fgf21 analog | success | 11 |
| resmetirom | MDGL | mash | thr-beta agonist | success | 5 |

