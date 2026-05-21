from __future__ import annotations

from piwm_train.a3plus_metrics import intent_a3plus_metrics


def test_intent_a3plus_metrics_split_core_and_low_confidence_labels() -> None:
    pairs = [
        ("confirm_choice", "confirm_choice"),
        ("explore_options", "request_demonstration"),
        ("explore_options", "explore_options"),
        ("explore_options", "seek_reassurance"),
        ("confirm_choice", "negotiate_price"),
    ]

    metrics = intent_a3plus_metrics(pairs)

    assert metrics["intent_core_5class_n"] == 3
    assert metrics["intent_core_5class_macro_f1"] is not None
    assert metrics["intent_core_5class_accuracy"] == 2 / 3
    assert metrics["intent_low_confidence_seek_reassurance_sample_count"] == 1
    assert metrics["intent_low_confidence_negotiate_price_sample_count"] == 1
    assert "visually unidentifiable" in str(metrics["intent_low_confidence_seek_reassurance_note"])
    assert "visually unidentifiable" in str(metrics["intent_low_confidence_negotiate_price_note"])
