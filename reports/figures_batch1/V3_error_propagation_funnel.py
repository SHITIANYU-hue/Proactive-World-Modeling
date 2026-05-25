from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports" / "figures_batch1"

STEPS = [
    ("Target-Test samples", 30.0),
    ("Step 1 parse success", 24.0),
    ("Step 1 stage correct", 18.0),
    ("Best-action correct\nwithin stage-correct subset", 9.6),
]


def main():
    labels = [x[0] for x in STEPS]
    values = [x[1] for x in STEPS]
    colors = ["#1d4ed8", "#3b82f6", "#93c5fd", "#bfdbfe"]

    fig, ax = plt.subplots(figsize=(7.2, 4.4))
    y = range(len(labels))
    bars = ax.barh(y, values, color=colors, edgecolor="#1f2937", linewidth=0.5)
    ax.invert_yaxis()
    ax.set_yticks(y, labels)
    ax.set_xlim(0, 32)
    ax.set_xlabel("Samples")
    ax.set_title("End-to-End Error Propagation on Target-Test (n=30)")
    ax.grid(axis="x", alpha=0.22)

    total = values[0]
    prev = None
    for bar, val in zip(bars, values):
        pct_total = 100 * val / total
        if prev is None:
            text = f"{val:g} ({pct_total:.1f}% of total)"
        else:
            text = f"{val:g} ({100 * val / prev:.1f}% of previous; {pct_total:.1f}% total)"
        ax.text(val + 0.5, bar.get_y() + bar.get_height() / 2, text, va="center", fontsize=9)
        prev = val

    fig.tight_layout()
    fig.savefig(OUT / "V3_error_propagation_funnel.pdf", bbox_inches="tight")
    fig.savefig(OUT / "V3_error_propagation_funnel.png", dpi=220, bbox_inches="tight")


if __name__ == "__main__":
    main()
