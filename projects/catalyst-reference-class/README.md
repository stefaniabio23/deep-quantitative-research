# Catalyst reference-class engine

Reference-class forecasting for biotech catalysts. Instead of forecasting
one drug from its own story (the inside view), forecast it from what
happened to the class of drugs like it: same mechanism, target, disease,
and situation. Given an upcoming binary event, the engine retrieves its
historical analogues and reads the base-rate outcome distribution off that
class.

This is the clinical-outcome core of the larger catalyst system. It is
**survivorship-immune** (clinical outcomes don't disappear when a ticker is
acquired or delisted, the way prices do), which is why it leads. The price-
reaction overlay (the `biotech-sell-the-news` work) layers on top later.

## Use

```bash
# Base rates per reference class + leave-one-out calibration + examples
python run_reference_class.py

# Thesis for an upcoming situation, by exemplar...
python run_reference_class.py --like aducanumab-2021
# ...or by explicit query
python run_reference_class.py --disease cns --moa "anti-amyloid mAb"
python run_reference_class.py --disease metabolic --moa "fgf21 analog"

# Just the method-validation backtest
python run_reference_class.py --backtest
```

## What it does

1. **Retrieve.** Score analogues by disease area, MOA, target, modality,
   phase, and shared situational tags. A candidate qualifies only on a
   *core* match (mechanism or indication), so generic tags like
   `accelerated_approval` alone never pull an unrelated drug into the class.
2. **Base rates.** Outcome distribution (success / mixed / failure) over the
   class, with a confidence label capped by class size (insufficient < 3,
   low < 5, medium < 8, high otherwise). A base rate over 3 analogues is a
   weak prior, not a probability, and the engine says so.
3. **Thesis.** A readable read for one situation: the class, its size and
   confidence, the base rate, and the closest named analogues.
4. **Leave-one-out backtest.** For every event, predict its outcome from its
   analogues (itself excluded) and measure calibration. This validates the
   method, not a single call.

## v1 result (curated corpus, 34 catalysts, 4 areas)

Reference-class base rates the engine reads off the corpus:

| Disease | MOA | n | P(success) |
|---|---|---:|---:|
| CNS | anti-amyloid mAb | 7 | 43% |
| rare | AAV gene therapy | 4 | 75% |
| rare | exon-skipping antisense | 3 | 100% |
| metabolic | GIP/GLP-1 dual agonist | 2 | 100% |
| oncology | KRAS G12C inhibitor | 2 | 100% |

**Leave-one-out calibration:** across 21 predictable events, events the
engine rated likely-success actually succeeded more often (mean predicted
0.76) than those it rated likely-failure (0.60), separation **+0.16**,
accuracy 62%, Brier 0.179. On a 34-event corpus that is real signal, and it
will sharpen as the corpus grows.

Worked example, the anti-amyloid mAb class: an Alzheimer's anti-amyloid
antibody has a **33-43% base rate of success** (lecanemab and donanemab
worked; gantenerumab, solanezumab, crenezumab, bapineuzumab did not). That
is the outside-view prior any new anti-amyloid program should be judged
against.

## Corpus and the path to scale

`catalysts.csv` is the input; the engine is source-agnostic. v1 is curated
from domain knowledge (MOA and outcome are high-confidence facts; **audit
before any real use**). v2 auto-generates the corpus from captured datasets:

- **Disease, situation, outcome signal:** AACT / ClinicalTrials.gov
  (conditions to MeSH, phase, status, `why_stopped`, and the results
  `outcome_analyses` p-values).
- **MOA and target:** Open Targets (`mechanismsOfAction`, target, disease
  via EFO) and ChEMBL (`mechanism_of_action`), joined to the AACT
  intervention by normalized drug name (ChEMBL synonyms, UNII, RxNorm).
- **Regulatory outcome:** FDA Orange/Purple Book + openFDA (approved vs CRL).
- Company-doc scraping is a gap-filler for exact dates and soft tags only,
  not the spine; the ontologies cover MOA and disease far more reliably.

The binding constraint for v2 is the drug-name join (free-text AACT
intervention to ontology molecule), where coverage will leak.

## Verification

`run_reference_class.py --self-test` builds a synthetic corpus with two MOA
classes at planted base rates (75% vs 25%), confirms the engine recovers
them, and confirms leave-one-out separates actual successes from failures.

## Caveats

- Small reference classes are the core risk; the engine caps confidence and
  reports `n`, never presenting a 2-3 member class as a probability.
- v1 corpus is curated and partial; base rates will move as it grows. The
  numbers here are illustrative of the method, not settled base rates.
- Outcome is coarse (success / mixed / failure). v2 should separate clinical
  (endpoint met) from regulatory (approved) outcomes.
- No price-reaction overlay yet; that is the next layer and needs a
  survivorship-clean price source (see `biotech-sell-the-news`).
