from __future__ import annotations

import json
from pathlib import Path

import pytest

from piwm_train import config
from piwm_train.data_collator import (
    SFTExample,
    batch_examples,
    build_dpo_examples,
    build_sft_examples,
    write_dpo_jsonl,
    write_sft_jsonl,
)
from piwm_train.ms_swift_adapter import build_ms_swift_record


ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data/piwm_dataset_pilot30"
DATA_DIR_WITH_CONTINUATIONS = ROOT / "data/piwm_dataset_pilot30_with_continuations_compact_v2"


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _policy_row(state_id: str, action: str, act: str) -> dict:
    return {
        "state_id": state_id,
        "chosen_json": {
            "action": action,
            "rationale": f"{act} is the preferred action.",
            "action_spec": {"act": act, "params": {"mode": "silent"} if act == "Hold" else {"content_type": "comparison"}},
            "intervention_plan": {"physical_action": "terminal action", "utterance": "response"},
        },
        "rejected_json": {
            "action": "Greet_4f8123f9f15e",
            "rationale": "Greeting is less aligned.",
            "action_spec": {"act": "Greet", "params": {"phase": "open"}},
            "intervention_plan": {"physical_action": "greet", "utterance": "hello"},
        },
        "meta": {
            "frames": ["frame.jpg"],
            "state_summary": {
                "aida_stage": "interest",
                "intent": "compare_value_for_money",
                "visual_state": {
                    "summary": "customer compares",
                    "engagement_pattern": "",
                    "gaze_and_attention": "",
                    "body_and_hands": "",
                },
                "bdi": {"belief": "options differ", "desire": "compare", "intention": "keep comparing"},
            },
            "candidate_block": [
                {"action": action, "action_spec": {"act": act, "params": {"mode": "silent"} if act == "Hold" else {"content_type": "comparison"}}},
                {"action": "Greet_4f8123f9f15e", "action_spec": {"act": "Greet", "params": {"phase": "open"}}},
            ],
        },
    }


def _state_row(state_id: str, intent: str) -> dict:
    return {
        "state_id": state_id,
        "input": {"frames": ["frame.jpg"]},
        "output": {
            "aida_stage": "interest",
            "intent": intent,
            "visual_state": {
                "summary": "customer compares products",
                "engagement_pattern": "slowed browsing",
                "gaze_and_attention": "looking at the display",
                "body_and_hands": "standing close to the shelf",
            },
            "bdi": {
                "belief": "options differ",
                "desire": "compare alternatives",
                "intention": "continue evaluating",
            },
            "proactive_score": 3,
            "candidate_actions": ["Inform_abc"],
        },
        "meta": {"split": "train", "viewpoint": "salesperson_observable"},
    }


def test_build_sft_examples_from_pilot30_without_continuation() -> None:
    examples = build_sft_examples(DATA_DIR, include_continuation=True)
    task_counts = {task: sum(1 for example in examples if example.task == task) for task in ["perception", "deliberation", "continuation_caption"]}
    assert task_counts["perception"] == 24
    assert task_counts["deliberation"] == 66
    assert task_counts["continuation_caption"] == 0
    assert all(isinstance(example, SFTExample) for example in examples)


def test_build_sft_examples_from_pilot30_with_continuations() -> None:
    examples = build_sft_examples(DATA_DIR_WITH_CONTINUATIONS, include_continuation=True)
    task_counts = {
        task: sum(1 for example in examples if example.task == task)
        for task in ["perception", "deliberation", "continuation_caption", "future_verification"]
    }
    assert task_counts == {
        "perception": 24,
        "deliberation": 66,
        "continuation_caption": 44,
        "future_verification": 84,
    }
    first_continuation = next(example for example in examples if example.task == "continuation_caption")
    assert first_continuation.images
    assert first_continuation.meta["continuation_frames"]
    first_verification = next(example for example in examples if example.task == "future_verification")
    assert len(first_verification.images) == 6
    assert first_verification.meta["is_positive_pair"] in {True, False}


