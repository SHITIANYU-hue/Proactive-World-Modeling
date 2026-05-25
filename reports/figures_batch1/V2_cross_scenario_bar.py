from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports" / "figures_batch1"

SCENARIOS = ["Target-Test", "Cross-Domain", "E2E", "Real-Store"]
MODELS = {
    "PIWM": [0.641, 0.734, 0.295, 0.579],
    "State-Outcome Model": [0.240, 0.259, np.nan, 0.217],
    "Qwen2.5-VL-7B (zero-shot)": [0.313, 0.142, np.nan, 0.111],
}
COLORS = {
    "PIWM": "#1d4ed8",
    "State-Outcome Model": "#9ca3af",
    "Qwen2.5-VL-7B (zero-shot)": "#d1d5db",
}


def main():
    x = np.arange(len(SCENARIOS))
    width = 0.24
    fig, ax = plt.subplots(figsize=(8.0, 4.8))

    offsets = [-width, 0, width]
    for offset, (model, values) in zip(offsets, MODELS.items()):
        vals = np.array(values, dtype=float)
        bars = ax.bar(x + offset, np.nan_to_num(vals, nan=0.0), width, label=model, color=COLORS[model], edgecolor="#374151", linewidth=0.4)
        for bar, val in zip(bars, vals):
            if np.isnan(val):
                bar.set_alpha(0.18)
                ax.text(bar.get_x() + bar.get_width() / 2, 0.025, "N/A", ha="center", va="bottom", fontsize=8, color="#4b5563", rotation=90)
            else:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.015, f"{val:.3f}", ha="center", va="bottom", fontsize=8)

    ax.axhline(0.414, color="#111827", linestyle="--", linewidth=1.1, label="Random Baseline (0.414)")
    ax.set_xticks(x, SCENARIOS)
    ax.set_ylim(0, 0.82)
    ax.set_ylabel("Macro F1")
    ax.set_title("Best-Action Selection Across Evaluation Scenarios")
    ax.grid(axis="y", alpha=0.22)
    ax.legend(loc="upper right", fontsize=8, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "V2_cross_scenario_bar.pdf", bbox_inches="tight")
    fig.savefig(OUT / "V2_cross_scenario_bar.png", dpi=220, bbox_inches="tight")


if __name__ == "__main__":
    main()
