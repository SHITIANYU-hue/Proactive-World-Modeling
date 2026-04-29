"""Provenance registry and coverage checks for the expert corpus.

This module keeps sales-rule provenance separate from modeling-theory
provenance. Sales rules may link only to ``SRC_SALES_*`` entries; sources such
as BDI belong in the modeling registry and must not be used as sales evidence.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter, ValidationError

from .compile import DEFAULT_JSONL
from .schemas import (
    CorpusValidationError,
    ExtractedPrinciple,
    RuleEntry,
    RuleSourceLink,
    SourceRegistryEntry,
)

DEFAULT_SALES_SOURCE_REGISTRY = Path(__file__).parent / "sources" / "sales_source_registry.jsonl"
DEFAULT_MODELING_SOURCE_REGISTRY = Path(__file__).parent / "sources" / "modeling_source_registry.jsonl"
DEFAULT_EXTRACTED_PRINCIPLES = Path(__file__).parent / "distilled" / "extracted_principles.jsonl"
DEFAULT_RULE_SOURCE_LINKS = Path(__file__).parent / "distilled" / "rule_source_links.jsonl"
DEFAULT_COVERAGE_REPORT = Path(__file__).parent / "distilled" / "_provenance_coverage.json"

_SOURCE_ADAPTER: TypeAdapter[SourceRegistryEntry] = TypeAdapter(SourceRegistryEntry)
_LINK_ADAPTER: TypeAdapter[RuleSourceLink] = TypeAdapter(RuleSourceLink)
_RULE_ADAPTER: TypeAdapter[RuleEntry] = TypeAdapter(RuleEntry)
_PRINCIPLE_ADAPTER: TypeAdapter[ExtractedPrinciple] = TypeAdapter(ExtractedPrinciple)

_ANCHORED_OR_BETTER = {"theory_anchored", "manual_supported", "expert_reviewed"}
_MANUAL_OR_BETTER = {"manual_supported", "expert_reviewed"}


def load_source_registry(path: Path) -> list[SourceRegistryEntry]:
    return _load_jsonl(path, _SOURCE_ADAPTER, "source registry")


def load_rule_source_links(path: Path = DEFAULT_RULE_SOURCE_LINKS) -> list[RuleSourceLink]:
    return _load_jsonl(path, _LINK_ADAPTER, "rule source links")


def load_rule_entries(path: Path = DEFAULT_JSONL) -> list[RuleEntry]:
    return _load_jsonl(path, _RULE_ADAPTER, "conditional rules")


def load_extracted_principles(path: Path = DEFAULT_EXTRACTED_PRINCIPLES) -> list[ExtractedPrinciple]:
    return _load_jsonl(path, _PRINCIPLE_ADAPTER, "extracted principles")


def validate_source_registries(
    sales_sources: list[SourceRegistryEntry],
    modeling_sources: list[SourceRegistryEntry],
) -> None:
    errors: list[str] = []
    seen: set[str] = set()
    for source in sales_sources + modeling_sources:
        if source.source_id in seen:
            errors.append(f"duplicate source_id: {source.source_id}")
        seen.add(source.source_id)
        if source.domain == "sales" and not source.source_id.startswith("SRC_SALES_"):
            errors.append(f"sales source must use SRC_SALES_ prefix: {source.source_id}")
        if source.domain == "modeling" and not source.source_id.startswith("SRC_MODELING_"):
            errors.append(f"modeling source must use SRC_MODELING_ prefix: {source.source_id}")
    for source in sales_sources:
        if source.domain != "sales":
            errors.append(f"sales registry contains non-sales source: {source.source_id}")
    for source in modeling_sources:
        if source.domain != "modeling":
            errors.append(f"modeling registry contains non-modeling source: {source.source_id}")
    if errors:
        raise CorpusValidationError("; ".join(errors))


def validate_rule_source_links(
    links: list[RuleSourceLink],
    rules: list[RuleEntry],
    sales_sources: list[SourceRegistryEntry],
    modeling_sources: list[SourceRegistryEntry],
) -> None:
    """Validate that rule links are honest and use only sales sources."""

    rule_type_by_id = {rule.rule_id: rule.rule_type for rule in rules}
    sales_ids = {source.source_id for source in sales_sources}
    modeling_ids = {source.source_id for source in modeling_sources}
    seen_rule_ids: set[str] = set()
    errors: list[str] = []

    for link in links:
        if link.rule_id in seen_rule_ids:
            errors.append(f"duplicate rule source link: {link.rule_id}")
        seen_rule_ids.add(link.rule_id)

        existing_type = rule_type_by_id.get(link.rule_id)
        if link.lifecycle != "new_source_backed":
            if existing_type is None:
                errors.append(f"link references unknown seed rule: {link.rule_id}")
            elif existing_type != link.rule_type:
                errors.append(
                    f"{link.rule_id}: rule_type mismatch link={link.rule_type} corpus={existing_type}"
                )

        if link.support_status in _ANCHORED_OR_BETTER and not link.source_ids:
            errors.append(f"{link.rule_id}: anchored rule must list source_ids")
        if link.support_status in _ANCHORED_OR_BETTER and link.support_strength == "none":
            errors.append(f"{link.rule_id}: anchored rule cannot have support_strength=none")

        bad_modeling = sorted(set(link.source_ids) & modeling_ids)
        if bad_modeling:
            errors.append(f"{link.rule_id}: sales rule links cannot use modeling sources {bad_modeling}")

        unknown_sources = sorted(set(link.source_ids) - sales_ids)
        if unknown_sources:
            errors.append(f"{link.rule_id}: unknown or non-sales source_ids {unknown_sources}")

    if errors:
        raise CorpusValidationError("; ".join(errors))


def validate_extracted_principles(
    principles: list[ExtractedPrinciple],
    sales_sources: list[SourceRegistryEntry],
    modeling_sources: list[SourceRegistryEntry],
) -> None:
    source_ids = {source.source_id for source in sales_sources + modeling_sources}
    errors: list[str] = []
    seen: set[str] = set()
    for principle in principles:
        if principle.principle_id in seen:
            errors.append(f"duplicate principle_id: {principle.principle_id}")
        seen.add(principle.principle_id)
        if principle.source_id not in source_ids:
            errors.append(f"{principle.principle_id}: unknown source_id {principle.source_id}")
        if len(principle.principle.split()) > 45:
            errors.append(f"{principle.principle_id}: principle is too long for a compact paraphrase")
        if "verbatim" in principle.copyright_note.lower():
            errors.append(f"{principle.principle_id}: copyright_note must not claim verbatim extraction")
    if errors:
        raise CorpusValidationError("; ".join(errors))


def build_provenance_coverage(
    rules: list[RuleEntry] | None = None,
    links: list[RuleSourceLink] | None = None,
) -> dict[str, Any]:
    rules = rules if rules is not None else load_rule_entries()
    links = links if links is not None else load_rule_source_links()

    rule_type_by_id = {rule.rule_id: rule.rule_type for rule in rules}
    existing_rule_ids = set(rule_type_by_id)
    links_by_id = {link.rule_id: link for link in links}
    linked_existing = existing_rule_ids & set(links_by_id)
    unlinked_existing = existing_rule_ids - set(links_by_id)

    status_counts = Counter(link.support_status for link in links)
    lifecycle_counts = Counter(link.lifecycle for link in links)
    coverage_by_rule_type: dict[str, dict[str, int]] = defaultdict(
        lambda: {
            "total": 0,
            "linked": 0,
            "unlinked": 0,
            "theory_anchored_or_better": 0,
            "manual_supported_or_better": 0,
            "expert_reviewed": 0,
            "candidate_for_removal": 0,
        }
    )

    for rule in rules:
        coverage_by_rule_type[rule.rule_type]["total"] += 1

    for rule_id in unlinked_existing:
        coverage_by_rule_type[rule_type_by_id[rule_id]]["unlinked"] += 1

    for rule_id in linked_existing:
        link = links_by_id[rule_id]
        bucket = coverage_by_rule_type[rule_type_by_id[rule_id]]
        bucket["linked"] += 1
        if link.support_status in _ANCHORED_OR_BETTER:
            bucket["theory_anchored_or_better"] += 1
        if link.support_status in _MANUAL_OR_BETTER:
            bucket["manual_supported_or_better"] += 1
        if link.support_status == "expert_reviewed":
            bucket["expert_reviewed"] += 1
        if link.support_status == "candidate_for_removal":
            bucket["candidate_for_removal"] += 1

    return {
        "n_existing_rules_total": len(existing_rule_ids),
        "n_rule_source_links_total": len(links),
        "n_existing_rules_linked": len(linked_existing),
        "n_existing_rules_unlinked": len(unlinked_existing),
        "support_status_counts": dict(sorted(status_counts.items())),
        "lifecycle_counts": dict(sorted(lifecycle_counts.items())),
        "coverage_by_rule_type": {
            key: dict(value) for key, value in sorted(coverage_by_rule_type.items())
        },
    }


def write_provenance_coverage(
    out: Path = DEFAULT_COVERAGE_REPORT,
    rules: list[RuleEntry] | None = None,
    links: list[RuleSourceLink] | None = None,
) -> dict[str, Any]:
    report = build_provenance_coverage(rules=rules, links=links)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def validate_default_provenance_files() -> dict[str, Any]:
    sales_sources = load_source_registry(DEFAULT_SALES_SOURCE_REGISTRY)
    modeling_sources = load_source_registry(DEFAULT_MODELING_SOURCE_REGISTRY)
    rules = load_rule_entries(DEFAULT_JSONL)
    principles = load_extracted_principles(DEFAULT_EXTRACTED_PRINCIPLES)
    links = load_rule_source_links(DEFAULT_RULE_SOURCE_LINKS)
    validate_source_registries(sales_sources, modeling_sources)
    validate_extracted_principles(principles, sales_sources, modeling_sources)
    validate_rule_source_links(links, rules, sales_sources, modeling_sources)
    return build_provenance_coverage(rules=rules, links=links)


def _load_jsonl(path: Path, adapter: TypeAdapter[Any], label: str) -> list[Any]:
    if not path.exists():
        raise FileNotFoundError(f"{label} not found: {path}")
    out: list[Any] = []
    with path.open(encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                raw = json.loads(line)
            except json.JSONDecodeError as exc:
                raise CorpusValidationError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
            try:
                out.append(adapter.validate_python(raw))
            except ValidationError as exc:
                raise CorpusValidationError(f"{path}:{line_no}: schema error: {exc}") from exc
    return out


def main() -> None:
    report = validate_default_provenance_files()
    write_provenance_coverage(rules=load_rule_entries(), links=load_rule_source_links())
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
