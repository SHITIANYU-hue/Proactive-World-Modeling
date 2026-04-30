from __future__ import annotations

from piwm_train import config


class MockVLM:
    """Deterministic VLM stub keyed by PIWM role strings."""

    def __init__(self, outputs: dict[str, str] | None = None) -> None:
        self.outputs = outputs or default_outputs()
        self.calls: list[dict[str, str | int]] = []

    def generate(self, prompt: str, *, role: str, max_new_tokens: int) -> str:
        self.calls.append({"role": role, "prompt": prompt, "max_new_tokens": max_new_tokens})
        if role in self.outputs:
            return self.outputs[role]
        if role.startswith("deliberation:"):
            action = role.split(":", 1)[1]
            return self.outputs[f"deliberation:{action}"]
        if role.startswith("continuation:"):
            action = role.split(":", 1)[1]
            return self.outputs.get(
                f"continuation:{action}",
                f"{config.TAG_REACTION_CAPTION_OPEN}the customer remains calm{config.TAG_REACTION_CAPTION_CLOSE}",
            )
        raise KeyError(role)


def default_outputs() -> dict[str, str]:
    return {
        "perception": "\n".join(
            [
                f"{config.TAG_STAGE_OPEN}interest{config.TAG_STAGE_CLOSE}",
                f"{config.TAG_BELIEF_OPEN}the customer is comparing options{config.TAG_BELIEF_CLOSE}",
                f"{config.TAG_DESIRE_OPEN}reduce uncertainty{config.TAG_DESIRE_CLOSE}",
                f"{config.TAG_INTENTION_OPEN}continue evaluating{config.TAG_INTENTION_CLOSE}",
                f"{config.TAG_SCORE_OPEN}3{config.TAG_SCORE_CLOSE}",
                f"{config.TAG_CANDS_OPEN}A1_silent_observe, A2_offer_value_comparison{config.TAG_CANDS_CLOSE}",
            ]
        ),
        "deliberation:A1_silent_observe": "\n".join(
            [
                f"{config.TAG_NEXT_STAGE_OPEN}interest{config.TAG_NEXT_STAGE_CLOSE}",
                f"{config.TAG_NEXT_BELIEF_OPEN}the customer remains unsure{config.TAG_NEXT_BELIEF_CLOSE}",
                f"{config.TAG_NEXT_DESIRE_OPEN}keep comparing{config.TAG_NEXT_DESIRE_CLOSE}",
                f"{config.TAG_NEXT_INTENTION_OPEN}stay near the display{config.TAG_NEXT_INTENTION_CLOSE}",
                f"{config.TAG_RISK_OPEN}low{config.TAG_RISK_CLOSE}",
                f"{config.TAG_BENEFIT_OPEN}low{config.TAG_BENEFIT_CLOSE}",
                f"{config.TAG_REWARD_OPEN}0.20{config.TAG_REWARD_CLOSE}",
            ]
        ),
        "deliberation:A2_offer_value_comparison": "\n".join(
            [
                f"{config.TAG_NEXT_STAGE_OPEN}desire{config.TAG_NEXT_STAGE_CLOSE}",
                f"{config.TAG_NEXT_BELIEF_OPEN}the salesperson can clarify value{config.TAG_NEXT_BELIEF_CLOSE}",
                f"{config.TAG_NEXT_DESIRE_OPEN}compare value{config.TAG_NEXT_DESIRE_CLOSE}",
                f"{config.TAG_NEXT_INTENTION_OPEN}engage in dialogue{config.TAG_NEXT_INTENTION_CLOSE}",
                f"{config.TAG_RISK_OPEN}low{config.TAG_RISK_CLOSE}",
                f"{config.TAG_BENEFIT_OPEN}high{config.TAG_BENEFIT_CLOSE}",
                f"{config.TAG_REWARD_OPEN}0.80{config.TAG_REWARD_CLOSE}",
            ]
        ),
        "continuation:A1_silent_observe": (
            f"{config.TAG_REACTION_CAPTION_OPEN}the customer keeps comparing alone"
            f"{config.TAG_REACTION_CAPTION_CLOSE}"
        ),
        "continuation:A2_offer_value_comparison": (
            f"{config.TAG_REACTION_CAPTION_OPEN}the customer turns toward the salesperson"
            f"{config.TAG_REACTION_CAPTION_CLOSE}"
        ),
        "action": "\n".join(
            [
                f"{config.TAG_RATIONALE_OPEN}value comparison gives high benefit with low risk{config.TAG_RATIONALE_CLOSE}",
                f"{config.TAG_CHOSEN_OPEN}A2_offer_value_comparison{config.TAG_CHOSEN_CLOSE}",
            ]
        ),
    }

