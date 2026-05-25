# GuidanceSalesBench

GuidanceSalesBench is the unified dataset bundle for guidance-sales proactive
intent/world-model work. It is organized into four partitions:

- `general`: schema v2.2 synthetic general-domain guidance-sales data.
- `target`: target-domain smart-vending front-camera data and current 5-act splits.
- `real_shooting`: entity-shot smart-vending evaluation metadata and media manifest.
- `human_labels`: empty placeholder for future human annotation.

The current operational act space is fixed as `Greet / Elicit / Inform /
Recommend / Hold`. `Reassure` is retained only in source/compatibility provenance
where it already exists, and is not an operational training/evaluation/inference
label in the current splits.