def test_build_sft_examples_can_include_action_selection() -> None:
    examples = build_sft_examples(DATA_DIR, include_action=True)
    task_counts = {
        task: sum(1 for example in examples if example.task == task)
        for task in ["perception", "deliberation", "action_selection"]
    }
    assert task_counts == {
        "perception": 24,
        "deliberation": 66,
        "action_selection": 24,
    }
    action = next(example for example in examples if example.task == "action_selection")
    assert config.TAG_CHOSEN_OPEN in action.target
    assert config.TAG_RATIONALE_OPEN in action.target
    assert action.images


def test_build_sft_examples_can_include_leakage_free_user_intent() -> None:
    examples = build_sft_examples(
        DATA_DIR,
        include_user_intent=True,
        include_perception=False,
        include_deliberation=False,
        include_continuation=False,
    )
    assert {example.task for example in examples} == {"user_intent"}
    first = examples[0]
    assert config.TAG_INTENT_LABEL_OPEN in first.target
    assert config.TAG_CANDS_OPEN not in first.target
    assert "Do not choose a sales action" in first.prompt


def test_a3plus_user_intent_low_confidence_labels_get_loss_weight(tmp_path: Path) -> None:
    _write_jsonl(
        tmp_path / "state_inference.jsonl",
        [
            _state_row("seek_1", "seek_reassurance"),
            _state_row("price_1", "negotiate_price"),
            _state_row("confirm_1", "confirm_choice"),
        ],
    )

    examples = build_sft_examples(
        tmp_path,
        include_user_intent=True,
        include_perception=False,
        include_deliberation=False,
        include_continuation=False,
    )

    by_id = {example.source_id: example for example in examples}
    assert by_id["seek_1"].weight == 0.1
    assert by_id["price_1"].weight == 0.1
    assert by_id["confirm_1"].weight == 1.0
    assert by_id["seek_1"].meta["loss_weight"] == 0.1
    assert by_id["price_1"].meta["loss_weight"] == 0.1
    assert by_id["confirm_1"].meta["loss_weight"] == 1.0
    assert by_id["seek_1"].meta["loss_weight_policy"] == "a3plus_visual_intent_low_confidence"

    swift_row = build_ms_swift_record(by_id["seek_1"], root=tmp_path, validate_images=False)
    assert swift_row["weight"] == 0.1
    assert swift_row["loss_weight"] == 0.1
    assert swift_row["meta"]["intent_label"] == "seek_reassurance"


def test_build_sft_examples_can_use_no_leak_action_prompt(tmp_path: Path) -> None:
    _write_jsonl(
        tmp_path / "policy_preference.jsonl",
        [
            {
                "state_id": "target_keep",
                "chosen_json": {
                    "action": "Inform_5ac252a82695",
                    "rationale": "Inform fits comparison.",
                    "action_spec": {"act": "Inform", "params": {"content_type": "comparison"}},
                    "intervention_plan": {"physical_action": "show comparison", "utterance": "Here is the comparison."},
                },
                "rejected_json": {
                    "action": "Hold_eda24b4bb712",
                    "rationale": "Hold is less aligned.",
                    "action_spec": {"act": "Hold", "params": {"mode": "silent"}},
                    "intervention_plan": {"physical_action": "stay silent", "utterance": "（静默）"},
                },
                "meta": {
                    "frames": ["frame.jpg"],
                    "state_summary": {
                        "aida_stage": "interest",
                        "intent": "compare_value_for_money",
                        "visual_state": {"summary": "customer compares", "engagement_pattern": "", "gaze_and_attention": "", "body_and_hands": ""},
                        "bdi": {"belief": "options differ", "desire": "compare", "intention": "keep comparing"},
                    },
                    "candidate_block": [
                        {"action": "Inform_5ac252a82695", "action_spec": {"act": "Inform", "params": {"content_type": "comparison"}}},
                        {"action": "Hold_eda24b4bb712", "action_spec": {"act": "Hold", "params": {"mode": "silent"}}},
                    ],
                },
            }
        ],
    )
    examples = build_sft_examples(
        tmp_path,
        include_perception=False,
        include_deliberation=False,
        include_continuation=False,
        include_action=True,
        action_prompt_mode="no_leak",
        five_act_only=True,
    )
    action = examples[0]
    assert action.task == "action_selection_5act"
    assert "predicted_next_stage=" not in action.prompt
    assert "reward=" not in action.prompt
    assert action.meta["candidate_action_acts"]


