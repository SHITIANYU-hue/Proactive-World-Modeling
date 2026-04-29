"""Tests for source registries and rule provenance coverage.

These tests enforce the key boundary: BDI and other modeling sources may
support PIWM's representation, but they must not be used as sales-rule
evidence.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from piwm_data.expert_corpus.provenance import (
    DEFAULT_MODELING_SOURCE_REGISTRY,
    DEFAULT_EXTRACTED_PRINCIPLES,
    DEFAULT_RULE_SOURCE_LINKS,
    DEFAULT_SALES_SOURCE_REGISTRY,
    build_provenance_coverage,
    load_extracted_principles,
    load_rule_entries,
    load_rule_source_links,
    load_source_registry,
    validate_extracted_principles,
    validate_rule_source_links,
    validate_source_registries,
    write_provenance_coverage,
)
from piwm_data.expert_corpus.schemas import CorpusValidationError, RuleSourceLink


def test_source_registries_are_separated() -> None:
    sales_sources = load_source_registry(DEFAULT_SALES_SOURCE_REGISTRY)
    modeling_sources = load_source_registry(DEFAULT_MODELING_SOURCE_REGISTRY)

    validate_source_registries(sales_sources, modeling_sources)
    assert sales_sources
    assert modeling_sources
    assert all(source.domain == "sales" for source in sales_sources)
    assert all(source.source_id.startswith("SRC_SALES_") for source in sales_sources)
    assert all(source.domain == "modeling" for source in modeling_sources)
    assert all(source.source_id.startswith("SRC_MODELING_") for source in modeling_sources)
    assert any("BDI" in source.title for source in modeling_sources)
    assert not any("BDI" in source.title for source in sales_sources)


def test_rule_source_links_use_only_sales_sources() -> None:
    sales_sources = load_source_registry(DEFAULT_SALES_SOURCE_REGISTRY)
    modeling_sources = load_source_registry(DEFAULT_MODELING_SOURCE_REGISTRY)
    rules = load_rule_entries()
    links = load_rule_source_links(DEFAULT_RULE_SOURCE_LINKS)

    validate_rule_source_links(links, rules, sales_sources, modeling_sources)
    assert links
    for link in links:
        assert all(source_id.startswith("SRC_SALES_") for source_id in link.source_ids)


def test_extracted_principles_are_compact_paraphrases() -> None:
    sales_sources = load_source_registry(DEFAULT_SALES_SOURCE_REGISTRY)
    modeling_sources = load_source_registry(DEFAULT_MODELING_SOURCE_REGISTRY)
    principles = load_extracted_principles(DEFAULT_EXTRACTED_PRINCIPLES)

    validate_extracted_principles(principles, sales_sources, modeling_sources)
    assert principles
    assert all(len(item.principle.split()) <= 45 for item in principles)
    assert all("verbatim" not in item.copyright_note.lower() for item in principles)


def test_candidate_and_transition_rules_are_theory_anchored() -> None:
    rules = load_rule_entries()
    links = load_rule_source_links(DEFAULT_RULE_SOURCE_LINKS)
    coverage = build_provenance_coverage(rules=rules, links=links)

    candidate = coverage["coverage_by_rule_type"]["state_aida_to_candidates"]
    transition = coverage["coverage_by_rule_type"]["transition"]
    assert candidate["total"] == 9
    assert candidate["linked"] == 9
    assert candidate["theory_anchored_or_better"] == 9
    assert transition["total"] == 21
    assert transition["linked"] == 21
    assert transition["theory_anchored_or_better"] == 21
    assert coverage["n_existing_rules_total"] == 72
    assert coverage["n_existing_rules_linked"] == 72
    assert coverage["n_existing_rules_unlinked"] == 0


def test_rule_source_links_do_not_require_all_72_seed_rules() -> None:
    links = load_rule_source_links(DEFAULT_RULE_SOURCE_LINKS)
    linked_ids = {link.rule_id for link in links}

    assert "CAND_001" in linked_ids
    assert "TRANS_001" in linked_ids
    assert "CUE2STATE_001" in linked_ids
    assert len(linked_ids) == 72


def test_modeling_source_cannot_be_used_for_sales_rule() -> None:
    sales_sources = load_source_registry(DEFAULT_SALES_SOURCE_REGISTRY)
    modeling_sources = load_source_registry(DEFAULT_MODELING_SOURCE_REGISTRY)
    rules = load_rule_entries()
    bad = RuleSourceLink(
        rule_id="TRANS_001",
        rule_type="transition",
        lifecycle="retained_seed",
        support_status="theory_anchored",
        source_ids=["SRC_MODELING_BDI_001"],
        formalization_note="This intentionally misuses BDI as sales-rule evidence.",
        support_strength="medium",
        needs_manual_support=True,
    )

    with pytest.raises(CorpusValidationError, match="modeling sources"):
        validate_rule_source_links([bad], rules, sales_sources, modeling_sources)


def test_write_provenance_coverage(tmp_path: Path) -> None:
    out = tmp_path / "coverage.json"
    report = write_provenance_coverage(out=out)

    assert out.exists()
    assert report["n_existing_rules_total"] == 72
    assert report["coverage_by_rule_type"]["transition"]["linked"] == 21
    assert report["n_existing_rules_unlinked"] == 0
