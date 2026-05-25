# Paper Polish Batch 1 Changelog

Date: 2026-05-26

## Scope

- Updated the Overleaf main file `acl_latex.tex` in Sections 5 and 6.
- Kept Abstract unchanged except for no edits by design, and did not edit Method, Related Work, or Conclusion prose beyond the requested limitations paragraph already located in the experiment discussion.
- Used `reports/2026-05-24_paper_writing_materials.md`, `reports/2026-05-26_dataset_statistics.md`, and existing evaluation artifacts as data sources.

## Section Changes

- Added Section 5.4, `Dataset Statistics`, with a five-panel dataset statistics table.
- Replaced the Section 6.3 main results table with the scenario-transfer table.
- Added scenario-level Figure 5 after the main results discussion.
- Updated Section 6.4 action-level analysis and added the per-class radar and PIWM confusion matrix figures.
- Replaced the old combined ablation table with five independent ablation tables in Sections 6.5.1-6.5.5.
- Added the counterfactual-planning distribution figure to Section 6.5.3.
- Added the E2E error-propagation funnel figure to Section 6.5.5.
- Renumbered the sim-to-real pilot table as Table 9 and updated model/scenario naming.

## Naming Updates

- `Stage-1 only` and related variants are now `State-Outcome Model`.
- `Qwen2.5-VL-7B zero-shot` and related variants are now `Qwen2.5-VL-7B (zero-shot)`.
- `Small action-selection training` is now `Small-Scale Action Training`.
- `Random baseline` is now `Random Baseline`.
- `Always-one-action baselines` is now `Constant-Action Baselines`.
- Scenario names were normalized to `Target-Test (n=30)`, `Cross-Domain (n=60)`, `Target-Test E2E (n=30)`, and `Real-Store Pilot (n=20)`.
- The Abstract still contains the original reader-facing phrase `30 held-out target videos`, per task instruction.

## Tables

- Table 3: Main scenario-transfer results.
- Table 4: Training Data Composition.
- Table 5: Candidate Filtering Strategy.
- Table 6: Inference-Time Counterfactual Planning, including the added `State-Outcome Model + CF Planning (model-reward) = 0.418` row.
- Table 7: Pipeline Diagnostics on Cross-Domain (n=60).
- Table 8: Oracle State vs. End-to-End.
- Table 9: Sim-to-Real Pilot Evaluation.
- Table 10: Dataset Statistics.

Implementation note: Table 10 is placed in Section 5.4 while preserving the requested numbering order for Tables 3-10. The Overleaf source uses a local LaTeX table counter adjustment around Table 10 to make the displayed number match the requested manuscript numbering.

## Figures

Generated local figure artifacts:

- `reports/figures_batch1/V1_confusion_matrix.{pdf,png,py}`
- `reports/figures_batch1/V2_cross_scenario_bar.{pdf,png,py}`
- `reports/figures_batch1/V3_error_propagation_funnel.{pdf,png,py}`
- `reports/figures_batch1/V4_per_class_radar.{pdf,png,py}`
- `reports/figures_batch1/V5_trick6_mode_collapse.{pdf,png,py}`

Overleaf uploads:

- Uploaded `V1_confusion_matrix.pdf`.
- Uploaded `V2_cross_scenario_bar.pdf`.
- Uploaded `V3_error_propagation_funnel.pdf`.
- Uploaded `V4_per_class_radar.pdf`.
- Uploaded `V5_trick6_mode_collapse.pdf`.

Figure data note:

- V5 uses the latest 2026-05-25 stage-reward rerun tied to the `0.171` Table 6 result: `Greet=2`, `Elicit=11`, `Inform=9`, `Recommend=7`, `Hold=1`.
- The requested parenthetical distribution included `Hold=24` together with later counts that sum to more than 30. That `Hold=24` distribution belongs to an older raw artifact with a different score, so it was not plotted as the current Table 6 figure.

## Validation

- Overleaf compilation completed and produced an 11-page PDF after adding the new tables and figures.
- All Figure 4-8 insertions have `\label{}` and are referenced in body text.
- All Tables 3-10 have `\label{}` and are referenced in body text.
- Local file check confirmed all five figures have PDF, PNG, and Python source files.
- Naming grep found only the Abstract's original `30 held-out target videos` wording, intentionally preserved per instruction.

## Local Source Snapshot

- Local edit snapshot before Overleaf paste: `tmp/overleaf_edit/acl_latex_before.tex`
- Local edit snapshot after Overleaf paste: `tmp/overleaf_edit/acl_latex_after.tex`

