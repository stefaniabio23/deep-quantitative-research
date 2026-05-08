# Pipeline Monitor

A lightweight validation protocol, not an agent. Runs automatically between every phase via `scripts/validate_output.py`. Checks that each phase produced a valid handoff block before the next phase starts.

---

## Handoff validation schema

Every phase must produce a block conforming to this structure:

```yaml
phase_status:
  phase: string
  completed: true | false
  required_fields_present: true | false
  evidence_attached: true | false       # files referenced in output exist on disk
  confidence_defined: true | false      # confidence or verdict field populated
  downstream_ready: true | false        # final gate: all above true
  retry_required: false | true
  failure_reason: null | string
  degraded_output: false | true
  degraded_fields: []
```

```bash
python scripts/validate_output.py --phase [agent_name] --output_dir ./[slug]/
```

---

## Retry logic

If `downstream_ready: false`:

1. List all failing fields in `failure_reason`
2. Re-run the agent with an explicit instruction: "The following required fields are missing: [list]. Complete them before producing the handoff block."
3. Re-validate

If still failing after one retry: set `degraded_output: true`, populate `degraded_fields`, continue with downstream agents informed of the degraded state. Affected conclusions are tagged `low_confidence: true` in the final report.

---

## Hard stops

Some failures are not recoverable by retry:

| Condition | Action |
|-----------|--------|
| data_quality verdict = DO_NOT_PROCEED | Hard stop. Inform user. Do not continue. |
| All three critique critics fail in thorough mode | Pause pipeline. Inform user. |
| findings-evaluator returns OVERTURNED | Route to report-compiler as null result |
| Iteration count reaches max (3) without score >= 6 | Terminate with null result |

Hard stops require user decision before proceeding.

---

## Degraded output propagation

When `degraded_output: true` is set on any phase, every downstream phase inherits the flag. The report-compiler surfaces all degraded fields in the limitations section.

Example in final report:
> "Data quality: PROCEED_WITH_CAVEATS — survivorship bias likely in the 2000-2010 subperiod (pre-2010 delisted tickers absent). Findings from this subperiod are treated as exploratory."

---

## Validation commands

```bash
# Validate single phase
python scripts/validate_output.py --phase data-scout-quality --output_dir ./kras_nsclc/

# Validate full pipeline
python scripts/validate_output.py --all --output_dir ./kras_nsclc/

# Summary report
python scripts/validate_output.py --all --output_dir ./kras_nsclc/ --report
```
