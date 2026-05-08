# Mode Guide

## Which mode to use

**quick** — You want a fast answer, not a rigorous one. Good for: initial scoping, checking whether a question is worth pursuing, 30-minute turnarounds. No backtest, no causal analysis, no critique cluster.

**full** — Default. Complete pipeline. Use when you want a defensible finding. Critique cluster runs but doesn't block if one critic fails.

**thesis-test** — You have a specific hypothesis and you want it stress-tested, not explored. All three critics required. Use before presenting a thesis to a committee, portfolio manager, or in a publication.

**data-first** — You have a dataset and you want to know what it says. Skips originality-scout (you're not looking for novelty, you're exploring data). Runs data quality audit early.

**literature** — You want to understand what the field knows, not produce original analysis. No data fetching, no regression. Runs originality-scout and knowledge-base-builder as the core.

**thorough** — Maximum rigour. All critics required. Revision loop enabled — FATAL critique challenges route back to the relevant analysis agent for targeted fixes (max 2 rounds). Use for publication-quality output or high-stakes decisions.

---

## Quick decision tree

1. Do you have a dataset already? → **data-first**
2. Do you want to survey literature only? → **literature**
3. Do you have a specific thesis to stress-test? → **thesis-test**
4. Do you need an answer in under an hour? → **quick**
5. Is this going into a report, presentation, or publication? → **thorough**
6. Otherwise → **full**