def test_five_act_action_selection_drops_reassure_best_rows_and_filters_reassure_candidates(tmp_path: Path) -> None:
    policy_rows = [
        {
            "state_id": "target_keep",
            "chosen_json": {
                "action": "Greet_4f8123f9f15e",
                "rationale": "Greet is inside the 5-act policy path.",
                "action_spec": {"act": "Greet", "params": {"phase": "open"}},
                "intervention_plan": {"physical_action": "show greeting", "utterance": "Hello."},
            },
            "rejected_json": {
                "action": "Reassure_dbe6016c33c1",
                "rationale": "Reassure is outside the 5-act policy path.",
                "action_spec": {"act": "Reassure", "params": {"focus": "time"}},
                "intervention_plan": {"physical_action": "soft reassurance", "utterance": "Take your time."},
            },
            "meta": {
                "frames": ["frame.jpg"],
                "state_summary": {
                    "aida_stage": "interest",
                    "intent": "compare_value_for_money",
                    "visual_state": {"summary": "customer compares", "engagement_pattern": "", "gaze_and_attention": "", "body_and_hands": ""},
                    "bdi": {"belief": "options differ", "desire": "compare", "intention": "keep comparing"},
                },
                "candidate_block": [
                    {"action": "Reassure_dbe6016c33c1", "action_spec": {"act": "Reassure", "params": {"focus": "time"}}},
                    {"action": "Greet_4f8123f9f15e", "action_spec": {"act": "Greet", "params": {"phase": "open"}}},
                    {"action": "Hold_eda24b4bb712", "action_spec": {"act": "Hold", "params": {"mode": "silent"}}},
                ],
            },
        },
        {
            "state_id": "target_drop",
            "chosen_json": {
                "action": "Reassure_dbe6016c33c1",
                "rationale": "Reassure is excluded from the main 5-act path.",
                "action_spec": {"act": "Reassure", "params": {"focus": "time"}},
                "intervention_plan": {"physical_action": "soft reassurance", "utterance": "Take your time."},
            },
            "rejected_json": {
                "action": "Hold_eda24b4bb712",
                "rationale": "Hold is less aligned.",
                "action_spec": {"act": "Hold", "params": {"mode": "silent"}},
                "intervention_plan": {"physical_action": "stay silent", "utterance": "（静默）"},
            },
            "meta": {
                "frames": ["frame.jpg"],
                "state_summary": {
                    "aida_stage": "action",
                    "intent": "close_interaction",
                    "visual_state": {"summary": "customer leaving", "engagement_pattern": "", "gaze_and_attention": "", "body_and_hands": ""},
                    "bdi": {"belief": "done", "desire": "leave", "intention": "exit"},
                },
                "candidate_block": [
                    {"action": "Reassure_dbe6016c33c1", "action_spec": {"act": "Reassure", "params": {"focus": "time"}}},
                    {"action": "Hold_eda24b4bb712", "action_spec": {"act": "Hold", "params": {"mode": "silent"}}},
                ],
            },
        },
    ]
    _write_jsonl(tmp_path / "policy_preference.jsonl", policy_rows)

    examples = build_sft_examples(
        tmp_path,
        include_perception=False,
        include_deliberation=False,
        include_continuation=False,
        include_action=True,
        action_prompt_mode="no_leak",
        five_act_only=True,
    )

    assert [example.source_id for example in examples] == ["target_keep"]
    assert "Reassure_" not in examples[0].prompt
    assert "Reassure_" not in examples[0].target
    assert "Greet_" in examples[0].target
    assert set(examples[0].meta["candidate_action_acts"].values()) <= {"Greet", "Elicit", "Inform", "Recommend", "Hold"}


