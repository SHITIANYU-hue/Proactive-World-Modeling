from __future__ import annotations

from piwm_train import config


def test_all_tag_literals_are_lowercase_and_closed() -> None:
    for group in (
        config.PERCEPTION_TAGS,
        config.DELIBERATION_TAGS,
        config.CONTINUATION_TAGS,
        config.FUTURE_VERIFICATION_TAGS,
        config.ACTION_TAGS,
    ):
        for tag in group:
            assert tag.open == tag.open.lower()
            assert tag.close == tag.close.lower()
            assert tag.open.startswith("<")
            assert tag.open.endswith(">")
            assert tag.close.startswith("</")
            assert tag.close.endswith(">")
            assert tag.open[1:-1] == tag.close[2:-1]


def test_tag_instruction_lines_uses_pairs_in_order() -> None:
    lines = config.tag_instruction_lines(config.PERCEPTION_TAGS).splitlines()
    assert lines[0] == f"{config.TAG_STAGE_OPEN}...{config.TAG_STAGE_CLOSE}"
    assert lines[-1] == f"{config.TAG_INTERVENTION_UTTERANCE_OPEN}...{config.TAG_INTERVENTION_UTTERANCE_CLOSE}"


def test_model_constants_match_sprint_scope() -> None:
    assert config.MODEL_NAME == "Qwen/Qwen3-VL-8B-Instruct"
    assert config.FALLBACK_MODEL_NAME == "Qwen/Qwen2.5-VL-7B-Instruct"
    assert config.LORA_TARGET_MODULES == ["q_proj", "k_proj", "v_proj", "o_proj"]
    assert config.REWARD_FORMAT.format(0.7341) == "0.73"
