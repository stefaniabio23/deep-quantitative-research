# Drug -> NCT auto-resolver validation

Run on the 9 curated-NCT catalysts (ground truth).

- **Outcome agreement** (resolver+labeler vs hand): **5/9**.
- Exact pivotal-NCT recovery: 4/9 (strict; multiple valid trials exist per drug).

| Drug | curated NCT | resolved NCT | auto | hand | outcome match |
|---|---|---|---|---|---|
| aducanumab | NCT02484547 | NCT02477800 | failure | success | False |
| lecanemab | NCT03887455 | NCT01767311 | unlabeled | success | False |
| donanemab | NCT04437511 | NCT04437511 | success | success | True |
| gantenerumab | NCT03443973 | NCT03444870 | failure | failure | True |
| KarXT | NCT04659161 | NCT04738123 | unlabeled | success | False |
| zuranolone | NCT03672175 | NCT03672175 | failure | failure | True |
| AXS-05 | NCT04019704 | NCT04634669 | failure | success | False |
| obeticholic acid | NCT02548351 | NCT02548351 | failure | failure | True |
| sotorasib | NCT04303780 | NCT04303780 | success | success | True |
