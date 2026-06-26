# Proactive World Modeling for Goal-Oriented Social Intelligence

This repository contains the code, data tooling, evaluation scripts, and paper
artifacts for **PIWM**: a proactive intent world model for multimodal retail
assistance. PIWM studies a setting where an agent observes short pre-interaction
video clips, infers the customer's latent state, and decides whether and how to
intervene before an explicit request is made.

The project is organized around the **See, Infer, Intervene** pipeline:

1. **See**: sample sparse visual observations from a retail interaction.
2. **Infer**: estimate a structured customer state using AIDA stages and BDI
   fields.
3. **Intervene**: select a best action from a constrained response set, including
   the option to hold and remain silent.

The repository is intended for reproducibility, dataset inspection, and
follow-up experiments. Large dataset artifacts are hosted separately on
Hugging Face.

## Highlights

- **GuidanceSalesBench data pipeline** for synthetic and real-store retail
  guidance scenarios.
- **Structured customer-state schema** based on AIDA purchasing stages and BDI
  fields.
- **Best-action selection evaluation** over five action classes:
  `Greet`, `Elicit`, `Inform`, `Recommend`, and `Hold`.
- **Oracle-state and end-to-end evaluation** scripts for separating action
  selection from upstream video-to-state grounding.
- **Ablation and diagnostic tooling** for frame count, BDI fields, observable
  evidence, candidate filtering, and counterfactual planning.
- **Paper-ready reports and figures** under `reports/`, `figures/`, and `paper/`.

## Repository Layout

```text
piwm_data/      Dataset schemas, rules, validation tests, and export utilities.
piwm_train/     Prompt templates and training-facing helpers.
piwm_infer/     Inference-time parsers and decision-loop utilities.
scripts/        Dataset construction, evaluation, ablation, and sync scripts.
configs/        Experiment and evaluation configuration files.
docs/           Data contracts, runbooks, and project documentation.
data/           Lightweight manifests and small structured artifacts.
reports/        Evaluation outputs, audit notes, and paper-writing materials.
figures/        Generated figures and paper assets.
paper/          Manuscript fragments and submission-related TeX artifacts.
```

Large binary artifacts, full data exports, and real-video files are not meant to
be stored directly in Git history. They are mirrored to the Hugging Face dataset
repository described below.

## Data

The large release bundle is hosted at:

```text
https://huggingface.co/datasets/GameFreshMan/PIWM
```

To download it with the Hugging Face CLI:

```bash
pip install -U huggingface_hub
huggingface-cli download GameFreshMan/PIWM \
  --repo-type dataset \
  --local-dir data/hf/PIWM
```

If the dataset is private or gated, authenticate first:

```bash
huggingface-cli login
```

or set `HF_TOKEN` in the environment before running Hugging Face commands. Do
not commit tokens or credentials to this repository.

The uploaded dataset bundle includes the staged contents used for the current
paper experiments, including official data exports, annotation packs, selected
report artifacts, and real-store video assets.

## Installation

The lightweight Python package targets Python 3.9 or newer.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[test]"
```

For local training and vision-language-model evaluation, install the optional
training dependencies:

```bash
python -m pip install -e ".[train,test]"
```

GPU training and evaluation scripts assume an environment compatible with
Qwen2.5-VL, ModelScope, ms-swift, PyTorch, and the corresponding CUDA stack.
The exact server environment may need to be adapted to local hardware.

## Quick Checks

Run the unit tests:

```bash
pytest
```

Inspect action-balance utilities and parser behavior:

```bash
python scripts/inspect_act_balance.py --help
python scripts/eval_ms_swift_checkpoint.py --help
python scripts/run_end_to_end_best_action_eval.py --help
```

The repository contains many one-off research scripts. Prefer reading the
matching report in `reports/` before re-running an experiment, because the
scripts often encode a specific data snapshot, checkpoint path, or paper-table
protocol.

## Evaluation Entry Points

Common evaluation scripts include:

```text
scripts/eval_ms_swift_checkpoint.py
scripts/piwm_4dim_eval.py
scripts/run_end_to_end_best_action_eval.py
scripts/run_trick6_counterfactual_planning.py
scripts/eval_closed_model.py
scripts/closed_model_best_action_eval.py
scripts/summarize_real_eval_results.py
```

Important report files include:

```text
reports/2026-05-24_paper_writing_materials.md
reports/2026-05-25_rerun_evaluation_main_table.md
reports/2026-05-26_end_to_end_main_result.md
reports/2026-05-26_dataset_statistics.md
reports/2026-05-26_paper_polish_batch2_changelog.md
```

These reports document the main numbers, ablations, dataset statistics, and
manuscript integration steps used in the current paper draft.

## Reported Results Snapshot

The current paper snapshot reports PIWM best-action selection across several
settings:

| Setting | Macro F1 |
|---|---:|
| Target-Test, oracle customer state | 0.641 |
| Cross-Domain, oracle customer state | 0.734 |
| Target-Test, end-to-end video-only state inference | 0.295 |
| Real-Store Pilot, fully annotated subset | 0.579 |

These values are copied from the local paper reports and should be treated as a
snapshot of the current experimental state, not as a package-level benchmark
API. See the corresponding report files for parse rates, per-class breakdowns,
candidate-set details, and error-propagation analysis.

## Hugging Face Sync Utility

Large artifacts were staged locally under `local_artifacts/hf_upload_stage_*`
and uploaded with:

```text
scripts/hf_background_dataset_sync.py
```

The sync script expects `HF_TOKEN` to be set in the environment and uploads only
files missing from the remote dataset repository. It batches remaining files to
avoid excessive one-file commits and respects retry windows when Hugging Face
rate-limits repository commits.

## Reproducibility Notes

- Model checkpoints are not modified by this repository sync.
- Raw large files should go to Hugging Face, not GitHub.
- Parse failures are counted as errors in strict evaluation reports unless a
  report explicitly states otherwise.
- Closed-source model outputs are separated from local PIWM evaluation outputs.
- Some paths in older reports refer to historical A100 or workstation layouts;
  use the current scripts and manifests as the source of truth for new runs.

## Citation

If you use this code or dataset artifacts, cite the associated manuscript once
the public citation is available. Until then, please refer to the project as:

```bibtex
@article{zhang2026see,
  title={See, Infer, Intervene: Proactive World Modeling for Goal-Oriented Social Intelligence},
  author={Zhang, Honghui and Guo, Chenmeinian and Yu, Yichen and Liu, Guanyu and Qin, Yongming and Song, Chongguo and Yang, Mengyue and Yu, Lei and Shi, Tianyu},
  journal={arXiv preprint arXiv:2606.03371},
  year={2026}
}
```

## License and Release Status

This repository is a research release. If a formal license file has not yet been
added, contact the maintainers before using the code or dataset artifacts beyond
review, reproduction, or internal research purposes.
