#!/usr/bin/env python3
"""Normalize PIWM labeled JSON files to the canonical action format."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from action_space import enrich_labeled_record


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_LABELED_DIR = REPO_ROOT / "data" / "labeled"


def upgrade_file(path: Path, dry_run: bool = False) -> bool:
    record = json.loads(path.read_text(encoding="utf-8"))
    before = json.dumps(record, ensure_ascii=False, sort_keys=True)
    upgraded = enrich_labeled_record(record)
    after = json.dumps(upgraded, ensure_ascii=False, sort_keys=True)
    changed = before != after
    if changed and not dry_run:
        path.write_text(json.dumps(upgraded, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return changed


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize action/realization fields in data/labeled/*.json.")
    parser.add_argument("paths", nargs="*", help="JSON files to upgrade. Defaults to data/labeled/piwm_*.json.")
    parser.add_argument("--dry-run", action="store_true", help="Only report files that would change.")
    args = parser.parse_args()

    paths = [Path(p) for p in args.paths] if args.paths else sorted(DEFAULT_LABELED_DIR.glob("piwm_*.json"))
    changed = 0
    for path in paths:
        if upgrade_file(path, dry_run=args.dry_run):
            changed += 1
            print(f"{'would update' if args.dry_run else 'updated'} {path}")
    print(f"{changed} file(s) {'would change' if args.dry_run else 'changed'}")


if __name__ == "__main__":
    main()
