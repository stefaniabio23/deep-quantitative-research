# {{Experiment Name}}

Experiment record. One per run. Path: `experiments/runs/<run-id>/run.yaml` (machine-readable) plus this markdown as the human-readable narrative.

## Objective

{{What are you testing in one sentence. Reference the hypothesis_id.}}

## Setup

- Signal: `{{signal_id}}`
- Target dataset: `{{target_dataset_id}}`
- Predictor datasets: `{{predictor_ids}}`
- Registry commit: `{{commit_hash}}`
- Code commit: `{{code_commit}}`
- Run mode: KPI prediction | tradable signal
- Period: train {{train_period}}, test {{test_period}}

## Method

{{What was actually done. Cadence chosen, feature grid scope, lag set, validation set design. Two paragraphs max.}}

## Result

- Outcome: {{one sentence: signal confirmed | partial | refuted | inconclusive}}.
- Metric headline: {{the single number that summarises}}.
- Confidence: {{low | medium | high}}.
- Binding constraint: {{check_name from validation report}}.

## Interpretation

{{Why did it work or fail? What is the relationship_type? Pull from the causal-inference output.}}

## Key Insight

{{The ONE thing learned. One sentence.}}

## Decision

Keep | Kill | Iterate.

If Iterate, name the next experiment.

## Next Step

- {{One concrete action with owner and rough timing.}}

## Links

- Hypothesis: `experiments/ideas/{{slug}}.yaml`
- SignalSpec: `experiments/specs/{{slug}}.yaml`
- Signal card: `signal-card.md`
- Validation: `validation-report.md`
