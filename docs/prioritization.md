# Experiment Prioritization (MVP)

`rank_experiments` provides deterministic, confidence-adjusted ranking for growth experiments.

## Input contract

Each experiment must include:

- `name` (string)
- `reach` (number)
- `impact` (number)
- `confidence` (number, must be within `0..1`)
- `effort` (number, must be > 0)

Optional ranking filters:

- `min_confidence` (number in `0..1`) — excludes items below this threshold before scoring
- `max_effort` (number `> 0`) — excludes items with effort greater than this threshold

## Scoring

Base score:

`reach * impact * confidence / effort`

Then a light confidence-weighted impact multiplier is applied:

`base_score * (0.7 + 0.3 * normalized(impact * confidence))`

This keeps RICE-like behavior while preferring higher-confidence opportunities.

## Determinism

- Sort order: score descending
- Tie-break: experiment name (case-insensitive, ascending)

This ensures stable ordering for dashboards and CI snapshots.
