"""SFT entrypoint for PIWM pilot training.

Dry-run mode is dependency-free and only validates the dataset adapter. Real
training imports torch/transformers lazily so the data pipeline remains light.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
import types
from pathlib import Path
from typing import Sequence

from . import config
from .data_collator import SFTExample, build_sft_examples, write_sft_jsonl


SMOKE_JSONL = "sft_train_smoke.jsonl"
SMOKE_SUMMARY = "sft_smoke_summary.json"
TRAIN_SUMMARY = "sft_train_summary.json"


def build_smoke_summary(data_dir: Path, output_dir: Path, examples: Sequence[SFTExample], mode: str = "dry-run") -> dict:
    task_counts: dict[str, int] = {
        "perception": 0,
        "deliberation": 0,
        "continuation_caption": 0,
    }
    image_path_count = 0
    for example in examples:
        task_counts[example.task] = task_counts.get(example.task, 0) + 1
        image_path_count += len(example.images)

    note = (
        "dry-run validates the dataset adapter only; it is not a training result."
        if mode == "dry-run"
        else "real SFT smoke run; use only as pilot-stage training evidence."
    )
    return {
        "mode": mode,
        "note": note,
        "data_dir": str(data_dir),
        "output_dir": str(output_dir),
        "n_examples": len(examples),
        "task_counts": task_counts,
        "image_path_count": image_path_count,
        "has_continuation_examples": task_counts.get("continuation_caption", 0) > 0,
    }


def run_dry_run(data_dir: Path, output_dir: Path) -> dict:
    examples = build_sft_examples(data_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    write_sft_jsonl(examples, output_dir / SMOKE_JSONL)

    summary = build_smoke_summary(data_dir, output_dir, examples)
    _write_json(summary, output_dir / SMOKE_SUMMARY)
    return summary


def missing_training_dependencies() -> list[str]:
    return [
        name
        for name in ("torch", "transformers", "peft", "PIL")
        if importlib.util.find_spec(name) is None
    ]


def run_train(
    data_dir: Path,
    output_dir: Path,
    *,
    model_name: str,
    max_examples: int | None,
    epochs: int,
    learning_rate: float,
    gradient_accumulation_steps: int,
    use_4bit: bool,
) -> dict:
    missing = missing_training_dependencies()
    if missing:
        raise RuntimeError(
            "SFT training requires optional dependencies that are not installed: "
            + ", ".join(missing)
            + ". Install the train extra before running without --dry-run."
        )

    import torch
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    from transformers import AutoProcessor, BitsAndBytesConfig

    _patch_torch_compat(torch)
    model_class = _load_model_class()

    examples = build_sft_examples(data_dir)
    if max_examples is not None:
        examples = examples[:max_examples]
    if not examples:
        raise RuntimeError(f"no SFT examples found in {data_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    write_sft_jsonl(examples, output_dir / SMOKE_JSONL)

    started = time.time()
    dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
    quantization_config = None
    if use_4bit and torch.cuda.is_available():
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_use_double_quant=True,
        )

    processor = AutoProcessor.from_pretrained(model_name, trust_remote_code=True)
    model = model_class.from_pretrained(
        model_name,
        torch_dtype=dtype,
        device_map="auto" if torch.cuda.is_available() else None,
        quantization_config=quantization_config,
        trust_remote_code=True,
    )
    if quantization_config is not None:
        model = prepare_model_for_kbit_training(model)

    model = get_peft_model(
        model,
        LoraConfig(
            r=config.LORA_RANK,
            lora_alpha=config.LORA_ALPHA,
            target_modules=config.LORA_TARGET_MODULES,
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM",
        ),
    )
    model.train()
    optimizer = torch.optim.AdamW(model.parameters(), lr=learning_rate)

    losses: list[float] = []
    optimizer.zero_grad(set_to_none=True)
    step_count = 0
    for _epoch in range(epochs):
        for example in examples:
            batch = _encode_example(example, processor, Path.cwd())
            batch = {key: value.to(model.device) if hasattr(value, "to") else value for key, value in batch.items()}
            outputs = model(**batch)
            loss = outputs.loss / gradient_accumulation_steps
            loss.backward()
            losses.append(float(outputs.loss.detach().cpu()))
            step_count += 1
            if step_count % gradient_accumulation_steps == 0:
                optimizer.step()
                optimizer.zero_grad(set_to_none=True)
    if step_count % gradient_accumulation_steps:
        optimizer.step()
        optimizer.zero_grad(set_to_none=True)

    checkpoint_dir = output_dir / "checkpoint-final"
    model.save_pretrained(checkpoint_dir)
    processor.save_pretrained(checkpoint_dir)

    finite = all(torch.isfinite(torch.tensor(value)).item() for value in losses)
    summary = {
        **build_smoke_summary(data_dir, output_dir, examples, mode="train"),
        "is_training_result": True,
        "model_name": model_name,
        "epochs": epochs,
        "learning_rate": learning_rate,
        "gradient_accumulation_steps": gradient_accumulation_steps,
        "use_4bit": bool(quantization_config is not None),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
        "loss_first": losses[0] if losses else None,
        "loss_last": losses[-1] if losses else None,
        "loss_is_finite": finite,
        "checkpoint_dir": str(checkpoint_dir),
        "runtime_seconds": time.time() - started,
    }
    _write_json(summary, output_dir / TRAIN_SUMMARY)
    return summary


def _load_model_class() -> object:
    import transformers

    for name in (
        "Qwen3VLForConditionalGeneration",
        "Qwen2_5_VLForConditionalGeneration",
        "Qwen2VLForConditionalGeneration",
        "AutoModelForVision2Seq",
    ):
        cls = getattr(transformers, name, None)
        if cls is not None:
            return cls
    raise RuntimeError("installed transformers does not expose a Qwen VL model class")


def _patch_torch_compat(torch_module: object) -> None:
    """Patch small API gaps in older torch builds used on sprint servers."""
    compiler = getattr(torch_module, "compiler", None)
    if compiler is None:
        setattr(torch_module, "compiler", types.SimpleNamespace(is_compiling=lambda: False))
        return
    if not hasattr(compiler, "is_compiling"):
        setattr(compiler, "is_compiling", lambda: False)


def _encode_example(example: SFTExample, processor: object, cwd: Path) -> dict:
    full_messages = _messages(example, include_target=True, cwd=cwd)
    prompt_messages = _messages(example, include_target=False, cwd=cwd)
    full = processor.apply_chat_template(
        full_messages,
        tokenize=True,
        add_generation_prompt=False,
        return_dict=True,
        return_tensors="pt",
    )
    prompt = processor.apply_chat_template(
        prompt_messages,
        tokenize=True,
        add_generation_prompt=True,
        return_dict=True,
        return_tensors="pt",
    )
    labels = full["input_ids"].clone()
    prompt_len = min(prompt["input_ids"].shape[-1], labels.shape[-1])
    labels[:, :prompt_len] = -100
    full["labels"] = labels
    return full


def _messages(example: SFTExample, *, include_target: bool, cwd: Path) -> list[dict]:
    prompt_text = example.prompt.replace(config.IMAGE_PLACEHOLDER, "").strip()
    content = [{"type": "image", "image": _resolve_image(path, cwd)} for path in example.images]
    content.append({"type": "text", "text": prompt_text})
    messages = [
        {"role": "system", "content": _system_prompt()},
        {"role": "user", "content": content},
    ]
    if include_target:
        messages.append({"role": "assistant", "content": [{"type": "text", "text": example.target}]})
    return messages


def _resolve_image(path: str, cwd: Path) -> str:
    image_path = Path(path)
    if not image_path.is_absolute():
        image_path = cwd / image_path
    if not image_path.exists():
        raise FileNotFoundError(f"image not found: {image_path}")
    return image_path.as_posix()


def _system_prompt() -> str:
    from .prompts import PIWM_SYSTEM_PROMPT

    return PIWM_SYSTEM_PROMPT


def _write_json(payload: dict, out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PIWM SFT entrypoint")
    parser.add_argument("--data-dir", type=Path, required=True, help="Directory with PIWM JSONL training artifacts.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Directory for SFT outputs.")
    parser.add_argument("--dry-run", action="store_true", help="Write dependency-free dataset smoke artifacts.")
    parser.add_argument("--model-name", default=config.MODEL_NAME)
    parser.add_argument("--max-examples", type=int, default=8)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--learning-rate", type=float, default=1e-5)
    parser.add_argument("--gradient-accumulation-steps", type=int, default=4)
    parser.add_argument("--no-4bit", action="store_true")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if args.dry_run:
        summary = run_dry_run(args.data_dir, args.output_dir)
        print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
        return 0
    try:
        summary = run_train(
            args.data_dir,
            args.output_dir,
            model_name=args.model_name,
            max_examples=args.max_examples,
            epochs=args.epochs,
            learning_rate=args.learning_rate,
            gradient_accumulation_steps=args.gradient_accumulation_steps,
            use_4bit=not args.no_4bit,
        )
    except Exception as exc:  # noqa: BLE001 - CLI should preserve actionable failure.
        print(f"SFT training failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
