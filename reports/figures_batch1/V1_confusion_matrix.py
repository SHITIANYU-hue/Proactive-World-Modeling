import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports" / "figures_batch1"
RAW = ROOT / "reports" / "closed_model_eval_20260525" / "piwm_main" / "raw_outputs.jsonl"
ACTS = ["Greet", "Elicit", "Inform", "Recommend", "Hold"]


def load_target_rows():
    rows = []
    with RAW.open() as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("domain") == "target":
                rows.append(row)
    return rows


def main():
    rows = load_target_rows()
    matrix = np.zeros((len(ACTS), len(ACTS)), dtype=int)
    parse_fail_by_gold = {act: 0 for act in ACTS}

    for row in rows:
        gold = row["gold_act"]
        if not row.get("parse_ok"):
            parse_fail_by_gold[gold] += 1
            continue
        pred = row.get("pred_act")
        if gold in ACTS and pred in ACTS:
            matrix[ACTS.index(gold), ACTS.index(pred)] += 1

    fig, ax = plt.subplots(figsize=(7.0, 5.8))
    im = ax.imshow(matrix, cmap="Blues", vmin=0, vmax=max(6, matrix.max()))
    ax.set_xticks(range(len(ACTS)), ACTS, rotation=35, ha="right")
    ax.set_yticks(range(len(ACTS)), ACTS)
    ax.set_xlabel("Predicted action")
    ax.set_ylabel("Gold action")
    ax.set_title("PIWM Confusion Matrix on Target-Test (n=30)", pad=14)

    for i in range(len(ACTS)):
        gold_total = sum(1 for row in rows if row["gold_act"] == ACTS[i])
        for j in range(len(ACTS)):
            count = matrix[i, j]
            pct = 100 * count / gold_total if gold_total else 0
            color = "white" if count >= 4 else "#1f2937"
            ax.text(j, i, f"{count}\n{pct:.1f}%", ha="center", va="center", color=color, fontsize=9)

    for i in range(len(ACTS)):
        ax.add_patch(plt.Rectangle((i - 0.5, i - 0.5), 1, 1, fill=False, edgecolor="#0f172a", lw=1.6))

    failures = sum(parse_fail_by_gold.values())
    ax.text(
        0.5,
        -0.20,
        f"{failures} parse failures counted as errors but omitted from 5-class prediction columns.",
        transform=ax.transAxes,
        ha="center",
        va="top",
        fontsize=9,
        color="#374151",
    )
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Count")
    fig.tight_layout()
    fig.savefig(OUT / "V1_confusion_matrix.pdf", bbox_inches="tight")
    fig.savefig(OUT / "V1_confusion_matrix.png", dpi=220, bbox_inches="tight")


if __name__ == "__main__":
    main()
