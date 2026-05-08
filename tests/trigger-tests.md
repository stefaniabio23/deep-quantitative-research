# Trigger Tests

Tests to verify the `deep-quant-research` skill loads at the right times.

Run each query. The skill should load automatically for all "Should trigger" cases.

---

## Should trigger

### Finance
- "Research what drives EBITDA multiple expansion in European pharma"
- "What KPIs are most predictive of stock price in med-tech?"
- "Backtest a momentum strategy on European small-caps"
- "Run a factor analysis on my portfolio returns"
- "Is revenue growth correlated with next-quarter returns?"
- "What is the lag between earnings revisions and price moves?"
- "Analyse the correlation between gross margin and EV/EBITDA"
- "Deep research on what drives biotech valuations"

### Biotech
- "Analyse the clinical data on KRAS G12C inhibitors"
- "Research the genomic landscape of NSCLC"
- "What does the clinical evidence show for CAR-T in solid tumours?"
- "Find and summarise Phase 3 data on [drug name]"
- "Literature review on PARP inhibitors"
- "Is biomarker selection associated with better OS in oncology trials?"

### Quant
- "Factor analysis on my monthly returns"
- "Test whether the Value factor outperforms during high inflation"
- "Distance correlation between oil price and energy sector returns"
- "Research macro drivers of credit spreads"
- "Analyse the dependence structure of European sector returns"
- "Is the momentum factor crowded?"

### Mixed
- "Research the investment case for European oncology"
- "What are the key data catalysts for [biotech company] and how have similar catalysts affected peers?"

---

## Should NOT trigger

- "Help me write a Python function"
- "What's the weather forecast?"
- "Summarise this article" (generic, not research-oriented)
- "Fix this bug in my code"
- "How do I use pandas?"
- "Write me a cover letter"

---

## Mode-specific triggers

- `/thesis-test:` — should activate thesis-test mode
- `/quick:` — should activate quick mode
- `/data-first:` — should activate data-first mode
- `/literature:` — should activate literature mode

---

## Expected behaviour

On trigger, Claude should:
1. Acknowledge the research question
2. Ask for any critical clarifying information (or proceed if the question is clear)
3. Begin Phase 1 with `question-sharpener` — present a refined hypothesis for confirmation
4. Not skip directly to analysis without hypothesis confirmation

The skill should NOT trigger if the user is just asking Claude a factual question ("what is a Sharpe ratio?") without an intent to conduct structured research.
