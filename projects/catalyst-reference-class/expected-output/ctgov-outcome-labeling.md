# CT.gov corpus outcome auto-labeling

- Catalysts with a curated NCT: 9/34.
- Auto-labeled (clean p-value signal): 8/9.
- Auto-outcome matches hand: **7/8**.

Divergent (trial outcome != hand/regulatory outcome, a real distinction):
- aducanumab [NCT02484547]: trial=failure, hand=success

| Drug | NCT | primary p | auto | hand | status |
|---|---|---:|---|---|---|
| aducanumab | NCT02484547 | 0.0901 | failure | success | divergent |
| lecanemab | NCT03887455 | None | unlabeled | success | unlabeled |
| donanemab | NCT04437511 | 0.001 | success | success | match |
| gantenerumab | NCT03443973 | 0.2998 | failure | failure | match |
| KarXT | NCT04659161 | 0.0001 | success | success | match |
| zuranolone | NCT03672175 | 0.6638 | failure | failure | match |
| AXS-05 | NCT04019704 | 0.002 | success | success | match |
| obeticholic acid | NCT02548351 | 0.1028 | failure | failure | match |
| sotorasib | NCT04303780 | 0.002 | success | success | match |
