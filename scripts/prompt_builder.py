"""Build Kling-ready ``prompt.json`` files from sampled PIWM scenarios."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Iterable

from piwm_data import rules

DEFAULT_MANIFEST = Path("data/scenario_manifest.jsonl")
DEFAULT_OUT_ROOT = Path("Archive_prompts")

PRODUCT_SCENES = {
    "luxury_watch": {
        "store": "a quiet watch boutique with a glass display counter",
        "product": "two premium wristwatches on neutral display pads",
    },
    "electronics_phone": {
        "store": "a modern phone retail store with clean demo tables",
        "product": "two smartphones on security tethers near small price tags",
    },
    "electronics_laptop": {
        "store": "a laptop section in an electronics store",
        "product": "two open laptops on a demo table with specification cards",
    },
    "cosmetics_skincare": {
        "store": "a skincare aisle with soft shelf lighting",
        "product": "two skincare bottles beside tester pads and small shelf labels",
    },
    "apparel_premium": {
        "store": "a premium apparel store with a tidy fitting area nearby",
        "product": "two jackets on a rack beside a mirror and discreet price tags",
    },
    "home_appliance": {
        "store": "a home appliance showroom with wide aisles",
        "product": "two compact appliances on a display island with feature cards",
    },
    "jewelry": {
        "store": "a jewelry counter with bright but natural display lighting",
        "product": "two small jewelry pieces in a glass case with discreet tags",
    },
    "footwear": {
        "store": "a footwear store with shoe benches and wall displays",
        "product": "two pairs of shoes on a low display stand near size labels",
    },
}

STAGE_STYLE = {
    "attention": "The shopper has just noticed the display and keeps body movement light and noncommittal.",
    "interest": "The shopper stays near the display and examines details with visible curiosity.",
    "desire": "The shopper moves closer, spends more time with the product, and shows stronger consideration.",
    "action": "The shopper appears close to asking for help or making a concrete next move, but no purchase is completed.",
}

CUE_TIMELINES = {
    "long_dwell_with_price_check": [
        ("0-2s", "The shopper approaches the display and notices the product."),
        ("2-5s", "The shopper leans toward a visible price placard, briefly points near it, then looks back at the product."),
        ("5-8s", "The shopper's head and gaze clearly alternate between the product and the price placard."),
        ("8-10s", "The shopper remains in place, again checks the price placard, and does not purchase."),
    ],
    "repeated_product_handling": [
        ("0-2s", "The shopper stops at the display and reaches toward the product."),
        ("2-5s", "The shopper touches the accessible demo item on the open tray, releases it, then reaches for it again."),
        ("5-8s", "The shopper repeats the handling motion while studying the item closely with hands visible."),
        ("8-10s", "The shopper leaves the demo item on the tray and remains undecided."),
    ],
    "comparing_two_products": [
        ("0-2s", "The shopper stands between two nearby options."),
        ("2-5s", "The shopper turns head and gaze from the left product to the right product while both remain visible."),
        ("5-8s", "The shopper points or moves a hand between the two products to compare them side by side."),
        ("8-10s", "The shopper remains between both options without choosing either one."),
    ],
    "looking_around_for_help": [
        ("0-2s", "The shopper studies the product and pauses."),
        ("2-5s", "The shopper lifts their head and scans the aisle as if trying to find store staff."),
        ("5-8s", "The shopper glances back at the product, then looks around again for assistance."),
        ("8-10s", "The shopper stays near the display waiting for possible help."),
    ],
    "checking_phone_likely_research": [
        ("0-2s", "The shopper examines the product display."),
        ("2-5s", "The shopper takes out a phone and looks at it while standing next to the product."),
        ("5-8s", "The shopper alternates between the phone screen and the product, as if comparing information."),
        ("8-10s", "The shopper keeps the phone in hand and continues reviewing the product."),
    ],
    "brief_glance_walking_past": [
        ("0-2s", "The shopper enters the aisle already walking past the display, keeping a clear step of distance from the counter."),
        ("2-5s", "Without stopping, the shopper briefly turns their head toward the product for a quick glance while feet keep moving."),
        ("5-8s", "The shopper gives one more short side glance from the walkway, with no leaning, no hand reach, and no pause at the display."),
        ("8-10s", "The shopper continues out of the product area and leaves the display behind without engaging further."),
    ],
    "trying_on_or_testing": [
        ("0-2s", "The shopper steps close to the product display."),
        ("2-5s", "The shopper tries the product, tests a demo function, or checks fit in a natural way."),
        ("5-8s", "The shopper continues testing while watching the product response or appearance."),
        ("8-10s", "The shopper finishes the test and keeps considering the item."),
    ],
    "asking_companion_opinion": [
        ("0-2s", "The primary shopper stands near the product with one companion nearby."),
        ("2-5s", "The shopper gestures toward the product and turns to the companion for input."),
        ("5-8s", "The companion looks at the product while the shopper watches their reaction."),
        ("8-10s", "The shopper and companion continue quietly comparing the option without purchasing."),
    ],
    "no_eye_contact_avoidant": [
        ("0-2s", "The shopper is near the display but keeps their body angled away from the aisle."),
        ("2-5s", "The shopper avoids looking toward the service area and keeps attention low."),
        ("5-8s", "The shopper looks away when someone might approach, maintaining distance from interaction."),
        ("8-10s", "The shopper stays distant and avoids direct interaction."),
    ],
    "approaching_counter": [
        ("0-2s", "The shopper holds or closely follows the product display area."),
        ("2-5s", "The shopper turns toward the service counter or checkout area."),
        ("5-8s", "The shopper walks closer to the counter while still considering the product."),
        ("8-10s", "The shopper arrives near the counter but does not complete a purchase."),
    ],
}

FRAME_SAMPLING_PLAN = [
    {"index": 0, "timestamp_sec": 2.0, "role": "cue_onset"},
    {"index": 1, "timestamp_sec": 5.0, "role": "cue_peak"},
    {"index": 2, "timestamp_sec": 8.0, "role": "cue_resolution"},
]

VIEWPOINT_CAMERA = {
    "salesperson_observable": (
        "10-second realistic in-store medium shot from a salesperson-observable angle, "
        "three-quarter front or side-front view; customer face, gaze direction, subtle expression, "
        "upper body, hands, product display, and price area visible"
    ),
    "surveillance_oblique": (
        "10-second fixed in-store surveillance-style shot, slightly elevated oblique angle; "
        "customer body trajectory, dwell time, hand movement, product display, and counter area visible; "
        "face detail is helpful but not required"
    ),
    "third_party_side": (
        "10-second realistic side-view retail observation, medium distance; customer profile, "
        "head direction, hands, product display, and price area visible"
    ),
    "first_person_pov": (
        "10-second first-person salesperson POV; customer may briefly look toward the camera, "
        "product area partially visible, no conversation has started"
    ),
}

VIEWPOINT_NEGATIVE = {
    "salesperson_observable": "no back-only shot, no face hidden, no hands outside frame",
    "surveillance_oblique": "no extreme overhead shot, no tiny distant customer, no occluded product area",
    "third_party_side": "no back-only profile, no cropped hands, no occluded product area",
    "first_person_pov": "no camera shake, no already-started conversation, no blocking hands",
}

CUE_NEGATIVE = {
    "brief_glance_walking_past": (
        "no stopping at the display, no leaning over the counter, no close product inspection, "
        "no hand reaching toward the product"
    ),
}

CUE_CAMERA = {
    "brief_glance_walking_past": (
        "for this pass-by cue, keep the shopper's full body and head direction visible throughout the walkway; "
        "use a wider aisle composition with the product display on the side of the frame"
    ),
}


def build_prompt_json(scenario: dict[str, Any]) -> dict[str, Any]:
    viewpoint = scenario.get("viewpoint", rules.DEFAULT_VIEWPOINT)
    if viewpoint not in rules.VIEWPOINTS:
        raise ValueError(f"invalid viewpoint: {viewpoint}")
    timeline = _timeline_entries(scenario["target_cue"])
    sections = {
        "camera": _camera_section(scenario["target_cue"], viewpoint),
        "scene": _scene_section(scenario["product_category"], scenario["target_cue"]),
        "behavior_timeline": timeline,
        "negative": _negative_section(scenario["target_cue"], viewpoint),
    }
    kling_prompt = _join_sections(sections, scenario["aida_stage"])
    return {
        "session_id": scenario["session_id"],
        "split": scenario["split"],
        "viewpoint": viewpoint,
        "product_category": scenario["product_category"],
        "persona": scenario["persona"],
        "aida_stage": scenario["aida_stage"],
        "target_cue": scenario["target_cue"],
        "duration_seconds": scenario.get("duration_seconds", 10),
        "training_input_mode": scenario.get("training_input_mode", "multi_image_single_turn"),
        "source_rule_ids": scenario["source_rule_ids"],
        "runtime_fallbacks": scenario.get("runtime_fallbacks", []),
        "behavior_description": _timeline_to_text(timeline),
        "behavior_timeline": timeline,
        "frame_sampling_plan": FRAME_SAMPLING_PLAN,
        "kling_prompt_sections": sections,
        "kling_prompt": kling_prompt,
        "sampler": scenario.get("sampler", {}),
        "scenario_metadata": {
            "sample_index": scenario.get("sample_index"),
            "derived": scenario.get("derived", {}),
            "sampler": scenario.get("sampler", {}),
        },
    }


def write_prompt_jsons(
    scenarios: Iterable[dict[str, Any]],
    out_root: Path = DEFAULT_OUT_ROOT,
    overwrite: bool = False,
) -> list[dict[str, Any]]:
    written: list[dict[str, Any]] = []
    out_root.mkdir(parents=True, exist_ok=True)
    for scenario in scenarios:
        prompt_json = build_prompt_json(scenario)
        out_dir = out_root / prompt_json["session_id"]
        out_path = out_dir / "prompt.json"
        if out_path.exists() and not overwrite:
            raise FileExistsError(f"prompt.json exists: {out_path}. Use --overwrite to replace it.")
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(prompt_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append(
            {
                "session_id": prompt_json["session_id"],
                "split": prompt_json["split"],
                "viewpoint": prompt_json["viewpoint"],
                "product_category": prompt_json["product_category"],
                "prompt_path": out_path.as_posix(),
                "prompt_chars": len(prompt_json["kling_prompt"]),
                "target_cue": prompt_json["target_cue"],
            }
        )
    return written


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Kling prompt.json files from PIWM scenarios.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--index-out", type=Path, default=None)
    args = parser.parse_args(argv)

    scenarios = load_jsonl(args.manifest)
    if args.limit is not None:
        scenarios = scenarios[: args.limit]
    written = write_prompt_jsons(scenarios, out_root=args.out_root, overwrite=args.overwrite)
    index_out = args.index_out or args.out_root / "_prompt_index.jsonl"
    _write_jsonl(written, index_out)
    stats = {
        "n_prompts": len(written),
        "out_root": args.out_root.as_posix(),
        "index_out": index_out.as_posix(),
    }
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    return 0


def _camera_section(cue: str, viewpoint: str) -> str:
    subject_rule = "one primary shopper"
    if cue == "asking_companion_opinion":
        subject_rule = "one primary shopper and one quiet companion"
    camera = VIEWPOINT_CAMERA[viewpoint]
    cue_camera = CUE_CAMERA.get(cue)
    cue_clause = f"; {cue_camera}" if cue_camera else ""
    return f"{camera}{cue_clause}; {subject_rule}, natural movement, no subtitles, no voiceover, no brand logos."


def _scene_section(product_category: str, cue: str) -> str:
    product = PRODUCT_SCENES[product_category]
    setup = product["product"]
    if cue in {"repeated_product_handling", "trying_on_or_testing"}:
        setup = (
            "an accessible demo sample on an open presentation tray on top of the counter, outside any glass case; "
            "the shopper can naturally touch only this demo sample, while the enclosed display stays in the background"
        )
    elif cue == "comparing_two_products":
        setup = (
            "two comparable products placed side by side on the same accessible display surface, "
            "with both products fully visible throughout the shot"
        )
    elif cue == "long_dwell_with_price_check":
        setup = (
            f"{setup}, plus clearly visible blank price placards positioned next to the products"
        )
    elif cue == "brief_glance_walking_past":
        setup = (
            f"{setup}, positioned beside a clear walking path so the shopper can pass by without stopping"
        )
    return f"{product['store']}; visible product setup: {setup}."


def _negative_section(cue: str, viewpoint: str) -> str:
    companion_clause = "no extra shoppers besides the companion" if cue == "asking_companion_opinion" else "no extra shoppers"
    cue_clause = CUE_NEGATIVE.get(cue)
    cue_prefix = f"{cue_clause}, " if cue_clause else ""
    return (
        f"{VIEWPOINT_NEGATIVE[viewpoint]}, {cue_prefix}{companion_clause}, no completed purchase, no salesperson speech, no exaggerated acting, "
        "no floating labels, no hidden-category labels, no intervention labels, no scoring text, no UI overlays."
    )


def _timeline_entries(cue: str) -> list[dict[str, str]]:
    return [{"time": time_range, "event": event} for time_range, event in CUE_TIMELINES[cue]]


def _timeline_to_text(timeline: list[dict[str, str]]) -> str:
    return " ".join(f"{entry['time']}: {entry['event']}" for entry in timeline)


def _join_sections(sections: dict[str, Any], aida_stage: str) -> str:
    timeline = "\n".join(f"- {entry['time']}: {entry['event']}" for entry in sections["behavior_timeline"])
    stage_style = STAGE_STYLE[aida_stage]
    return (
        f"Camera: {sections['camera']}\n"
        f"Scene: {sections['scene']}\n"
        f"Customer behavior style: {stage_style}\n"
        f"Behavior timeline:\n{timeline}\n"
        f"Negative constraints: {sections['negative']}"
    )


def _write_jsonl(rows: Iterable[dict[str, Any]], out: Path) -> int:
    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=False) + "\n")
            count += 1
    return count


def forbidden_label_hits(prompt: str) -> list[str]:
    labels = set(rules.LATENT_STATES) | set(rules.ACTIONS) | set(rules.INTENTS)
    labels.update({"BDI", "belief", "desire", "intention", "reward", "state_subtype"})
    return sorted(label for label in labels if label in prompt)


if __name__ == "__main__":
    raise SystemExit(main())
