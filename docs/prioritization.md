# Experiment Prioritization (MVP)

`rank_experiments` provides deterministic, confidence-adjusted ranking for growth experiments.
It returns scored records with both `confidence_weighted_impact` and `expected_lift`
so planning and reporting can use normalized ranking + absolute upside.

## Input contract

Each experiment must include:

- `name` (string)
- `reach` (number)
- `impact` (number)
- `confidence` (number, must be within `0..1`)
- `effort` (number, must be > 0)

If required fields are missing or contain non-numeric values, the function raises
`ValueError` with the experiment name and offending field for faster triage in CI/logs.

Optional ranking filters:

- `min_confidence` (number in `0..1`) — excludes items below this threshold before scoring
- `max_effort` (number `> 0`) — excludes items with effort greater than this threshold
- `min_reach` (number `>= 0`) — excludes items with reach smaller than this threshold
- `min_impact` (number `>= 0`) — excludes items with impact smaller than this threshold
- `min_score` (number `>= 0`) — excludes items with final score lower than this threshold
- `min_base_score` (number `>= 0`) — excludes items where base score `(reach * impact * confidence) / effort` falls below this floor
- `min_confidence_weighted_impact` (number `>= 0`) — excludes items where `impact * confidence` falls below this floor
- `min_reach_per_effort` (number `>= 0`) — excludes items where `reach / effort` falls below this floor
- `min_expected_lift` (number `>= 0`) — excludes items where `reach * impact * confidence` falls below this floor
- `min_roi` (number `>= 0`) — excludes items where `(reach * impact * confidence) / effort` falls below this floor
- `max_results` (positive integer) — returns only the top N items after ranking

## Scoring

Base score:

`reach * impact * confidence / effort`

Then a light confidence-weighted impact multiplier is applied:

`base_score * (0.7 + 0.3 * normalized(impact * confidence))`

This keeps RICE-like behavior while preferring higher-confidence opportunities.

## Output fields

Each ranked item contains:

- `name`
- `score` (final confidence-adjusted prioritization score)
- `base_score` (unboosted score: `(reach * impact * confidence) / effort`)
- `roi` (alias of `base_score` for planning/reporting readability)
- `confidence_weighted_impact` (`impact * confidence`)
- `expected_lift` (`reach * impact * confidence`, absolute upside before effort penalty)
- `reach_per_effort` (`reach / effort`, operational leverage for execution planning)

## Determinism

- Sort order: score descending
- Tie-break: experiment name (case-insensitive, ascending)

This ensures stable ordering for dashboards and CI snapshots.
