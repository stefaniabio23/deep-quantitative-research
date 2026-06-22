# Live ticker screen through the reference-class pipeline

Screened 15 tickers. Enrichment is live (Open Targets); the reference class is matched against the 34-catalyst curated corpus.

- **2/15 produced a reference-class base rate.** The rest have no mechanistic analogue in the curated corpus yet, the coverage gap that the v2 scale-out closes.

| Ticker | Drug | MOA (verified) | OT MOA (auto) | Ref class n | Base rate | Confidence | Read |
|---|---|---|---|---:|---:|---|---|
| IMVT | IMVT-1402 | anti-fcrn | (unresolved) |  |  | none | no class in corpus yet |
| ROIV | brepocitinib | tyk2/jak1 inhibitor | Tyrosine-protein kinase TYK2 inhibitor |  |  | none | no class in corpus yet |
| PALI | PL7737 | melanocortin-4 agonist | (unresolved) | 6 | 83% | medium | analogues: orforglipron, tirzepatide, semaglutide |
| SEPN | SEP-786 | pth1r agonist | (unresolved) |  |  | none | no class in corpus yet |
| PTGX | rusfertide | hepcidin mimetic |  |  |  | none | no class in corpus yet |
| ESTA | Motiva | medical device | (not a drug) |  |  | out-of-scope | device, out of scope |
| ABVX | obefazimod | mir-124 enhancer | Cap binding complex modulator |  |  | none | no class in corpus yet |
| EQ | itolizumab | anti-cd6 mab | T-cell differentiation antigen CD6 inhibitor |  |  | none | no class in corpus yet |
| IKT | IKT-001 | tyrosine kinase inhibitor |  |  |  | none | no class in corpus yet |
| ZLAB | zocilurtatug pelitecan | dll3 adc | (unresolved) |  |  | none | no class in corpus yet |
| ZURA | tibulizumab | anti-il17a/baff bispecific | Interleukin 17A inhibitor |  |  | none | no class in corpus yet |
| QURE | AMT-130 | aav gene therapy | (unresolved) | 4 | 75% | low | analogues: SRP-9001, valoctocogene roxaparvovec, etranacogene dezaparvovec |
| JANX | JANX007 | psma t-cell engager | (unresolved) |  |  | none | no class in corpus yet |
| CYTK | aficamten | cardiac myosin inhibitor |  |  |  | none | no class in corpus yet |
| MNPR | ALXN1840 | copper modulator |  |  |  | none | no class in corpus yet |

## Theses (where a reference class exists)

- **PALI (PL7737, obesity)**: reference class of 6 (medium confidence), base rate 83% success. Closest analogues: orforglipron, tirzepatide, semaglutide. Caveat: matched on indication, verify the class is mechanistically apt before relying on it.
- **QURE (AMT-130, huntingtons)**: reference class of 4 (low confidence), base rate 75% success. Closest analogues: SRP-9001, valoctocogene roxaparvovec, etranacogene dezaparvovec. Caveat: matched on MOA/modality, verify the class is mechanistically apt before relying on it.

## Honest limits

- ticker->drug is curated (no free ticker->pipeline source); only the lead asset is screened.
- A 34-catalyst corpus covers few mechanisms, so most live names return no class. This is the expected result and the case for v2 (auto-enrich the full trial universe).
- Indication-only matches (e.g. an obesity drug pulling GLP-1 analogues) can be mechanistically wrong; the read flags the match basis.
