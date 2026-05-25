import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports" / "figures_batch1"
RAW = ROOT / "reports" / "rerun_eval_20260525" / "piwm_main_trick6_rewardA_stage_advance.json"
ACTS = ["Greet", "Elicit", "Inform", "Recommend", "Hold"]


def load_counts():
    with RAW.open() as f:
        data = json.load(f)
    pred = {act: int(data["metrics"]["per_act"][act]["pred_count"]) for act in ACTS}
    gold = {act: int(data["metrics"]["per_act"][act]["support"]) for act in ACTS}
    return gold, pred


def main():
    gold, pred = load_counts()
    x = np.arange(len(ACTS))
    width = 0.36

    fig, ax = plt.subplots(figsize=(7.4, 4.6))
    bars_gold = ax.bar(x - width / 2, [gold[a] for a in ACTS], width, label="Gold", color="#bfdbfe", edgecolor="#1f2937", linewidth=0.5)
    bars_pred = ax.bar(x + width / 2, [pred[a] for a in ACTS], width, label="CF Planning (stage-reward)", color="#1d4ed8", edgecolor="#1f2937", linewidth=0.5)

    for bars in (bars_gold, bars_pred):
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.25, f"{int(bar.get_height())}", ha="center", va="bottom", fontsize=9)

    ax.set_xticks(x, ACTS)
    ax.set_ylabel("Count")
    ax.set_ylim(0, 13)
    ax.set_title("Counterfactual Planning Distribution: Predicted vs Gold")
    ax.text(
        0.5,
        -0.22,
        "Latest stage-reward rerun: F1=0.171. Older Hold=24 distribution belongs to a prior F1=0.263 run.",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=8.5,
        color="#374151",
    )
    ax.grid(axis="y", alpha=0.22)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "V5_trick6_mode_collapse.pdf", bbox_inches="tight")
    fig.savefig(OUT / "V5_trick6_mode_collapse.png", dpi=220, bbox_inches="tight")


if __name__ == "__main__":
    main()