def test_action_balancing_inverse_freq_sets_minority_weight(tmp_path: Path) -> None:
    _write_jsonl(
        tmp_path / "policy_preference.jsonl",
        [
            _policy_row("inform_1", "Inform_5ac252a82695", "Inform"),
            _policy_row("inform_2", "Inform_5ac252a82695", "Inform"),
            _policy_row("hold_1", "Hold_eda24b4bb712", "Hold"),
        ],
    )

    examples = build_sft_examples(
        tmp_path,
        include_perception=False,
        include_deliberation=False,
        include_continuation=False,
        include_action=True,
        action_prompt_mode="no_leak",
        five_act_only=True,
        act_balancing="inverse_freq",
    )

    weights = {example.source_id: example.weight for example in examples}
    assert weights["hold_1"] > weights["inform_1"]
    assert all(example.meta["act_balancing"] == "inverse_freq" for example in examples)


def test_action_balancing_oversamples_minority_to_half_majority(tmp_path: Path) -> None:
    _write_jsonl(
        tmp_path / "policy_preference.jsonl",
        [
            _policy_row("inform_1", "Inform_5ac252a82695", "Inform"),
            _policy_row("inform_2", "Inform_5ac252a82695", "Inform"),
            _policy_row("inform_3", "Inform_5ac252a82695", "Inform"),
            _policy_row("inform_4", "Inform_5ac252a82695", "Inform"),
            _policy_row("hold_1", "Hold_eda24b4bb712", "Hold"),
        ],
    )

    examples = build_sft_examples(
        tmp_path,
        include_perception=False,
        include_deliberation=False,
        include_continuation=False,
        include_action=True,
        action_prompt_mode="no_leak",
        five_act_only=True,
        act_balancing="oversample_minority",
    )

    source_ids = [example.source_id for example in examples]
    assert source_ids.count("hold_1") == 2
    assert len(examples) == 6
    assert any(example.meta.get("oversampled") for example in examples if example.source_id == "hold_1")


def test_build_sft_examples_can_disable_deliberation_for_ablation() -> None:
    examples = build_sft_examples(
        DATA_DIR,
        include_deliberation=False,
        include_continuation=False,
        include_action=True,
    )
    assert {example.task for example in examples} == {"perception", "action_selection"}


def test_perception_examples_include_recap_by_default() -> None:
    example = next(example for example in build_sft_examples(DATA_DIR) if example.task == "perception")
    assert "[recap]" in example.target
    assert example.target.count(config.TAG_STAGE_OPEN) == 2
    assert example.target.count(config.TAG_INTENTION_OPEN) == 2


def test_build_dpo_examples_from_pilot30() -> None:
    examples = build_dpo_examples(DATA_DIR)
    assert len(examples) == 24
    first = examples[0]
    assert config.TAG_CHOSEN_OPEN in first.chosen
    assert config.TAG_CHOSEN_OPEN in first.rejected
    assert first.images


def test_batch_examples_requires_positive_batch_size() -> None:
    with pytest.raises(ValueError):
        list(batch_examples([], 0))


def test_batch_examples_chunks() -> None:
    examples = build_dpo_examples(DATA_DIR)[:5]
    batches = list(batch_examples(examples, 2))
    assert [len(batch) for batch in batches] == [2, 2, 1]


def test_write_training_jsonl_roundtrip(tmp_path: Path) -> None:
    sft = build_sft_examples(DATA_DIR)[:2]
    dpo = build_dpo_examples(DATA_DIR)[:2]
    sft_out = tmp_path / "sft.jsonl"
    dpo_out = tmp_path / "dpo.jsonl"
    assert write_sft_jsonl(sft, sft_out) == 2
    assert write_dpo_jsonl(dpo, dpo_out) == 2
    first_sft = json.loads(sft_out.read_text(encoding="utf-8").splitlines()[0])
    first_dpo = json.loads(dpo_out.read_text(encoding="utf-8").splitlines()[0])
    assert first_sft["prompt"]
    assert first_sft["target"]
    assert first_dpo["chosen"]
    assert first_dpo["rejected"]
