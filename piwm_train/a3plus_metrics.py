"""A3+ metric helpers for visually underdetermined intent labels."""

from __future__ import annotations

from . import config


def intent_a3plus_metrics(pairs: list[tuple[str, str]]) -> dict[str, float | int | str | None]:
    """Return primary core-intent metrics plus weak-label diagnostics.

    ``pairs`` are ``(pred_label, gold_label)`` tuples. The primary A3+ metric
    excludes labels that the taxonomy audit marked as weakly supervised under
    the current visual-only Stage-1 contract, while still reporting those
    labels separately for auditability.
    """
    weak_labels = set(config.LOW_CONFIDENCE_INTENT_LABELS)
    core_labels = sorted({gold for _, gold in pairs} - weak_labels)
    core_pairs = [(pred, gold) for pred, gold in pairs if gold in core_labels]
    metrics: dict[str, float | int | str | None] = {
        "intent_core_5class_n": len(core_pairs),
        "intent_core_5class_macro_f1": _macro_f1_for_labels(core_pairs, core_labels),
        "intent_core_5class_accuracy": _accuracy(core_pairs),
        "intent_low_confidence_labels": ",".join(config.LOW_CONFIDENCE_INTENT_LABELS),
    }
    for label in config.LOW_CONFIDENCE_INTENT_LABELS:
        stats = _per_label_stats(pairs, label)
        prefix = f"intent_low_confidence_{label}"
        metrics[f"{prefix}_sample_count"] = stats["support"]
        metrics[f"{prefix}_pred_count"] = stats["pred_count"]
        metrics[f"{prefix}_f1"] = stats["f1"]
        metrics[f"{prefix}_note"] = "visually unidentifiable under the current visual-only Stage-1 contract"
    return metrics


def _accuracy(pairs: list[tuple[str, str]]) -> float | None:
    if not pairs:
        return None
    return sum(int(pred == gold) for pred, gold in pairs) / len(pairs)


def _macro_f1_for_labels(pairs: list[tuple[str, str]], labels: list[str]) -> float | None:
    if not labels:
        return None
    f1s = [_per_label_stats(pairs, label)["f1"] for label in labels]
    return sum(f1s) / len(f1s)


def _per_label_stats(pairs: list[tuple[str, str]], label: str) -> dict[str, float | int]:
    tp = sum(1 for pred, gold in pairs if pred == label and gold == label)
    fp = sum(1 for pred, gold in pairs if pred == label and gold != label)
    fn = sum(1 for pred, gold in pairs if pred != label and gold == label)
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
    return {
        "support": sum(1 for _, gold in pairs if gold == label),
        "pred_count": sum(1 for pred, _ in pairs if pred == label),
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }
