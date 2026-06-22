# Open Targets enrichment coverage (v2 leg 1)

- Drug-name resolved to a ChEMBL molecule: **31/34** (91%).
- Modality auto-match vs hand tag (of resolved): 25/31.

Unresolved (the name-join coverage leak, the binding constraint):

- KarXT (karxt-2022)
- AXS-05 (axs05-2022)
- VK2735 (vk2735-2024)

Resolved, hand vs Open Targets (for inspection):

| Drug | hand MOA | OT MOA | hand target | OT target | hand mod | OT mod |
|---|---|---|---|---|---|---|
| aducanumab | anti-amyloid mAb | Amyloid-beta A4 protein binding agent | amyloid-beta | APP | mab | mab |
| lecanemab | anti-amyloid mAb | Amyloid-beta A4 protein inhibitor | amyloid-beta | APP | mab | mab |
| donanemab | anti-amyloid mAb | Amyloid-beta A4 protein disrupting agent | amyloid-beta | APP | mab | mab |
| gantenerumab | anti-amyloid mAb | Amyloid-beta A4 protein binding agent | amyloid-beta | APP | mab | mab |
| solanezumab | anti-amyloid mAb | Amyloid-beta A4 protein binding agent | amyloid-beta | APP | mab | mab |
| crenezumab | anti-amyloid mAb | Amyloid-beta A4 protein inhibitor | amyloid-beta | APP | mab | mab |
| bapineuzumab | anti-amyloid mAb | Amyloid-beta A4 protein binding agent | amyloid-beta | APP | mab | mab |
| zuranolone | gaba-a positive modulator | GABA-A receptor; anion channel positive allosteric modulator | GABRA | GABRA1 | small_molecule | small_molecule |
| pimavanserin | 5-ht2a inverse agonist | Serotonin 2a (5-HT2a) receptor inverse agonist | HTR2A | HTR2A | small_molecule | small_molecule |
| lumateperone | d2/5-ht2a modulator | Serotonin transporter inhibitor | DRD2/HTR2A | SLC6A4 | small_molecule | small_molecule |
| eteplirsen | exon-skipping antisense | Dystrophin pre-mRNA positive modulator | dystrophin | DMD | antisense | antisense |
| golodirsen | exon-skipping antisense | Dystrophin pre-mRNA positive modulator | dystrophin | DMD | antisense | antisense |
| casimersen | exon-skipping antisense | Dystrophin pre-mRNA positive modulator | dystrophin | DMD | antisense | antisense |
| SRP-9001 | aav gene therapy | Dystrophin exogenous gene | microdystrophin | DMD | gene_therapy | gene |
| valoctocogene roxaparvovec | aav gene therapy | Coagulation factor IX exogenous protein | factor-viii | F9 | gene_therapy | gene |
| etranacogene dezaparvovec | aav gene therapy | Coagulation factor IX exogenous protein | factor-ix | F9 | gene_therapy | gene |
| onasemnogene abeparvovec | aav gene therapy | Survival motor neuron protein exogenous gene | SMN1 | SMN2 | gene_therapy | gene |
| exagamglogene autotemcel | crispr gene editing | B-cell lymphoma/leukemia 11A gene editing negative modulator | BCL11A | BCL11A | gene_editing | gene |
| betibeglogene autotemcel | lentiviral gene therapy | Hemoglobin beta chain exogenous gene | beta-globin | HBB | gene_therapy | gene |
| tirzepatide | gip/glp-1 dual agonist | Glucagon-like peptide 1 receptor agonist | GIPR/GLP1R | GLP1R | peptide | peptide |
| semaglutide | glp-1 agonist | Glucagon-like peptide 1 receptor agonist | GLP1R | GLP1R | peptide | peptide |
| retatrutide | gip/glp-1/glucagon triple | Gastric inhibitory polypeptide receptor agonist | GIPR/GLP1R/GCGR | GIPR | peptide | peptide |
| orforglipron | oral glp-1 agonist |  | GLP1R |  | small_molecule | small_molecule |
| CagriSema | glp-1/amylin coagonist | Glucagon-like peptide 1 receptor agonist | GLP1R/amylin | GLP1R | peptide | peptide |
| resmetirom | thr-beta agonist | Thyroid hormone receptor beta-1 agonist | THRB | THRB | small_molecule | small_molecule |
| efruxifermin | fgf21 analog |  | FGF21 |  | peptide | peptide |
| pegozafermin | fgf21 analog |  | FGF21 |  | peptide | peptide |
| obeticholic acid | fxr agonist | Bile acid receptor FXR agonist | NR1H4 | NR1H4 | small_molecule | small_molecule |
| bempedoic acid | acl inhibitor | ATP-citrate synthase inhibitor | ACLY | ACLY | small_molecule | small_molecule |
| sotorasib | kras g12c inhibitor | GTPase KRas inhibitor | KRAS | KRAS | small_molecule | small_molecule |
| adagrasib | kras g12c inhibitor | GTPase KRas inhibitor | KRAS | KRAS | small_molecule | small_molecule |
